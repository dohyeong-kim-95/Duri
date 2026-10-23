"""Regression tests for the medium/low code review findings (M*, L*)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi import FastAPI, WebSocketDisconnect

from duri_api import recover
from duri_api.auth import AuthError, AuthService
from duri_api.main import app as default_app
from duri_api.main import create_app_from_env, handle_timeline_websocket
from duri_api.storage import DuriStorageWriter, StorageWriteError
from duri_api.timeline import (
    read_timeline_logs,
    read_timeline_summary,
    resolve_storage_path,
    search_timeline_logs,
)

PARTICIPANTS = {
    "01J_USER_A": "UserA",
    "01J_USER_B": "UserB",
}


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def make_writer(storage_root: Path, app_timezone: str = "Asia/Seoul") -> DuriStorageWriter:
    return DuriStorageWriter(
        storage_root=storage_root,
        participants=PARTICIPANTS,
        app_timezone=app_timezone,
    )


def partition_path(storage_root: Path, period: str) -> Path:
    return storage_root / "timeline" / period[:4] / period


def write_raw_metadata(storage_root: Path, period: str, metadata: object) -> Path:
    partition = partition_path(storage_root, period)
    partition.mkdir(parents=True, exist_ok=True)
    metadata_path = partition / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    return metadata_path


def read_metadata(storage_root: Path, period: str) -> dict[str, object]:
    metadata_path = partition_path(storage_root, period) / "metadata.json"
    loaded: dict[str, object] = json.loads(metadata_path.read_text(encoding="utf-8"))
    return loaded


def append_text(writer: DuriStorageWriter, log_id: str, created_at: str, text: str) -> None:
    writer.append_message(
        log_id=log_id,
        actor_id="01J_USER_A",
        created_at=dt(created_at),
        message_id=f"{log_id}_MESSAGE",
        text=text,
    )


def test_m1_log_without_created_at_or_broken_file_does_not_break_timeline(
    tmp_path: Path,
) -> None:
    append_text(make_writer(tmp_path), "01J_MSG_OK", "2026-08-01T10:00:00+09:00", "정상")
    write_raw_metadata(
        tmp_path,
        "2026-07",
        {
            "schema_version": 1,
            "period": "2026-07",
            "participants": {},
            "logs": [
                {"id": "01J_MSG_NO_TIME", "type": "Message", "payload": {"text": "시각 없음"}},
                {
                    "id": "01J_MSG_NAIVE",
                    "type": "Message",
                    "created_at": "2026-07-02T10:00:00",
                    "payload": {"text": "offset 없음"},
                },
            ],
        },
    )
    broken = partition_path(tmp_path, "2026-06")
    broken.mkdir(parents=True)
    (broken / "metadata.json").write_text("{not json", encoding="utf-8")

    log_ids = [log["id"] for log in read_timeline_logs(tmp_path)]

    assert log_ids == ["01J_MSG_NO_TIME", "01J_MSG_NAIVE", "01J_MSG_OK"]
    assert read_timeline_summary(tmp_path)["total"] == 3
    assert [log["id"] for log in search_timeline_logs(tmp_path, "정상")] == ["01J_MSG_OK"]


def test_m2_naive_datetime_is_rejected_and_nothing_is_written(tmp_path: Path) -> None:
    writer = make_writer(tmp_path)

    with pytest.raises(ValueError, match="timezone-aware"):
        append_text(writer, "01J_MSG_NAIVE", "2026-07-31T20:00:00", "naive UTC")
    with pytest.raises(ValueError, match="timezone-aware"):
        writer.append_photo(
            log_id="01J_PHOTO_NAIVE",
            actor_id="01J_USER_A",
            created_at=dt("2026-07-31T20:00:00"),
            photo_bytes=b"naive",
            original_filename="naive.jpg",
            mime_type="image/jpeg",
        )

    assert list(tmp_path.rglob("*.json")) == []
    assert [path for path in tmp_path.rglob("*") if path.is_file()] == []


def test_m3_writer_sorts_by_real_time_and_refuses_a_partition_in_another_timezone(
    tmp_path: Path,
) -> None:
    write_raw_metadata(
        tmp_path,
        "2026-07",
        {
            "schema_version": 1,
            "period": "2026-07",
            "timezone": "Asia/Seoul",
            "participants": {},
            "logs": [
                # 03:00 UTC written with +00:00, later than 10:00+09:00 (01:00 UTC).
                {
                    "id": "01J_MSG_LATER",
                    "type": "Message",
                    "created_at": "2026-07-12T03:00:00+00:00",
                    "actor_id": "01J_USER_A",
                    "payload": {"text": "later"},
                },
                {
                    "id": "01J_MSG_BROKEN",
                    "type": "Message",
                    "actor_id": "01J_USER_A",
                    "payload": {"text": "no created_at"},
                },
            ],
        },
    )
    append_text(make_writer(tmp_path), "01J_MSG_EARLIER", "2026-07-12T10:00:00+09:00", "earlier")

    log_ids = [log["id"] for log in read_metadata(tmp_path, "2026-07")["logs"]]  # type: ignore[attr-defined]
    assert log_ids == ["01J_MSG_BROKEN", "01J_MSG_EARLIER", "01J_MSG_LATER"]

    metadata_before = read_metadata(tmp_path, "2026-07")
    with pytest.raises(StorageWriteError, match="timezone"):
        append_text(
            make_writer(tmp_path, app_timezone="UTC"),
            "01J_MSG_UTC",
            "2026-07-13T00:00:00+00:00",
            "utc writer",
        )
    assert read_metadata(tmp_path, "2026-07") == metadata_before


WRITER_PROCESS_SCRIPT = """
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from duri_api.storage import DuriStorageWriter

