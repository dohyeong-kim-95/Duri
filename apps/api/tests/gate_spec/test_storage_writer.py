from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

from duri_api.storage import (
    DuriStorageWriter,
    StorageWriteError,
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
    *,
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
    "A1-1. 업로드된 사진의 바이트는 `photos/`에 저장된 파일과 정확히 동일하다 (sha256 일치)."
)
def test_a1_1_uploaded_photo_bytes_are_stored_without_loss(tmp_path: Path) -> None:
    """A1-1. 업로드된 사진의 바이트는 `photos/`에 저장된 파일과 정확히 동일하다 (sha256 일치)."""
    photo_bytes = b"\xff\xd8original photo bytes\xff\xd9"

    result = make_writer(tmp_path).append_photo(
        log_id="01J_PHOTO_A1_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=photo_bytes,
        original_filename="original.jpg",
        mime_type="image/jpeg",
    )

    stored_file = tmp_path / result["media_ref"]["storage_path"]
    assert stored_file.read_bytes() == photo_bytes
    assert result["media_ref"]["sha256"] == hashlib.sha256(photo_bytes).hexdigest()


@pytest.mark.gate_spec(
    "A1-2. 사진 저장 후 `metadata.json`의 MediaRef는 실제 파일의 크기·해시와 일치한다."
)
def test_a1_2_photo_media_ref_matches_actual_file_size_and_hash(tmp_path: Path) -> None:
    """A1-2. 사진 저장 후 `metadata.json`의 MediaRef는 실제 파일의 크기·해시와 일치한다."""
    photo_bytes = b"photo bytes for metadata"

    make_writer(tmp_path).append_photo(
        log_id="01J_PHOTO_A1_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=photo_bytes,
        original_filename="metadata.jpg",
        mime_type="image/jpeg",
    )

    metadata = read_metadata(tmp_path, "2026-07")
    media_ref = metadata["logs"][0]["media_refs"][0]  # type: ignore[index]
    stored_file = tmp_path / media_ref["storage_path"]
    assert media_ref["size_bytes"] == stored_file.stat().st_size
    assert media_ref["sha256"] == hashlib.sha256(stored_file.read_bytes()).hexdigest()


@pytest.mark.gate_spec(
    "A1-3. 어떤 재수록·재계산 경로도 저장된 payload(메시지 본문, 사진 바이트)를 변경하지 않는다."
)
def test_a1_3_reingest_and_rebuild_paths_do_not_change_payloads(tmp_path: Path) -> None:
    """A1-3. 어떤 재수록·재계산 경로도 저장된 payload(메시지 본문, 사진 바이트)를 변경하지 않는다."""
    writer = make_writer(tmp_path)
    photo_bytes = b"payload must remain stable"
    writer.append_message(
        log_id="01J_MSG_A1_3",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A1_3",
        text="오늘 저녁 뭐 먹을까?",
    )
    photo = writer.append_photo(
        log_id="01J_PHOTO_A1_3",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=photo_bytes,
        original_filename="stable.jpg",
        mime_type="image/jpeg",
    )
    before = read_metadata(tmp_path, "2026-07")
    stored_photo = tmp_path / photo["media_ref"]["storage_path"]

    writer.regenerate_messages("2026-07")
    rebuild_timeline_index(tmp_path, tmp_path / "indexes" / "timeline.sqlite3")
    writer.recover_orphan_media("2026-07")

    after = read_metadata(tmp_path, "2026-07")
    assert after["logs"] == before["logs"]
    assert stored_photo.read_bytes() == photo_bytes


@pytest.mark.gate_spec(
    "A2-1. 사진 쓰기가 원자적 rename 이전에 실패하면 `photos/`에 불완전한 파일이 남지 않는다."
)
def test_a2_1_failed_photo_write_before_atomic_rename_leaves_no_partial_file(
    tmp_path: Path,
) -> None:
    """A2-1. 사진 쓰기가 원자적 rename 이전에 실패하면 `photos/`에 불완전한 파일이 남지 않는다."""

    def fail_before_media_rename(_temp_path: Path, _final_path: Path) -> None:
        raise RuntimeError("simulated media failure")

    writer = make_writer(
        tmp_path,
        hooks=StorageWriteHooks(before_media_rename=fail_before_media_rename),
    )

    with pytest.raises(StorageWriteError):
        writer.append_photo(
            log_id="01J_PHOTO_A2_1",
            actor_id="01J_USER_1",
            created_at=dt("2026-07-12T19:30:22+09:00"),
            photo_bytes=b"partial file must not remain",
            original_filename="partial.jpg",
            mime_type="image/jpeg",
        )

    photos_dir = tmp_path / "timeline" / "2026" / "2026-07" / "photos"
    assert not photos_dir.exists() or list(photos_dir.iterdir()) == []


