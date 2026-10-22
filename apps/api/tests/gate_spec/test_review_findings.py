from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from duri_api import timeline_index
from duri_api.storage import (
    DuriStorageWriter,
    StorageWriteError,
    StorageWriteHooks,
    query_timeline_index,
    rebuild_timeline_index,
)
from duri_api.timeline import read_timeline_logs, read_timeline_summary

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


@pytest.mark.gate_spec(
    "R-H3-1. 사진 파일명이 겹쳐도 기존 원본 사진은 덮어써지지 않는다 — 같은 바이트면 기존 파일을 재사용하고, 다른 바이트면 새 이름으로 저장한다."
)
def test_r_h3_1_photo_filename_collision_never_overwrites_existing_original(
    tmp_path: Path,
) -> None:
    """R-H3-1. 사진 파일명이 겹쳐도 기존 원본 사진은 덮어써지지 않는다 — 같은 바이트면 기존 파일을 재사용하고, 다른 바이트면 새 이름으로 저장한다."""
    writer = make_writer(tmp_path)
    created_at = dt("2026-07-12T19:30:22+09:00")
    first = writer.append_photo(
        log_id="01J_PHOTO.1",
        actor_id="01J_USER_1",
        created_at=created_at,
        photo_bytes=b"first original",
        original_filename="a.jpg",
        mime_type="image/jpeg",
    )
    # "01J_PHOTO_1" sanitizes to the same filename as "01J_PHOTO.1".
    second = writer.append_photo(
        log_id="01J_PHOTO_1",
        actor_id="01J_USER_2",
        created_at=created_at,
        photo_bytes=b"different bytes",
        original_filename="b.jpg",
        mime_type="image/jpeg",
    )
    third = writer.append_photo(
        log_id="01J_PHOTO-1",
        actor_id="01J_USER_2",
        created_at=created_at,
        photo_bytes=b"first original",
        original_filename="c.jpg",
        mime_type="image/jpeg",
    )

    first_path = tmp_path / first["media_ref"]["storage_path"]
    second_path = tmp_path / second["media_ref"]["storage_path"]
    assert first_path.read_bytes() == b"first original"
    assert second_path != first_path
    assert second_path.name.endswith("_2.jpg")
    assert second_path.read_bytes() == b"different bytes"
    # Identical bytes under a non-colliding name are simply stored normally.
    assert (tmp_path / third["media_ref"]["storage_path"]).read_bytes() == b"first original"


@pytest.mark.gate_spec(
    "R-H3-2. 이미 같은 바이트의 사진 파일이 있는 경로로 다시 쓰면 파일을 새로 만들지 않고 그 파일을 참조한다 (크래시 후 재시도)."
)
def test_r_h3_2_existing_identical_photo_file_is_reused(tmp_path: Path) -> None:
    """R-H3-2. 이미 같은 바이트의 사진 파일이 있는 경로로 다시 쓰면 파일을 새로 만들지 않고 그 파일을 참조한다 (크래시 후 재시도)."""
    photos_dir = tmp_path / "timeline" / "2026" / "2026-07" / "photos"
    photos_dir.mkdir(parents=True)
    # Simulates a crash after the photo rename but before metadata.json was written.
    (photos_dir / "2026-07-12T19-30-22_01J_PHOTO_R_H3_2.jpg").write_bytes(b"same bytes")

    result = make_writer(tmp_path).append_photo(
        log_id="01J_PHOTO_R_H3_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"same bytes",
        original_filename="retry.jpg",
        mime_type="image/jpeg",
    )

    assert result["media_ref"]["storage_path"].endswith("2026-07-12T19-30-22_01J_PHOTO_R_H3_2.jpg")
    assert [path.name for path in photos_dir.iterdir()] == [
        "2026-07-12T19-30-22_01J_PHOTO_R_H3_2.jpg"
    ]


@pytest.mark.gate_spec(
    "R-H4-1. 같은 바이트의 orphan 파일 두 개는 서로 다른 id로 복구되고, 복구 뒤에도 인덱스 재구축이 가능하다."
)
def test_r_h4_1_identical_orphans_get_distinct_ids(tmp_path: Path) -> None:
    """R-H4-1. 같은 바이트의 orphan 파일 두 개는 서로 다른 id로 복구되고, 복구 뒤에도 인덱스 재구축이 가능하다."""
    photos_dir = tmp_path / "timeline" / "2026" / "2026-07" / "photos"
    photos_dir.mkdir(parents=True)
    (photos_dir / "copy-a.jpg").write_bytes(b"same photo")
    (photos_dir / "copy-b.jpg").write_bytes(b"same photo")

    recovered = make_writer(tmp_path).recover_orphan_media("2026-07")

    recovered_ids = {log["id"] for log in recovered}
    assert len(recovered_ids) == 2
    db_path = tmp_path / "indexes" / "timeline.sqlite3"
    rebuild_timeline_index(tmp_path, db_path)
    assert len(query_timeline_index(db_path)) == 2


