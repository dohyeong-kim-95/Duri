from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from duri_api.timeline import read_timeline_logs, timeline_search_text

JsonObject = dict[str, Any]

logger = logging.getLogger(__name__)


def rebuild_timeline_index(storage_root: Path, db_path: Path) -> None:
    """Rebuild the SQLite timeline index from DuriStorage.

    The index is built in a temp file and swapped in with os.replace, so a failed
    rebuild leaves the previous index untouched. Duplicate log ids in canonical data
    are tolerated: the first one is kept and a warning is logged.

    Args:
        storage_root: DuriStorage root directory.
        db_path: Path of the SQLite index file.

    Returns:
        None.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logs = read_timeline_logs(storage_root)
    temp_path = db_path.with_name(f"{db_path.name}.rebuild.tmp")
    temp_path.unlink(missing_ok=True)

    try:
        _write_index(temp_path, logs)
        os.replace(temp_path, db_path)
    finally:
        temp_path.unlink(missing_ok=True)


def _write_index(db_path: Path, logs: list[JsonObject]) -> None:
    """Create the timeline table in a fresh SQLite file and insert all Logs.

    Args:
        db_path: Path of a new, empty SQLite file.
        logs: Timeline Logs read from DuriStorage.

    Returns:
        None.
    """
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE timeline (
              log_id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              created_at TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              actor_display_name TEXT NOT NULL,
              period TEXT NOT NULL,
              search_text TEXT NOT NULL,
              log_json TEXT NOT NULL
            )
            """
        )
        for log in logs:
            log_id = str(log.get("id", ""))
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO timeline (
                  log_id,
                  type,
                  created_at,
                  actor_id,
                  actor_display_name,
                  period,
                  search_text,
                  log_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    str(log.get("type", "")),
                    str(log.get("created_at", "")),
                    str(log.get("actor_id", "")),
                    str(log.get("actor_display_name", "")),
                    str(log.get("period", "")),
                    timeline_search_text(log),
                    json.dumps(log, ensure_ascii=False, sort_keys=True),
                ),
            )
            if cursor.rowcount == 0:
                logger.warning(
                    "duplicate log id %s in period %s; keeping the first one in the index",
                    log_id,
                    log.get("period"),
                )
        connection.commit()
    finally:
        connection.close()


def query_timeline_index(db_path: Path) -> list[JsonObject]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT log_id, type, created_at, actor_id, period
            FROM timeline
            ORDER BY created_at, log_id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def read_indexed_timeline_logs(
    db_path: Path,
    *,
    period: str | None = None,
    log_type: str | None = None,
) -> list[JsonObject]:
    rows = _select_index_rows(db_path, period=period, log_type=log_type)
    return [_load_log_json(row["log_json"]) for row in rows]


def search_indexed_timeline_logs(
    db_path: Path,
    query: str,
    *,
    period: str | None = None,
    log_type: str | None = None,
) -> list[JsonObject]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    rows = _select_index_rows(db_path, period=period, log_type=log_type)
    return [
        _load_log_json(row["log_json"])
        for row in rows
        if normalized_query in str(row["search_text"]).casefold()
    ]


def _select_index_rows(
    db_path: Path,
    *,
    period: str | None,
    log_type: str | None,
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[str] = []
    period_filter = _clean_filter(period)
    type_filter = _clean_filter(log_type)

    if period_filter is not None:
        clauses.append("period = ?")
        params.append(period_filter)
    if type_filter is not None:
        clauses.append("LOWER(type) = LOWER(?)")
        params.append(type_filter)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect(db_path) as connection:
        return connection.execute(
            f"""
            SELECT log_json, search_text
            FROM timeline
            {where}
            ORDER BY created_at, log_id
            """,
            params,
        ).fetchall()


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _load_log_json(value: str) -> JsonObject:
    loaded = json.loads(value)
    if isinstance(loaded, dict):
        return loaded
    return {}


def _clean_filter(value: str | None) -> str | None:
    cleaned = value.strip() if value is not None else ""
    return cleaned or None