@pytest.mark.gate_spec(
    "A2-2. `metadata.json` 갱신 도중 프로세스가 중단되어도 이전 `metadata.json`은 온전한 JSON으로 남는다 (temp 파일 + rename 검증)."
)
def test_a2_2_previous_metadata_remains_valid_if_update_stops_before_rename(
    tmp_path: Path,
) -> None:
    """A2-2. `metadata.json` 갱신 도중 프로세스가 중단되어도 이전 `metadata.json`은 온전한 JSON으로 남는다 (temp 파일 + rename 검증)."""
    make_writer(tmp_path).append_message(
        log_id="01J_MSG_EXISTING",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_EXISTING",
        text="기존 메시지",
    )
    before = read_metadata(tmp_path, "2026-07")

    def fail_after_metadata_tmp_write(_temp_path: Path, _final_path: Path) -> None:
        raise RuntimeError("simulated metadata interruption")

    writer = make_writer(
        tmp_path,
        hooks=StorageWriteHooks(after_metadata_tmp_write=fail_after_metadata_tmp_write),
    )

    with pytest.raises(StorageWriteError):
        writer.append_message(
            log_id="01J_MSG_INTERRUPTED",
            actor_id="01J_USER_2",
            created_at=dt("2026-07-12T19:29:00+09:00"),
            message_id="01J_MESSAGE_INTERRUPTED",
            text="중단된 메시지",
        )

    metadata_path = tmp_path / "timeline" / "2026" / "2026-07" / "metadata.json"
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == before


@pytest.mark.gate_spec(
    "A2-3. `messages.md` 재생성이 실패해도 `metadata.json`과 `photos/`는 영향받지 않는다."
)
def test_a2_3_messages_regeneration_failure_does_not_affect_metadata_or_photos(
    tmp_path: Path,
) -> None:
    """A2-3. `messages.md` 재생성이 실패해도 `metadata.json`과 `photos/`는 영향받지 않는다."""

    def fail_before_messages_write(_messages_path: Path) -> None:
        raise RuntimeError("simulated messages failure")

    photo_bytes = b"photo survives derived view failure"
    writer = make_writer(
        tmp_path,
        hooks=StorageWriteHooks(before_messages_write=fail_before_messages_write),
    )

    with pytest.raises(StorageWriteError):
        writer.append_photo(
            log_id="01J_PHOTO_A2_3",
            actor_id="01J_USER_1",
            created_at=dt("2026-07-12T19:30:22+09:00"),
            photo_bytes=photo_bytes,
            original_filename="derived-failure.jpg",
            mime_type="image/jpeg",
        )

    metadata = read_metadata(tmp_path, "2026-07")
    media_ref = metadata["logs"][0]["media_refs"][0]  # type: ignore[index]
    stored_file = tmp_path / media_ref["storage_path"]
    assert stored_file.read_bytes() == photo_bytes
    assert media_ref["sha256"] == hashlib.sha256(photo_bytes).hexdigest()


@pytest.mark.gate_spec(
    "A3-1. `messages.md`를 삭제한 뒤 `metadata.json`에서 동일한 내용으로 재생성할 수 있다."
)
def test_a3_1_messages_markdown_can_be_regenerated_from_metadata(tmp_path: Path) -> None:
    """A3-1. `messages.md`를 삭제한 뒤 `metadata.json`에서 동일한 내용으로 재생성할 수 있다."""
    writer = make_writer(tmp_path)
    writer.append_message(
        log_id="01J_MSG_A3_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A3_1",
        text="오늘 저녁 뭐 먹을까?",
    )
    messages_path = tmp_path / "timeline" / "2026" / "2026-07" / "messages.md"
    before = messages_path.read_text(encoding="utf-8")

    messages_path.unlink()
    regenerated = writer.regenerate_messages("2026-07")

    assert regenerated == before
    assert messages_path.read_text(encoding="utf-8") == before


