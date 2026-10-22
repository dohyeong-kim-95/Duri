from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from duri_api.storage import DuriStorageWriter, StorageWriteHooks

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
