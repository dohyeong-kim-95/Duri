"""Regression tests for the medium/low code review findings (M*, L*)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from duri_api.storage import DuriStorageWriter
from duri_api.timeline import read_timeline_logs, read_timeline_summary, search_timeline_logs

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