@pytest.mark.gate_spec(
    "A3-2. DB와 검색 인덱스를 삭제한 뒤 `DuriStorage/`만으로 전부 재구축할 수 있고, 재구축 결과로 동일한 Timeline 조회가 가능하다."
)
def test_a3_2_timeline_index_can_be_rebuilt_from_duri_storage(tmp_path: Path) -> None:
    """A3-2. DB와 검색 인덱스를 삭제한 뒤 `DuriStorage/`만으로 전부 재구축할 수 있고, 재구축 결과로 동일한 Timeline 조회가 가능하다."""
    writer = make_writer(tmp_path)
    writer.append_message(
        log_id="01J_MSG_A3_2_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A3_2_1",
        text="첫 메시지",
    )
    writer.append_photo(
        log_id="01J_PHOTO_A3_2_2",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"index rebuild photo",
        original_filename="index.jpg",
        mime_type="image/jpeg",
    )

    db_path = tmp_path / "indexes" / "timeline.sqlite3"
    rebuild_timeline_index(tmp_path, db_path)
    first_query = query_timeline_index(db_path)
    db_path.unlink()
    assert not db_path.exists()

    rebuild_timeline_index(tmp_path, db_path)
    assert query_timeline_index(db_path) == first_query


@pytest.mark.gate_spec(
    "A3-3. `metadata.json`에는 참여자 표시 이름 맵(`participants`)이 포함되어, 파일만 읽어도 발화자를 알 수 있다."
)
def test_a3_3_metadata_contains_participant_display_names(tmp_path: Path) -> None:
    """A3-3. `metadata.json`에는 참여자 표시 이름 맵(`participants`)이 포함되어, 파일만 읽어도 발화자를 알 수 있다."""
    make_writer(tmp_path).append_message(
        log_id="01J_MSG_A3_3",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A3_3",
        text="발화자를 파일만 보고 알아야 한다",
    )

    metadata = read_metadata(tmp_path, "2026-07")
    assert metadata["participants"] == {
        "01J_USER_1": {"display_name": "Dohyeong"},
        "01J_USER_2": {"display_name": "Partner"},
    }


@pytest.mark.gate_spec(
    "A4-1. `photos/`에 있으나 `metadata.json`에 없는 파일은 복구 스캔에서 삭제되지 않고 재수록된다."
)
def test_a4_1_orphan_photo_is_reingested_not_deleted(tmp_path: Path) -> None:
    """A4-1. `photos/`에 있으나 `metadata.json`에 없는 파일은 복구 스캔에서 삭제되지 않고 재수록된다."""
    writer = make_writer(tmp_path)
    writer.append_message(
        log_id="01J_MSG_A4_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A4_1",
        text="복구 스캔 기준 월 생성",
    )
    orphan_path = tmp_path / "timeline" / "2026" / "2026-07" / "photos" / "orphan.jpg"
    orphan_bytes = b"orphan media bytes"
    orphan_path.write_bytes(orphan_bytes)

    recovered = writer.recover_orphan_media("2026-07")

    assert orphan_path.exists()
    assert len(recovered) == 1
    metadata = read_metadata(tmp_path, "2026-07")
    media_paths = [
        media_ref["storage_path"]
        for log in metadata["logs"]  # type: ignore[index]
        for media_ref in log.get("media_refs", [])
    ]
    assert str(orphan_path.relative_to(tmp_path)) in media_paths


