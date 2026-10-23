"""Regression tests for the medium/low code review findings (M*, L*)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

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
