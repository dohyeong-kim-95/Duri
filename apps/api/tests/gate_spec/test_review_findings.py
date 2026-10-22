from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from duri_api import timeline_index
from duri_api.storage import (
    DuriStorageWriter,
    StorageWriteHooks,
    query_timeline_index,
    rebuild_timeline_index,
)

PARTICIPANTS = {
    "01J_USER_1": "Dohyeong",
    "01J_USER_2": "Partner",
}


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def make_writer(
    storage_root: Path,
    hooks: StorageWriteHooks | None = None,
) -> DuriStorageWriter:
    return DuriStorageWriter(
        storage_root=storage_root,
        participants=PARTICIPANTS,
        app_timezone="Asia/Seoul",
        hooks=hooks,
    )


def read_metadata(storage_root: Path, period: str) -> dict[str, object]:
    metadata_path = storage_root / "timeline" / period[:4] / period / "metadata.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


@pytest.mark.gate_spec(
    "R-H1-1. `metadata.json` 확정 뒤 `messages.md` 재생성이 실패해도 쓰기는 성공으로 반환된다."
)
def test_r_h1_1_messages_failure_after_metadata_commit_is_reported_as_success(
    tmp_path: Path,
) -> None:
    """R-H1-1. `metadata.json` 확정 뒤 `messages.md` 재생성이 실패해도 쓰기는 성공으로 반환된다."""

    def fail_before_messages_write(_messages_path: Path) -> None:
        raise RuntimeError("simulated messages failure")

    writer = make_writer(
        tmp_path,
        hooks=StorageWriteHooks(before_messages_write=fail_before_messages_write),
    )

    log = writer.append_message(
        log_id="01J_MSG_R_H1_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_R_H1_1",
        text="정본은 이미 저장됐다",
    )

    assert log["id"] == "01J_MSG_R_H1_1"
    metadata = read_metadata(tmp_path, "2026-07")
    assert [item["id"] for item in metadata["logs"]] == ["01J_MSG_R_H1_1"]  # type: ignore[attr-defined]


@pytest.mark.gate_spec(
    "R-H1-2. 같은 `log_id`로 다시 쓰면 중복 Log를 만들지 않고 기존 Log를 반환한다 (메시지·사진 모두)."
)
def test_r_h1_2_retry_with_same_log_id_is_idempotent(tmp_path: Path) -> None:
    """R-H1-2. 같은 `log_id`로 다시 쓰면 중복 Log를 만들지 않고 기존 Log를 반환한다 (메시지·사진 모두)."""
    writer = make_writer(tmp_path)
    first_message = writer.append_message(
        log_id="01J_MSG_R_H1_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_R_H1_2",
        text="첫 시도",
    )
    second_message = writer.append_message(
        log_id="01J_MSG_R_H1_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_R_H1_2",
        text="재시도",
    )
    first_photo = writer.append_photo(
        log_id="01J_PHOTO_R_H1_2",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"first upload",
        original_filename="retry.jpg",
        mime_type="image/jpeg",
    )
    second_photo = writer.append_photo(
        log_id="01J_PHOTO_R_H1_2",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"re-encoded retry upload",
        original_filename="retry.jpg",
        mime_type="image/jpeg",
    )

    assert second_message == first_message
    assert second_photo["media_ref"] == first_photo["media_ref"]
    metadata = read_metadata(tmp_path, "2026-07")
    log_ids = [log["id"] for log in metadata["logs"]]  # type: ignore[attr-defined]
    assert log_ids == ["01J_MSG_R_H1_2", "01J_PHOTO_R_H1_2"]
    photos_dir = tmp_path / "timeline" / "2026" / "2026-07" / "photos"
    assert len(list(photos_dir.iterdir())) == 1


def write_raw_metadata(storage_root: Path, period: str, metadata: dict[str, object]) -> None:
    partition = storage_root / "timeline" / period[:4] / period
    partition.mkdir(parents=True, exist_ok=True)
    (partition / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
    )


@pytest.mark.gate_spec(
    "R-H2-1. 정본에 같은 `id`가 중복돼도 인덱스 재구축은 실패하지 않고, 실패하더라도 기존 인덱스는 남는다."
)
def test_r_h2_1_index_rebuild_tolerates_duplicate_ids_and_keeps_old_index_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R-H2-1. 정본에 같은 `id`가 중복돼도 인덱스 재구축은 실패하지 않고, 실패하더라도 기존 인덱스는 남는다."""
    storage_root = tmp_path / "DuriStorage"
    duplicated_log = {
        "id": "01J_MSG_DUP",
        "type": "Message",
        "created_at": "2026-07-12T19:28:00+09:00",
        "actor_id": "01J_USER_1",
        "payload": {"text": "중복"},
    }
    write_raw_metadata(
        storage_root,
        "2026-07",
        {
            "schema_version": 1,
            "period": "2026-07",
            "participants": {},
            "logs": [duplicated_log, dict(duplicated_log)],
        },
    )
    db_path = tmp_path / "indexes" / "timeline.sqlite3"

    rebuild_timeline_index(storage_root, db_path)
    assert [row["log_id"] for row in query_timeline_index(db_path)] == ["01J_MSG_DUP"]

    # A rebuild that fails midway must not leave the index dropped.
    def fail_search_text(_log: dict[str, object]) -> str:
        raise RuntimeError("simulated rebuild failure")

    monkeypatch.setattr(timeline_index, "timeline_search_text", fail_search_text)
    with pytest.raises(RuntimeError):
        rebuild_timeline_index(storage_root, db_path)
    assert [row["log_id"] for row in query_timeline_index(db_path)] == ["01J_MSG_DUP"]
