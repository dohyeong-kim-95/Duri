from __future__ import annotations

import json
import sqlite3
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
    "R-H1-2. 같은 `log_id`로 같은 내용을 다시 쓰면 중복 Log를 만들지 않고 기존 Log를 반환하고, 다른 내용(type·actor·시각·본문)이면 기존 Log를 돌려주지 않고 오류로 거부한다 (메시지·사진 모두, 사진의 재인코딩 바이트 차이는 같은 내용으로 본다)."
)
def test_r_h1_2_retry_with_same_log_id_is_idempotent_and_conflicts_are_rejected(
    tmp_path: Path,
) -> None:
    """R-H1-2. 같은 `log_id`로 같은 내용을 다시 쓰면 중복 Log를 만들지 않고 기존 Log를 반환하고, 다른 내용(type·actor·시각·본문)이면 기존 Log를 돌려주지 않고 오류로 거부한다 (메시지·사진 모두, 사진의 재인코딩 바이트 차이는 같은 내용으로 본다)."""
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
        text="첫 시도",
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

    # Same id, different content: a client id bug. Must not silently return the old Log.
    with pytest.raises(StorageWriteError, match="different content"):
        writer.append_message(
            log_id="01J_MSG_R_H1_2",
            actor_id="01J_USER_2",
            created_at=dt("2026-07-12T20:00:00+09:00"),
            message_id="01J_MESSAGE_R_H1_2",
            text="DIFFERENT TEXT",
        )
    with pytest.raises(StorageWriteError, match="different content"):
        writer.append_message(
            log_id="01J_PHOTO_R_H1_2",
            actor_id="01J_USER_2",
            created_at=dt("2026-07-12T19:30:22+09:00"),
            message_id="01J_MESSAGE_R_H1_2_PHOTO_ID",
            text="photo id reused for a message",
        )
    with pytest.raises(StorageWriteError, match="different content"):
        writer.append_photo(
            log_id="01J_PHOTO_R_H1_2",
            actor_id="01J_USER_1",
            created_at=dt("2026-07-12T19:30:22+09:00"),
            photo_bytes=b"someone else's photo",
            original_filename="other.jpg",
            mime_type="image/jpeg",
        )
    assert read_metadata(tmp_path, "2026-07") == metadata
    assert len(list(photos_dir.iterdir())) == 1


@pytest.mark.gate_spec(
    "R-H1-3. `metadata.json` 확정 뒤에는 `messages.md` 렌더링·쓰기에서 어떤 예외가 나도 쓰기와 orphan 복구는 성공으로 반환된다."
)
def test_r_h1_3_any_messages_failure_after_commit_is_swallowed(tmp_path: Path) -> None:
    """R-H1-3. `metadata.json` 확정 뒤에는 `messages.md` 렌더링·쓰기에서 어떤 예외가 나도 쓰기와 orphan 복구는 성공으로 반환된다."""
    # A hand-edited Message without payload.text makes rendering raise KeyError.
    write_raw_metadata(
        tmp_path,
        "2026-07",
        {
            "schema_version": 1,
            "period": "2026-07",
            "timezone": "Asia/Seoul",
            "participants": {},
            "logs": [
                {
                    "id": "01J_MSG_HAND_EDITED",
                    "type": "Message",
                    "created_at": "2026-07-01T10:00:00+09:00",
                    "actor_id": "01J_USER_1",
                    "payload": {},
                }
            ],
        },
    )
    writer = make_writer(tmp_path)

    log = writer.append_message(
        log_id="01J_MSG_R_H1_3",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_R_H1_3",
        text="렌더링이 실패해도 정본은 저장된다",
    )
    assert log["id"] == "01J_MSG_R_H1_3"

    def fail_before_messages_write(_messages_path: Path) -> None:
        raise RuntimeError("simulated messages failure")

    photos_dir = tmp_path / "timeline" / "2026" / "2026-08" / "photos"
    photos_dir.mkdir(parents=True)
    (photos_dir / "IMG_0002.jpg").write_bytes(b"orphan")
    failing_writer = make_writer(
        tmp_path,
        hooks=StorageWriteHooks(before_messages_write=fail_before_messages_write),
    )

    recovered = failing_writer.recover_orphan_media("2026-08")

    assert len(recovered) == 1
    metadata_ids = [item["id"] for item in read_metadata(tmp_path, "2026-08")["logs"]]  # type: ignore[attr-defined]
    assert metadata_ids == [recovered[0]["id"]]


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
    "R-H2-2. 인덱스 재구축은 옛 인덱스에 남은 `-wal`/`-shm` 파일을 새 인덱스에 적용하지 않고, 임시 파일을 남기지 않는다."
)
def test_r_h2_2_index_rebuild_ignores_stale_wal_and_leaves_no_temp_files(tmp_path: Path) -> None:
    """R-H2-2. 인덱스 재구축은 옛 인덱스에 남은 `-wal`/`-shm` 파일을 새 인덱스에 적용하지 않고, 임시 파일을 남기지 않는다."""
    storage_root = tmp_path / "DuriStorage"
    make_writer(storage_root).append_message(
        log_id="01J_MSG_R_H2_2",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_R_H2_2",
        text="정본",
    )
    db_path = tmp_path / "indexes" / "timeline.sqlite3"
    rebuild_timeline_index(storage_root, db_path)

    # Someone opened the index in WAL mode and left an uncheckpointed ghost row.
    writer_connection = sqlite3.connect(db_path)
    writer_connection.execute("PRAGMA journal_mode=WAL")
    writer_connection.execute(
        "INSERT INTO timeline VALUES ('GHOST', 'Message', 'x', 'U', '', '2026-07', '', '{}')"
    )
    writer_connection.commit()
    reader_connection = sqlite3.connect(db_path)
    reader_connection.execute("SELECT COUNT(*) FROM timeline").fetchone()
    try:
        rebuild_timeline_index(storage_root, db_path)
        assert [row["log_id"] for row in query_timeline_index(db_path)] == ["01J_MSG_R_H2_2"]
    finally:
        writer_connection.close()
        reader_connection.close()

    leftover = [path.name for path in db_path.parent.iterdir() if ".rebuild." in path.name]
    assert leftover == []


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
    'R-H5-1. `schema_version`이 없는 `metadata.json`은 Timeline/Summary에서 건너뛰며, `period: "None"` 같은 잘못된 결과를 내지 않는다.'
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
    assert summary["periods"] == [{"period": "2026-08", "total": 1, "types": {"Message": 1}}]


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
