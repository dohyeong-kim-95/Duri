from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]


def read_timeline_logs(
    storage_root: Path | None,
    *,
    period: str | None = None,
    log_type: str | None = None,
) -> list[JsonObject]:
    if storage_root is None:
        return []

    period_filter = _clean_filter(period)
    type_filter = _clean_filter(log_type)
    logs: list[JsonObject] = []
    for metadata in _read_metadata_files(storage_root):
        participants = metadata.get("participants", {})
        period = metadata.get("period")
        for log in metadata.get("logs", []):
            if not isinstance(log, dict):
                continue

            item = dict(log)
            item["period"] = period
            item["actor_display_name"] = _display_name(
                participants=participants,
                actor_id=cast(str, item.get("actor_id", "")),
            )
            if not _matches_filters(item, period=period_filter, log_type=type_filter):
                continue
            logs.append(item)

    return _sorted_logs(logs)


def search_timeline_logs(
    storage_root: Path | None,
    query: str,
    *,
    period: str | None = None,
    log_type: str | None = None,
) -> list[JsonObject]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    return [
        log
        for log in read_timeline_logs(storage_root, period=period, log_type=log_type)
        if normalized_query in timeline_search_text(log).casefold()
    ]


def _read_metadata_files(storage_root: Path) -> list[JsonObject]:
    if not storage_root.exists():
        return []

    metadata_files = sorted(storage_root.glob("timeline/*/*/metadata.json"))
    metadata: list[JsonObject] = []
    for metadata_path in metadata_files:
        loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            metadata.append(cast(JsonObject, loaded))
    return metadata


def _display_name(*, participants: Any, actor_id: str) -> str:
    if isinstance(participants, dict):
        participant = participants.get(actor_id)
        if isinstance(participant, dict):
            display_name = participant.get("display_name")
            if isinstance(display_name, str):
                return display_name
    return actor_id


def _clean_filter(value: str | None) -> str | None:
    cleaned = value.strip() if value is not None else ""
    return cleaned or None


def _matches_filters(
    log: JsonObject,
    *,
    period: str | None,
    log_type: str | None,
) -> bool:
    if period is not None and log.get("period") != period:
        return False
    if log_type is not None and str(log.get("type", "")).casefold() != log_type.casefold():
        return False
    return True


def _sorted_logs(logs: list[JsonObject]) -> list[JsonObject]:
    return sorted(logs, key=lambda log: (_sort_datetime(log), str(log.get("id", ""))))


def _sort_datetime(log: JsonObject) -> datetime:
    value = log.get("created_at")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.min


def timeline_search_text(log: JsonObject) -> str:
    searchable = {
        "id": log.get("id"),
        "type": log.get("type"),
        "created_at": log.get("created_at"),
        "actor_id": log.get("actor_id"),
        "actor_display_name": log.get("actor_display_name"),
        "payload": log.get("payload"),
        "metadata": log.get("metadata"),
        "media_refs": log.get("media_refs"),
    }
    return json.dumps(searchable, ensure_ascii=False, sort_keys=True)
