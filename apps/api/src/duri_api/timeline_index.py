from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from duri_api.timeline import read_timeline_logs, timeline_search_text

JsonObject = dict[str, Any]


def rebuild_timeline_index(storage_root: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logs = read_timeline_logs(storage_root)

    with sqlite3.connect(db_path) as connection:
        connection.execute("DROP TABLE IF EXISTS timeline")
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
        connection.executemany(
            """
            INSERT INTO timeline (
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
            [
                (
                    str(log.get("id", "")),
                    str(log.get("type", "")),
                    str(log.get("created_at", "")),
                    str(log.get("actor_id", "")),
                    str(log.get("actor_display_name", "")),
                    str(log.get("period", "")),
                    timeline_search_text(log),
                    json.dumps(log, ensure_ascii=False, sort_keys=True),
                )
                for log in logs
            ],
        )
        connection.commit()


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