storage_root = Path(sys.argv[1])
worker = sys.argv[2]
writer = DuriStorageWriter(
    storage_root=storage_root,
    participants={"01J_USER_A": "UserA"},
    app_timezone="Asia/Seoul",
)
for number in range(int(sys.argv[3])):
    writer.append_message(
        log_id=f"01J_MSG_{worker}_{number:03d}",
        actor_id="01J_USER_A",
        created_at=datetime.fromisoformat("2026-07-12T10:00:00+09:00"),
        message_id=f"01J_MESSAGE_{worker}_{number:03d}",
        text=f"{worker} {number}",
    )
"""


def test_m4_concurrent_writer_processes_do_not_lose_logs(tmp_path: Path) -> None:
    messages_per_process = 40
    process_names = ["P1", "P2", "P3"]
    processes = []
    for process_name in process_names:
        command = [
            sys.executable,
            "-c",
            WRITER_PROCESS_SCRIPT,
            str(tmp_path),
            process_name,
            str(messages_per_process),
        ]
        processes.append(subprocess.Popen(command))
    for process in processes:
        assert process.wait(timeout=120) == 0

    logs = read_metadata(tmp_path, "2026-07")["logs"]
    assert len(logs) == messages_per_process * len(process_names)  # type: ignore[arg-type]
    leftover_temp_files = list(partition_path(tmp_path, "2026-07").glob("*.tmp"))
    assert leftover_temp_files == []


@pytest.mark.parametrize("period", ["../../etc", "2026-13", "2026-7", "2026-07/..", ""])
def test_l4_invalid_period_is_rejected_before_touching_the_filesystem(
    tmp_path: Path,
    period: str,
) -> None:
    writer = make_writer(tmp_path)

    with pytest.raises(ValueError, match="invalid period"):
        writer.regenerate_messages(period)
    with pytest.raises(ValueError, match="invalid period"):
        writer.recover_orphan_media(period)
    assert list(tmp_path.iterdir()) == []


def test_l4_photo_path_cannot_escape_storage_root(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    storage_root.mkdir()

    inside = resolve_storage_path(storage_root, "timeline/2026/2026-07/photos/a.jpg")
    assert inside == storage_root.resolve() / "timeline/2026/2026-07/photos/a.jpg"
    assert resolve_storage_path(storage_root, "../auth.sqlite3") is None
    assert resolve_storage_path(storage_root, "timeline/../../auth.sqlite3") is None
    assert resolve_storage_path(storage_root, "/etc/passwd") is None
    assert resolve_storage_path(storage_root, "") is None


def test_m5_recovery_cli_recovers_orphans_in_every_partition(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    append_text(make_writer(tmp_path), "01J_MSG_JULY", "2026-07-12T10:00:00+09:00", "july")
    for period in ("2026-07", "2026-08"):
        photos_dir = partition_path(tmp_path, period) / "photos"
        photos_dir.mkdir(parents=True, exist_ok=True)
        (photos_dir / "IMG_0001.jpg").write_bytes(period.encode())
    (tmp_path / "timeline" / "2026" / "not-a-period").mkdir()

    exit_code = recover.main(["--storage-root", str(tmp_path), "--timezone", "Asia/Seoul"])

    assert exit_code == 0
    assert "2026-07: recovered 1" in capsys.readouterr().out
    assert len(read_metadata(tmp_path, "2026-07")["logs"]) == 2  # type: ignore[arg-type]
    assert len(read_metadata(tmp_path, "2026-08")["logs"]) == 1  # type: ignore[arg-type]
    assert recover.recover_all_periods(tmp_path, "Asia/Seoul") == {}


def test_m6_search_matches_values_only_and_finds_quoted_text(tmp_path: Path) -> None:
    writer = make_writer(tmp_path)
    append_text(writer, "01J_MSG_QUOTE", "2026-07-12T10:00:00+09:00", 'UserB said "안녕"')
    append_text(writer, "01J_MSG_PLAIN", "2026-07-12T11:00:00+09:00", "오늘 저녁")
    writer.append_photo(
        log_id="01J_PHOTO_PARK",
        actor_id="01J_USER_B",
        created_at=dt("2026-07-12T12:00:00+09:00"),
        photo_bytes=b"park",
        original_filename="park-walk.jpg",
        mime_type="image/jpeg",
    )

    def search_ids(query: str) -> list[str]:
        return [log["id"] for log in search_timeline_logs(tmp_path, query)]

    for key_like_query in ["text", "payload", "default", "sha256", "01J_MSG", "timeline/"]:
        assert search_ids(key_like_query) == [], key_like_query
    # A quote matches only the message that really contains one.
    assert search_ids('"') == ["01J_MSG_QUOTE"]
    assert search_ids('"안녕"') == ["01J_MSG_QUOTE"]
    assert search_ids("park-walk") == ["01J_PHOTO_PARK"]
    assert search_ids("UserB") == ["01J_MSG_QUOTE", "01J_PHOTO_PARK"]


def make_auth(tmp_path: Path) -> AuthService:
    return AuthService(
        db_path=tmp_path / "auth.sqlite3",
        jwt_secret="test-secret",
        hash_secret="test-hash-secret",
    )


def register_user_a(auth: AuthService) -> dict[str, Any]:
    auth.create_invite_code(code="invite-slot-1", intended_slot=1)
    return auth.register_with_invite(
        code="invite-slot-1",
        display_name="UserA",
        device_label="phone",
        device_fingerprint="fingerprint-phone",
    )


def test_m7_revoked_device_can_register_again_without_reviving_old_sessions(
    tmp_path: Path,
) -> None:
    auth = make_auth(tmp_path)
    registered = register_user_a(auth)
    user_id = registered["user"]["id"]
    old_device_id = registered["device"]["id"]
    auth.revoke_device(old_device_id)

    again = auth.create_device_session(
        user_id=user_id,
        device_label="phone (found)",
        device_fingerprint="fingerprint-phone",
    )

    assert again["device"]["id"] == old_device_id
    assert again["device"]["revoked_at"] is None
    assert "access_token" in auth.refresh_access_token(again["refresh_token"])
    with pytest.raises(AuthError):
        auth.refresh_access_token(registered["refresh_token"])
    # An active device with the same fingerprint is a clear error, not a 500.
    with pytest.raises(AuthError, match="already registered"):
        auth.create_device_session(
            user_id=user_id,
            device_label="phone copy",
            device_fingerprint="fingerprint-phone",
        )


def make_revoking_websocket(access_token: str, revoke: Callable[[], None]) -> SimpleNamespace:
    """Fake socket (no class): two pings, and the device is revoked before the second."""
    state = SimpleNamespace(received_count=0, sent=[], closed=None)

    async def accept() -> None:
        return None

    async def close(code: int = 1000, reason: str | None = None) -> None:
        state.closed = (code, reason)

    async def send_json(data: Any) -> None:
        state.sent.append(data)

    async def receive_json() -> dict[str, Any]:
        state.received_count += 1
        if state.received_count == 2:
            revoke()
        if state.received_count > 2:
            raise WebSocketDisconnect(code=1000)
        return {"type": "ping"}

    state.query_params = {"access_token": access_token}
    state.accept = accept
    state.close = close
    state.send_json = send_json
    state.receive_json = receive_json
    return state


def test_m8_open_timeline_websocket_is_closed_after_device_revocation(tmp_path: Path) -> None:
    auth = make_auth(tmp_path)
    registered = register_user_a(auth)

    def revoke() -> None:
        auth.revoke_device(registered["device"]["id"])

    websocket = make_revoking_websocket(registered["access_token"], revoke)
    asyncio.run(handle_timeline_websocket(websocket, auth))

    assert [message["type"] for message in websocket.sent] == ["timeline.ready", "pong"]
    assert websocket.closed == (1008, "session revoked")


def valid_env(tmp_path: Path) -> dict[str, str]:
    return {
        "DURI_STORAGE_ROOT": str(tmp_path / "DuriStorage"),
        "DURI_AUTH_DB": str(tmp_path / "auth" / "auth.sqlite3"),
        "DURI_JWT_SECRET": "j" * 32,
        "DURI_HASH_SECRET": "h" * 32,
        "DURI_CORS_ORIGINS": "https://example.test, http://localhost:3000",
    }


async def get_timeline(app: FastAPI, access_token: str | None) -> httpx.Response:
    headers = {}
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get("/timeline", headers=headers)


def test_m9_app_from_env_wires_auth_and_storage(tmp_path: Path) -> None:
    environ = valid_env(tmp_path)
    append_text(
        make_writer(Path(environ["DURI_STORAGE_ROOT"])),
        "01J_MSG_ENV",
        "2026-07-12T10:00:00+09:00",
        "env",
    )
    app = create_app_from_env(environ)
    auth = AuthService(
        db_path=Path(environ["DURI_AUTH_DB"]),
        jwt_secret=environ["DURI_JWT_SECRET"],
        hash_secret=environ["DURI_HASH_SECRET"],
    )
    registered = register_user_a(auth)

    response = asyncio.run(get_timeline(app, registered["access_token"]))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["01J_MSG_ENV"]
    assert asyncio.run(get_timeline(app, None)).status_code == 401


def test_m9_default_app_denies_and_env_app_refuses_missing_or_weak_secrets(
    tmp_path: Path,
) -> None:
    assert asyncio.run(get_timeline(default_app, None)).status_code == 401

    environ = valid_env(tmp_path)
    del environ["DURI_AUTH_DB"]
    with pytest.raises(ValueError, match="DURI_AUTH_DB"):
        create_app_from_env(environ)

    environ = valid_env(tmp_path)
    environ["DURI_JWT_SECRET"] = "short"
    with pytest.raises(ValueError, match="at least 32 bytes"):
        create_app_from_env(environ)


def test_l3_failed_messages_md_write_keeps_the_previous_file_whole(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    writer = make_writer(tmp_path)
    append_text(writer, "01J_MSG_FIRST", "2026-07-12T10:00:00+09:00", "first")
    messages_path = partition_path(tmp_path, "2026-07") / "messages.md"
    before = messages_path.read_text(encoding="utf-8")
    real_replace = os.replace

    def fail_messages_replace(source: Any, destination: Any) -> None:
        if Path(destination).name == "messages.md":
            raise OSError("simulated crash while publishing messages.md")
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_messages_replace)
    append_text(writer, "01J_MSG_SECOND", "2026-07-12T11:00:00+09:00", "second")

    assert messages_path.read_text(encoding="utf-8") == before
    assert list(partition_path(tmp_path, "2026-07").glob("*.tmp")) == []
    assert len(read_metadata(tmp_path, "2026-07")["logs"]) == 2  # type: ignore[arg-type]