@pytest.mark.gate_spec(
    "R-H4-2. writer가 만든 파일명(`<created_at>_<log_id>.ext`)의 orphan은 원래 시각과 log_id로 복구되고, 그 외 파일만 월 시작 시각으로 복구된다."
)
def test_r_h4_2_orphan_from_writer_filename_keeps_created_at_and_log_id(
    tmp_path: Path,
) -> None:
    """R-H4-2. writer가 만든 파일명(`<created_at>_<log_id>.ext`)의 orphan은 원래 시각과 log_id로 복구되고, 그 외 파일만 월 시작 시각으로 복구된다."""
    photos_dir = tmp_path / "timeline" / "2026" / "2026-07" / "photos"
    photos_dir.mkdir(parents=True)
    (photos_dir / "2026-07-25T21-10-00_01J_PHOTO_CRASHED.jpg").write_bytes(b"crashed")
    (photos_dir / "IMG_0001.jpg").write_bytes(b"manual copy")

    recovered = make_writer(tmp_path).recover_orphan_media("2026-07")

    by_filename = {log["media_refs"][0]["original_filename"]: log for log in recovered}
    crashed = by_filename["2026-07-25T21-10-00_01J_PHOTO_CRASHED.jpg"]
    manual = by_filename["IMG_0001.jpg"]
    assert crashed["id"] == "01J_PHOTO_CRASHED"
    assert crashed["created_at"] == "2026-07-25T21:10:00+09:00"
    assert manual["id"].startswith("RECOVERED_")
    assert manual["created_at"] == "2026-07-01T00:00:00+09:00"


SINK_FORMAT_METADATA: dict[str, object] = {
    "month": "2026-07",
    "logs": [{"seq": 1, "at": 1752300000000, "name": "A", "type": "message", "text": "hi"}],
}


@pytest.mark.gate_spec(
    "R-H5-1. `schema_version`이 없는 `metadata.json`은 Timeline/Summary에서 건너뛰며, `period: \"None\"` 같은 잘못된 결과를 내지 않는다."
)
def test_r_h5_1_readers_skip_metadata_without_schema_version(tmp_path: Path) -> None:
    """R-H5-1. `schema_version`이 없는 `metadata.json`은 Timeline/Summary에서 건너뛰며, `period: "None"` 같은 잘못된 결과를 내지 않는다."""
    write_raw_metadata(tmp_path, "2026-07", SINK_FORMAT_METADATA)
    make_writer(tmp_path).append_message(
        log_id="01J_MSG_R_H5_1",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_R_H5_1",
        text="RFC 포맷 메시지",
    )

    logs = read_timeline_logs(tmp_path)
    summary = read_timeline_summary(tmp_path)

    assert [log["id"] for log in logs] == ["01J_MSG_R_H5_1"]
    assert summary["periods"] == [
        {"period": "2026-08", "total": 1, "types": {"Message": 1}}
    ]


@pytest.mark.gate_spec(
    "R-H5-2. writer는 `schema_version`이 없는 기존 `metadata.json`을 덮어쓰지 않고 명확한 오류로 거부한다."
)
def test_r_h5_2_writer_refuses_metadata_without_schema_version(tmp_path: Path) -> None:
    """R-H5-2. writer는 `schema_version`이 없는 기존 `metadata.json`을 덮어쓰지 않고 명확한 오류로 거부한다."""
    write_raw_metadata(tmp_path, "2026-07", SINK_FORMAT_METADATA)
    metadata_path = tmp_path / "timeline" / "2026" / "2026-07" / "metadata.json"
    before = metadata_path.read_text(encoding="utf-8")

    with pytest.raises(StorageWriteError, match="schema_version"):
        make_writer(tmp_path).append_message(
            log_id="01J_MSG_R_H5_2",
            actor_id="01J_USER_1",
            created_at=dt("2026-07-12T19:28:00+09:00"),
            message_id="01J_MESSAGE_R_H5_2",
            text="sink 파일에 쓰면 안 된다",
        )

    assert metadata_path.read_text(encoding="utf-8") == before
