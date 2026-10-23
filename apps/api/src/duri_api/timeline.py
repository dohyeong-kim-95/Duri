from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]

logger = logging.getLogger(__name__)

EARLIEST_AWARE_DATETIME = datetime.min.replace(tzinfo=UTC)

# metadata.json schema versions this code can read and write (RFC 0001).
SUPPORTED_SCHEMA_VERSIONS = (1,)


def is_supported_schema_version(value: object) -> bool:
    """Check a metadata.json "schema_version" value.

    Args:
        value: The raw value (may be missing, a string, a future version, ...).

    Returns:
        True only for an int listed in SUPPORTED_SCHEMA_VERSIONS ("1", 2, true → False).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value in SUPPORTED_SCHEMA_VERSIONS


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


def read_timeline_summary(storage_root: Path | None) -> JsonObject:
    logs = read_timeline_logs(storage_root)
    type_totals: dict[str, int] = {}
    period_totals: dict[str, JsonObject] = {}

    for log in logs:
        log_type = str(log.get("type", ""))
        period = str(log.get("period", ""))
        if not log_type or not period:
            continue

        type_totals[log_type] = type_totals.get(log_type, 0) + 1
        period_summary = period_totals.setdefault(
            period,
            {"period": period, "total": 0, "types": {}},
        )
        period_summary["total"] = int(period_summary["total"]) + 1
        period_types = cast(dict[str, int], period_summary["types"])
        period_types[log_type] = period_types.get(log_type, 0) + 1

    return {
        "total": len(logs),
        "periods": [period_totals[period] for period in sorted(period_totals, reverse=True)],
        "types": dict(sorted(type_totals.items())),
    }


def _read_metadata_files(storage_root: Path) -> list[JsonObject]:
    if not storage_root.exists():
        return []

    metadata_files = sorted(storage_root.glob("timeline/*/*/metadata.json"))
    metadata: list[JsonObject] = []
    for metadata_path in metadata_files:
        # One broken (e.g. hand-edited) file must not take the whole Timeline down.
        try:
            loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.warning("skipping %s: unreadable metadata.json", metadata_path, exc_info=True)
            continue
        if not isinstance(loaded, dict):
            continue
        # Files without a supported schema_version (e.g. the Bubblelab sink's
        # {month, logs[seq, at]} format, or a future version) are not RFC 0001 v1
        # metadata. Skip them until the format decision in docs/rfc/0002 is made.
        if not is_supported_schema_version(loaded.get("schema_version")):
            logger.warning(
                "skipping %s: schema_version %r is not supported %s",
                metadata_path,
                loaded.get("schema_version"),
                SUPPORTED_SCHEMA_VERSIONS,
            )
            continue
        metadata.append(cast(JsonObject, loaded))
    return metadata


def resolve_storage_path(storage_root: Path, relative_path: str) -> Path | None:
    """Resolve a client-supplied path inside DuriStorage.

    Args:
        storage_root: DuriStorage root directory.
        relative_path: Path relative to the root, e.g. a MediaRef storage_path.

    Returns:
        The resolved path, or None if it is absolute or escapes the root
        (e.g. "../auth.sqlite3").
    """
    if not relative_path or Path(relative_path).is_absolute():
        return None
    root = storage_root.resolve()
    resolved = (root / relative_path).resolve()
    if not resolved.is_relative_to(root):
        return None
    return resolved


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
    """Sort key for a Log's created_at that never mixes naive and aware datetimes.

    Args:
        log: A Log (possibly hand-edited).

    Returns:
        The aware created_at. A missing or invalid value sorts first (aware
        datetime.min); a value without offset is read as UTC.
    """
    value = log.get("created_at")
    if not isinstance(value, str):
        return EARLIEST_AWARE_DATETIME
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return EARLIEST_AWARE_DATETIME
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


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
