from __future__ import annotations

from datetime import datetime
from pathlib import Path

from duri_api.storage import DuriStorageWriter, rebuild_timeline_index
from duri_api.timeline import search_timeline_logs
from duri_api.timeline_index import (
    read_indexed_timeline_logs,
    search_indexed_timeline_logs,
)

PARTICIPANTS = {
    "01J_USER_1": "Dohyeong",
    "01J_USER_2": "Partner",
}


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def make_writer(storage_root: Path) -> DuriStorageWriter:
    return DuriStorageWriter(
        storage_root=storage_root,
        participants=PARTICIPANTS,
        app_timezone="Asia/Seoul",
    )


def test_index_returns_full_timeline_logs_with_filters(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    writer = make_writer(storage_root)
    writer.append_message(
        log_id="01J_MSG_JULY",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_JULY",
        text="7월 메시지",
    )
    writer.append_photo(
        log_id="01J_PHOTO_JULY",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"indexed photo",
        original_filename="indexed.jpg",
        mime_type="image/jpeg",
    )
    writer.append_message(
        log_id="01J_MSG_AUGUST",
        actor_id="01J_USER_2",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_AUGUST",
        text="8월 메시지",
    )

    db_path = tmp_path / "indexes" / "timeline.sqlite3"
    rebuild_timeline_index(storage_root, db_path)

    indexed = read_indexed_timeline_logs(db_path, period="2026-07", log_type="Message")

    assert [item["id"] for item in indexed] == ["01J_MSG_JULY"]
    assert indexed[0]["payload"]["text"] == "7월 메시지"
    assert indexed[0]["actor_display_name"] == "Dohyeong"
    assert indexed[0]["period"] == "2026-07"


def test_index_search_matches_filesystem_search_after_rebuild(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    writer = make_writer(storage_root)
    writer.append_message(
        log_id="01J_MSG_MATCH",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_MATCH",
        text="파스타 먹자",
    )
    writer.append_photo(
        log_id="01J_PHOTO_MATCH",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:22+09:00"),
        photo_bytes=b"pasta photo",
        original_filename="pasta.jpg",
        mime_type="image/jpeg",
    )
    writer.append_message(
        log_id="01J_MSG_OTHER_PERIOD",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_OTHER_PERIOD",
        text="파스타 또 먹자",
    )
    db_path = tmp_path / "indexes" / "timeline.sqlite3"

    rebuild_timeline_index(storage_root, db_path)
    first_results = search_indexed_timeline_logs(
        db_path,
        "파스타",
        period="2026-07",
        log_type="Message",
    )
    db_path.unlink()
    rebuild_timeline_index(storage_root, db_path)

    filesystem_results = search_timeline_logs(
        storage_root,
        "파스타",
        period="2026-07",
        log_type="Message",
    )
    rebuilt_results = search_indexed_timeline_logs(
        db_path,
        "파스타",
        period="2026-07",
        log_type="Message",
    )

    assert [item["id"] for item in first_results] == ["01J_MSG_MATCH"]
    assert rebuilt_results == first_results
    assert rebuilt_results == filesystem_results