@pytest.mark.gate_spec("A4-2. 복구 스캔은 기존 `metadata.json` 항목을 변경하지 않는다.")
def test_a4_2_recovery_scan_does_not_change_existing_metadata_entries(tmp_path: Path) -> None:
    """A4-2. 복구 스캔은 기존 `metadata.json` 항목을 변경하지 않는다."""
    writer = make_writer(tmp_path)
    writer.append_message(
        log_id="01J_MSG_A4_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_A4_2",
        text="기존 항목은 그대로 남아야 한다",
    )
    before_logs = deepcopy(read_metadata(tmp_path, "2026-07")["logs"])
    orphan_path = tmp_path / "timeline" / "2026" / "2026-07" / "photos" / "orphan-a4-2.jpg"
    orphan_path.write_bytes(b"orphan media bytes")

    writer.recover_orphan_media("2026-07")

    after_logs = read_metadata(tmp_path, "2026-07")["logs"]
    assert after_logs[: len(before_logs)] == before_logs


@pytest.mark.gate_spec(
    "A5-1. 같은 월 파티션에 대한 동시 쓰기 요청 2건이 모두 유실 없이 `metadata.json`에 반영된다 (직렬화 검증)."
)
def test_a5_1_concurrent_writes_to_same_month_are_serialized_without_loss(
    tmp_path: Path,
) -> None:
    """A5-1. 같은 월 파티션에 대한 동시 쓰기 요청 2건이 모두 유실 없이 `metadata.json`에 반영된다 (직렬화 검증)."""
    writer = make_writer(tmp_path)

    def append(index: int) -> None:
        writer.append_message(
            log_id=f"01J_MSG_A5_1_{index}",
            actor_id="01J_USER_1",
            created_at=dt(f"2026-07-12T19:2{index}:00+09:00"),
            message_id=f"01J_MESSAGE_A5_1_{index}",
            text=f"동시 메시지 {index}",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(append, [1, 2]))

    metadata = read_metadata(tmp_path, "2026-07")
    log_ids = {log["id"] for log in metadata["logs"]}  # type: ignore[index]
    assert log_ids == {"01J_MSG_A5_1_1", "01J_MSG_A5_1_2"}


@pytest.mark.gate_spec(
    "A5-2. Log는 `created_at`(앱 타임존)의 월 파티션에 저장된다 — 월 경계(말일 23:59 / 익월 00:00) 케이스 포함."
)
def test_a5_2_partition_uses_created_at_app_timezone_including_month_boundary(
    tmp_path: Path,
) -> None:
    """A5-2. Log는 `created_at`(앱 타임존)의 월 파티션에 저장된다 — 월 경계(말일 23:59 / 익월 00:00) 케이스 포함."""
    writer = make_writer(tmp_path)
    writer.append_message(
        log_id="01J_MSG_JULY_BOUNDARY",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-31T23:59:00+09:00"),
        message_id="01J_MESSAGE_JULY_BOUNDARY",
        text="7월 마지막 메시지",
    )
    writer.append_message(
        log_id="01J_MSG_AUGUST_BOUNDARY",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T00:00:00+09:00"),
        message_id="01J_MESSAGE_AUGUST_BOUNDARY",
        text="8월 첫 메시지",
    )

    assert read_metadata(tmp_path, "2026-07")["logs"][0]["id"] == "01J_MSG_JULY_BOUNDARY"  # type: ignore[index]
    assert read_metadata(tmp_path, "2026-08")["logs"][0]["id"] == "01J_MSG_AUGUST_BOUNDARY"  # type: ignore[index]


@pytest.mark.gate_spec(
    "A5-3. EXIF `captured_at`이 `created_at`과 다른 달이어도 파티션은 `created_at`을 따른다."
)
def test_a5_3_photo_partition_uses_created_at_even_when_exif_captured_at_differs(
    tmp_path: Path,
) -> None:
    """A5-3. EXIF `captured_at`이 `created_at`과 다른 달이어도 파티션은 `created_at`을 따른다."""
    writer = make_writer(tmp_path)

    writer.append_photo(
        log_id="01J_PHOTO_A5_3",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-01T00:05:00+09:00"),
        photo_bytes=b"captured in june uploaded in july",
        original_filename="captured-in-june.jpg",
        mime_type="image/jpeg",
        captured_at=dt("2026-06-30T22:00:00+09:00"),
    )

    assert read_metadata(tmp_path, "2026-07")["logs"][0]["id"] == "01J_PHOTO_A5_3"  # type: ignore[index]
    assert not (tmp_path / "timeline" / "2026" / "2026-06" / "metadata.json").exists()
