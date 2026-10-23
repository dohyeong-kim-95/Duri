from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import mimetypes
import os
import re
import secrets
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from duri_api import timeline_index as _timeline_index
from duri_api.timeline import (
    EARLIEST_AWARE_DATETIME,
    SUPPORTED_SCHEMA_VERSIONS,
    is_supported_schema_version,
)

JsonObject = dict[str, Any]
PathHook = Callable[[Path, Path], None]
MessagesHook = Callable[[Path], None]

SCHEMA_VERSION = 1
MAX_PHOTO_NAME_ATTEMPTS = 100
PARTITION_LOCK_FILENAME = ".write.lock"

logger = logging.getLogger(__name__)


class StorageWriteError(RuntimeError):
    """Raised when a write fails after preserving canonical storage guarantees."""


@dataclass(frozen=True, slots=True)
class StorageWriteHooks:
    before_media_rename: PathHook | None = None
    after_metadata_tmp_write: PathHook | None = None
    before_messages_write: MessagesHook | None = None


class DuriStorageWriter:
    _locks_guard = threading.Lock()
    _partition_locks: dict[str, threading.Lock] = {}

    def __init__(
        self,
        *,
        storage_root: Path,
        participants: Mapping[str, str],
        app_timezone: str,
        hooks: StorageWriteHooks | None = None,
    ) -> None:
        self.storage_root = storage_root
        self.participants = dict(participants)
        self.app_timezone = app_timezone
        self._timezone = ZoneInfo(app_timezone)
        self.hooks = hooks or StorageWriteHooks()

    def append_message(
        self,
        *,
        log_id: str,
        actor_id: str,
        created_at: datetime,
        message_id: str,
        text: str,
        thread_id: str = "default",
        ingested_at: datetime | None = None,
    ) -> JsonObject:
        period = self._period_for(created_at)
        log = self._base_log(
            log_id=log_id,
            log_type="Message",
            actor_id=actor_id,
            source="chat",
            created_at=created_at,
            ingested_at=ingested_at,
        )
        log["payload"] = {
            "message_id": message_id,
            "text": text,
            "thread_id": thread_id,
        }
        log["metadata"] = {}
        log["media_refs"] = []

        return self._append_log(period, log)

    def append_photo(
        self,
        *,
        log_id: str,
        actor_id: str,
        created_at: datetime,
        photo_bytes: bytes,
        original_filename: str,
        mime_type: str,
        captured_at: datetime | None = None,
        exif: JsonObject | None = None,
        ingested_at: datetime | None = None,
    ) -> JsonObject:
        period = self._period_for(created_at)

        with self._partition_lock(period):
            existing_log = _find_log_by_id(self._read_metadata_for_append(period)["logs"], log_id)
            if existing_log is not None:
                # Photo retries may carry re-encoded bytes, so only type/actor are compared.
                retry_log = {"id": log_id, "type": "Photo", "actor_id": actor_id}
                _raise_if_different_log(existing_log, retry_log)
                logger.warning(
                    "log %s already exists in %s; returning existing log", log_id, period
                )
                return _photo_result(existing_log)

            partition = self._partition_path(period)
            photos_dir = partition / "photos"
            photos_dir.mkdir(parents=True, exist_ok=True)

            filename = self._photo_filename(
                log_id=log_id,
                created_at=created_at,
                original_filename=original_filename,
                mime_type=mime_type,
            )
            final_path = self._write_photo_file(partition, photos_dir, filename, photo_bytes)

            media_ref = self._media_ref(
                log_id=log_id,
                media_path=final_path,
                original_filename=original_filename,
                mime_type=mime_type,
            )
            log = self._base_log(
                log_id=log_id,
                log_type="Photo",
                actor_id=actor_id,
                source="photo_upload",
                created_at=created_at,
                ingested_at=ingested_at,
            )
            log["payload"] = {
                "media_ref_id": media_ref["id"],
                "caption": None,
            }
            log["metadata"] = {
                "captured_at": _isoformat(captured_at) if captured_at is not None else None,
                "gps": None,
                "exif": exif or {},
                "width": None,
                "height": None,
                "size_bytes": media_ref["size_bytes"],
                "sha256": media_ref["sha256"],
            }
            log["media_refs"] = [media_ref]

            stored_log = self._append_log_locked(period, log)
            return _photo_result(stored_log)

    def _write_photo_file(
        self,
        partition: Path,
        photos_dir: Path,
        filename: str,
        photo_bytes: bytes,
    ) -> Path:
        """Store photo bytes in photos/ without ever overwriting an existing original.

        The bytes go to a temp file (unique per process and call), are fsynced and
        verified, and are then published with os.link. os.link fails with
        FileExistsError if another process created the name first, so the check and
        the publish are one atomic step across processes. On that error the name is
        picked again (same sha256 → reuse, different → "_2", "_3", ...).

        Args:
            partition: Month partition directory (temp file lives here).
            photos_dir: The partition's photos/ directory.
            filename: Preferred filename from _photo_filename.
            photo_bytes: Original uploaded bytes.

        Returns:
            Path of the stored photo (new, or an existing file with the same bytes).
            Raises StorageWriteError if anything fails before the file is published.
        """
        unique_suffix = f"{os.getpid()}.{secrets.token_hex(4)}"
        temp_path = partition / f".{filename}.{unique_suffix}.tmp"
        try:
            _write_bytes_durable(temp_path, photo_bytes)
            if self.hooks.before_media_rename is not None:
                self.hooks.before_media_rename(temp_path, photos_dir / filename)
            _verify_file_matches_bytes(temp_path, photo_bytes)

            for _attempt in range(MAX_PHOTO_NAME_ATTEMPTS):
                final_path, already_stored = _available_photo_path(
                    photos_dir, filename, photo_bytes
                )
                if already_stored:
                    return final_path
                try:
                    os.link(temp_path, final_path)
                except FileExistsError:
                    # Another writer took this name between the check and the link.
                    continue
                _fsync_directory(photos_dir)
                return final_path
            raise StorageWriteError(f"no free photo filename for {filename}")
        except Exception as exc:
            raise StorageWriteError("photo write failed before atomic publish") from exc
        finally:
            temp_path.unlink(missing_ok=True)

    def regenerate_messages(self, period: str) -> str:
        partition = self._partition_path(period)
        metadata = self._read_metadata(period)
        content = _render_messages_markdown(metadata)
        messages_path = partition / "messages.md"
        self._write_messages(messages_path, content)
        return content

    def recover_orphan_media(self, period: str) -> list[JsonObject]:
        with self._partition_lock(period):
            metadata = self._read_metadata(period)
            partition = self._partition_path(period)
            photos_dir = partition / "photos"
            if not photos_dir.exists():
                return []

            referenced = {
                media_ref["storage_path"]
                for log in metadata["logs"]
                for media_ref in log.get("media_refs", [])
            }
            existing_ids = {log.get("id") for log in metadata["logs"]}
            partition_timezone = _zone_or_default(metadata.get("timezone"), self._timezone)
            recovered: list[JsonObject] = []

            for media_path in sorted(path for path in photos_dir.iterdir() if path.is_file()):
                if media_path.name.startswith(".") or media_path.suffix == ".tmp":
                    continue

                relative_path = _relative_to_root(self.storage_root, media_path)
                if relative_path in referenced:
                    continue

                # Prefer the original created_at and log_id from the writer's own
                # filename; fall back to a path-based id and the period start.
                # The filename time was written in the partition's timezone, which
                # may differ from the current app timezone.
                log_id = _recovered_log_id(relative_path)
                created_at = self._period_start(period)
                parsed = _parse_writer_photo_filename(media_path.name, partition_timezone)
                if parsed is not None:
                    parsed_log_id, parsed_created_at = parsed
                    parsed_period = parsed_created_at.strftime("%Y-%m")
                    if parsed_period == period:
                        # Keep the real time even when the id is already taken.
                        created_at = parsed_created_at
                        if parsed_log_id not in existing_ids:
                            log_id = parsed_log_id

                media_ref = self._media_ref(
                    log_id=log_id,
                    media_path=media_path,
                    original_filename=media_path.name,
                    mime_type=(
                        mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
                    ),
                )
                log = self._base_log(
                    log_id=log_id,
                    log_type="Photo",
                    actor_id="system",
                    source="recovery_scan",
                    created_at=created_at,
                    ingested_at=datetime.now(tz=self._timezone),
                )
                # Keep the partition's own offset so the file stays in one timezone.
                log["created_at"] = _isoformat(created_at.astimezone(partition_timezone))
                log["payload"] = {
                    "media_ref_id": media_ref["id"],
                    "caption": None,
                }
                log["metadata"] = {
                    "captured_at": None,
                    "gps": None,
                    "exif": {},
                    "width": None,
                    "height": None,
                    "size_bytes": media_ref["size_bytes"],
                    "sha256": media_ref["sha256"],
                }
                log["media_refs"] = [media_ref]
                metadata["logs"].append(log)
                recovered.append(log)
                referenced.add(relative_path)
                existing_ids.add(log_id)

            if recovered:
                self._write_metadata(period, metadata)
                self._write_messages_after_commit(period, metadata)

            return recovered

    def _append_log(self, period: str, log: JsonObject) -> JsonObject:
        with self._partition_lock(period):
            return self._append_log_locked(period, log)

    @contextmanager
    def _partition_lock(self, period: str) -> Iterator[None]:
        """Serialize writes to one month partition across threads and processes.

        The threading.Lock covers threads of this process; an exclusive fcntl.flock
        on "<partition>/.write.lock" covers other processes (e.g. several uvicorn
        workers) on the same Linux host.

        Args:
            period: Month partition such as "2026-07".

        Returns:
            A context manager that holds both locks while the block runs.
        """
        partition = self._partition_path(period)
        partition.mkdir(parents=True, exist_ok=True)
        with self._lock_for(period):
            with (partition / PARTITION_LOCK_FILENAME).open("a") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _append_log_locked(self, period: str, log: JsonObject) -> JsonObject:
        """Append a Log to the period's metadata.json, idempotently.

        Args:
            period: Month partition such as "2026-07".
            log: The new Log to append.

        Returns:
            The stored Log. If a Log with the same id and the same content already
            exists, that existing Log is returned and nothing is written. If the
            content differs, StorageWriteError is raised and nothing is written.
        """
        metadata = self._read_metadata_for_append(period)
        existing_log = _find_log_by_id(metadata["logs"], log["id"])
        if existing_log is not None:
            _raise_if_different_log(existing_log, log)
            logger.warning("log %s already exists in %s; returning existing log", log["id"], period)
            return existing_log

        metadata["logs"].append(log)
        metadata["logs"] = _sorted_logs(metadata["logs"])
        self._write_metadata(period, metadata)

        self._write_messages_after_commit(period, metadata)
        return log

    def _write_messages_after_commit(self, period: str, metadata: JsonObject) -> None:
        """Regenerate messages.md after metadata.json has been committed.

        messages.md is a derived view, so any failure here (rendering or writing)
        is logged and swallowed: the write already succeeded (RFC 0001 §10).

        Args:
            period: Month partition such as "2026-07".
            metadata: The metadata that was just committed.

        Returns:
            None.
        """
        try:
            self._write_messages(
                self._partition_path(period) / "messages.md",
                _render_messages_markdown(metadata),
            )
        except Exception:
            logger.warning(
                "messages.md regeneration failed for %s; metadata.json is committed",
                period,
                exc_info=True,
            )

    def _read_metadata(self, period: str) -> JsonObject:
        metadata_path = self._metadata_path(period)
        if metadata_path.exists():
            metadata = cast(JsonObject, json.loads(metadata_path.read_text(encoding="utf-8")))
            # Refuse to modify files that are not RFC 0001 v1 metadata (e.g. the
            # Bubblelab sink format, or a future version). See docs/rfc/0002 (Draft).
            schema_version = metadata.get("schema_version")
            if not is_supported_schema_version(schema_version):
                raise StorageWriteError(
                    f"{metadata_path} has schema_version {schema_version!r}, supported: "
                    f"{SUPPORTED_SCHEMA_VERSIONS}; refusing to write (see docs/rfc/0002)"
                )
            # Fill participants when missing or empty (e.g. a partition first written
            # by the recovery CLI before any participants were known).
            if not metadata.get("participants"):
                metadata["participants"] = self._participants_payload()
            metadata.setdefault("logs", [])
            return metadata

        return {
            "schema_version": SCHEMA_VERSION,
            "period": period,
            "timezone": self.app_timezone,
            "participants": self._participants_payload(),
            "logs": [],
        }

    def _read_metadata_for_append(self, period: str) -> JsonObject:
        """Read metadata.json for a new Log, refusing a partition in another timezone.

        A partition written in one timezone and appended in another would mix
        offsets in created_at/messages.md and make its "timezone" field untrue.

        Args:
            period: Month partition such as "2026-07".

        Returns:
            The partition metadata. Raises StorageWriteError on a timezone mismatch.
        """
        metadata = self._read_metadata(period)
        partition_timezone = metadata.get("timezone")
        if partition_timezone is not None and partition_timezone != self.app_timezone:
            raise StorageWriteError(
                f"partition {period} is in timezone {partition_timezone!r} but the writer "
                f"uses {self.app_timezone!r}; refusing to mix timezones in one partition"
            )
        return metadata

    def _write_metadata(self, period: str, metadata: JsonObject) -> None:
        partition = self._partition_path(period)
        partition.mkdir(parents=True, exist_ok=True)
        (partition / "photos").mkdir(exist_ok=True)
        metadata_path = self._metadata_path(period)
        temp_path = partition / f"metadata.json.{os.getpid()}.{secrets.token_hex(4)}.tmp"
        payload = json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)

        try:
            _write_text_durable(temp_path, f"{payload}\n")
            if self.hooks.after_metadata_tmp_write is not None:
                self.hooks.after_metadata_tmp_write(temp_path, metadata_path)
            os.replace(temp_path, metadata_path)
            _fsync_directory(partition)
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise StorageWriteError("metadata write failed before atomic rename") from exc

        json.loads(metadata_path.read_text(encoding="utf-8"))

    def _write_messages(self, messages_path: Path, content: str) -> None:
        """Write messages.md via temp file + rename, so a crash never leaves it cut off.

        Args:
            messages_path: Destination messages.md path.
            content: Rendered Markdown.

        Returns:
            None. Raises StorageWriteError on failure (the old file stays as it was).
        """
        unique_suffix = f"{os.getpid()}.{secrets.token_hex(4)}"
        temp_path = messages_path.with_name(f".{messages_path.name}.{unique_suffix}.tmp")
        try:
            if self.hooks.before_messages_write is not None:
                self.hooks.before_messages_write(messages_path)
            _write_text_durable(temp_path, content)
            os.replace(temp_path, messages_path)
            _fsync_directory(messages_path.parent)
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise StorageWriteError("messages.md regeneration failed") from exc

    def _base_log(
        self,
        *,
        log_id: str,
        log_type: str,
        actor_id: str,
        source: str,
        created_at: datetime,
        ingested_at: datetime | None,
    ) -> JsonObject:
        ingested = ingested_at or datetime.now(tz=self._timezone)
        return {
            "id": log_id,
            "type": log_type,
            "created_at": _isoformat(_as_app_datetime(created_at, self._timezone)),
            "ingested_at": _isoformat(_as_app_datetime(ingested, self._timezone)),
            "actor_id": actor_id,
            "source": source,
        }

    def _media_ref(
        self,
        *,
        log_id: str,
        media_path: Path,
        original_filename: str,
        mime_type: str,
    ) -> JsonObject:
        media_bytes = media_path.read_bytes()
        return {
            "id": f"{log_id}_MEDIA",
            "log_id": log_id,
            "original_filename": original_filename,
            "mime_type": mime_type,
            "storage_path": _relative_to_root(self.storage_root, media_path),
            "size_bytes": len(media_bytes),
            "sha256": hashlib.sha256(media_bytes).hexdigest(),
            "created_at": _isoformat(datetime.now(tz=self._timezone)),
        }

    def _partition_path(self, period: str) -> Path:
        validate_period(period)
        return self.storage_root / "timeline" / period[:4] / period

    def _metadata_path(self, period: str) -> Path:
        return self._partition_path(period) / "metadata.json"

    def _period_for(self, created_at: datetime) -> str:
        return _as_app_datetime(created_at, self._timezone).strftime("%Y-%m")

    def _period_start(self, period: str) -> datetime:
        year, month = (int(part) for part in period.split("-", 1))
        return datetime(year, month, 1, 0, 0, 0, tzinfo=self._timezone)

    def _photo_filename(
        self,
        *,
        log_id: str,
        created_at: datetime,
        original_filename: str,
        mime_type: str,
    ) -> str:
        timestamp = _as_app_datetime(created_at, self._timezone).strftime("%Y-%m-%dT%H-%M-%S")
        extension = _safe_extension(original_filename, mime_type)
        safe_log_id = re.sub(r"[^A-Za-z0-9_-]", "_", log_id)
        return f"{timestamp}_{safe_log_id}{extension}"

    def _participants_payload(self) -> JsonObject:
        return {
            actor_id: {"display_name": display_name}
            for actor_id, display_name in self.participants.items()
        }

    @classmethod
    def _lock_for(cls, partition_key: str) -> threading.Lock:
        with cls._locks_guard:
            if partition_key not in cls._partition_locks:
                cls._partition_locks[partition_key] = threading.Lock()
            return cls._partition_locks[partition_key]


PERIOD_PATTERN = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def validate_period(period: str) -> None:
    """Make sure a period is a plain "YYYY-MM" before it becomes part of a path.

    Args:
        period: Month partition such as "2026-07".

    Returns:
        None. Raises ValueError for anything else (e.g. "../x", "2026-13").
    """
    if not isinstance(period, str) or PERIOD_PATTERN.fullmatch(period) is None:
        raise ValueError(f"invalid period {period!r}; expected YYYY-MM")


def rebuild_timeline_index(storage_root: Path, db_path: Path) -> None:
    _timeline_index.rebuild_timeline_index(storage_root, db_path)


def query_timeline_index(db_path: Path) -> list[JsonObject]:
    return _timeline_index.query_timeline_index(db_path)


def _render_messages_markdown(metadata: JsonObject) -> str:
    period = metadata["period"]
    participants = metadata.get("participants", {})
    lines = [f"# {period} Messages", ""]
    current_day: str | None = None

    for log in _sorted_logs(metadata["logs"]):
        if log["type"] != "Message":
            continue

        created_at = datetime.fromisoformat(log["created_at"])
        day = created_at.date().isoformat()
        if day != current_day:
            if current_day is not None:
                lines.append("")
            lines.append(f"## {day}")
            lines.append("")
            current_day = day

        display_name = participants.get(log["actor_id"], {}).get("display_name", log["actor_id"])
        lines.append(f"{created_at.strftime('%H:%M')} — {display_name}")
        lines.append(f": {log['payload']['text']}")

    return "\n".join(lines).rstrip() + "\n"


def _find_log_by_id(logs: list[JsonObject], log_id: str) -> JsonObject | None:
    """Find a Log by id.

    Args:
        logs: Logs from metadata.json.
        log_id: The id to look for.

    Returns:
        The first Log with that id, or None if there is none.
    """
    for log in logs:
        if log.get("id") == log_id:
            return log
    return None


def _raise_if_different_log(existing_log: JsonObject, new_log: JsonObject) -> None:
    """Reject a write whose log_id is already used by a Log with different content.

    Compared fields: type and actor_id always; created_at and payload.text for
    Messages. A Log made by the recovery scan has actor "system", so actor_id is
    not compared against it (the client retry is the same upload).

    Args:
        existing_log: The Log already stored under this id.
        new_log: The Log (or for photos, its id/type/actor_id) being written.

    Returns:
        None when the content matches. Raises StorageWriteError otherwise.
    """
    different_fields: list[str] = []
    if existing_log.get("type") != new_log.get("type"):
        different_fields.append("type")

    is_recovered = existing_log.get("source") == "recovery_scan"
    if not is_recovered and existing_log.get("actor_id") != new_log.get("actor_id"):
        different_fields.append("actor_id")

    if new_log.get("type") == "Message":
        existing_time = _parse_optional_datetime(existing_log.get("created_at"))
        new_time = _parse_optional_datetime(new_log.get("created_at"))
        if existing_time != new_time:
            different_fields.append("created_at")
        if _payload_text(existing_log) != _payload_text(new_log):
            different_fields.append("payload.text")

    if not different_fields:
        return
    raise StorageWriteError(
        f"log id {new_log.get('id')} already exists with different content "
        f"({', '.join(different_fields)})"
    )


def _parse_optional_datetime(value: object) -> datetime | None:
    """Parse an ISO datetime string, or return None if it is missing or invalid.

    Args:
        value: Raw created_at value from a Log.

    Returns:
        The parsed datetime, or None.
    """
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _payload_text(log: JsonObject) -> object:
    """Return payload.text of a Log, or None if there is none.

    Args:
        log: A Log.

    Returns:
        The text value, or None.
    """
    payload = log.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload.get("text")


def _photo_result(log: JsonObject) -> JsonObject:
    """Build the append_photo return value: the Log plus its first MediaRef.

    Args:
        log: A stored Photo Log.

    Returns:
        A copy of the Log with a "media_ref" key added.
    """
    result = dict(log)
    media_refs = log.get("media_refs") or []
    result["media_ref"] = media_refs[0] if media_refs else None
    return result


def _sorted_logs(logs: list[JsonObject]) -> list[JsonObject]:
    return sorted(logs, key=_log_sort_key)


def _log_sort_key(log: JsonObject) -> tuple[datetime, str]:
    """Sort by the real instant of created_at, not by its text.

    Args:
        log: A Log (possibly hand-edited).

    Returns:
        (created_at, id). A missing/invalid created_at sorts first; a value
        without offset is read as UTC (same rule as the Timeline reader).
    """
    created_at = _parse_optional_datetime(log.get("created_at"))
    if created_at is None:
        created_at = EARLIEST_AWARE_DATETIME
    elif created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return created_at, str(log.get("id", ""))


def _as_app_datetime(value: datetime, timezone: ZoneInfo) -> datetime:
    """Convert an aware datetime to the app timezone.

    Args:
        value: Must carry a UTC offset. A naive value (e.g. datetime.utcnow()) is
            ambiguous and would be stored hours off, so it is rejected.
        timezone: App timezone.

    Returns:
        The same instant in the app timezone. Raises ValueError for naive input.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"datetime must be timezone-aware, got naive {value.isoformat()}")
    return value.astimezone(timezone)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def _safe_extension(original_filename: str, mime_type: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    if re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        return suffix

    guessed = mimetypes.guess_extension(mime_type)
    return guessed or ".bin"


def _relative_to_root(storage_root: Path, path: Path) -> str:
    return path.relative_to(storage_root).as_posix()


def _zone_or_default(timezone_name: object, default: ZoneInfo) -> ZoneInfo:
    """Build a ZoneInfo from a metadata.json "timezone" value.

    Args:
        timezone_name: The raw "timezone" value (may be missing or invalid).
        default: Zone to use when the value cannot be used.

    Returns:
        The partition's zone, or default.
    """
    if not isinstance(timezone_name, str) or not timezone_name:
        return default
    try:
        return ZoneInfo(timezone_name)
    except (ValueError, KeyError):
        logger.warning("unknown timezone %r in metadata.json; using %s", timezone_name, default)
        return default


def _recovered_log_id(relative_path: str) -> str:
    """Build a recovery Log id from the file's path, so two files never share an id.

    Args:
        relative_path: Photo path relative to the storage root.

    Returns:
        "RECOVERED_" followed by 26 hex chars of the path's sha256.
    """
    digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:26].upper()
    return f"RECOVERED_{digest}"


WRITER_PHOTO_FILENAME = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})_([A-Za-z0-9_-]+)\.[A-Za-z0-9]{1,8}$"
)


def _parse_writer_photo_filename(
    filename: str,
    timezone: ZoneInfo,
) -> tuple[str, datetime] | None:
    """Read log_id and created_at back out of a filename made by _photo_filename.

    Args:
        filename: e.g. "2026-07-25T21-10-00_01J_PHOTO.jpg".
        timezone: Timezone the timestamp was written in (the partition's).

    Returns:
        (log_id, created_at), or None if the name does not match the pattern.
        log_id is the sanitized form used in the filename.
    """
    match = WRITER_PHOTO_FILENAME.match(filename)
    if match is None:
        return None

    timestamp_text = match.group(1)
    log_id = match.group(2)
    try:
        naive_created_at = datetime.strptime(timestamp_text, "%Y-%m-%dT%H-%M-%S")
    except ValueError:
        return None
    return log_id, naive_created_at.replace(tzinfo=timezone)


def _available_photo_path(
    photos_dir: Path,
    filename: str,
    photo_bytes: bytes,
) -> tuple[Path, bool]:
    """Pick a photo path that never overwrites an existing original.

    If a file already exists at the path with the same sha256, it is reused
    (idempotent retry). If it holds different bytes, "_2", "_3", ... is added
    before the extension until a free or identical file is found.

    Args:
        photos_dir: The partition's photos/ directory.
        filename: The preferred filename from _photo_filename.
        photo_bytes: The bytes about to be stored.

    Returns:
        (path, already_stored). already_stored is True when the path already
        holds exactly these bytes and nothing needs to be written.
    """
    new_sha256 = hashlib.sha256(photo_bytes).hexdigest()
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = photos_dir / filename
    number = 1
    while candidate.exists():
        existing_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if existing_sha256 == new_sha256:
            return candidate, True
        number += 1
        candidate = photos_dir / f"{stem}_{number}{suffix}"
    return candidate, False


def _write_bytes_durable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        file.write(payload)
        file.flush()
        os.fsync(file.fileno())


def _verify_file_matches_bytes(path: Path, expected: bytes) -> None:
    actual = path.read_bytes()
    if len(actual) != len(expected):
        raise StorageWriteError("temp media size mismatch before atomic rename")

    if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
        raise StorageWriteError("temp media hash mismatch before atomic rename")


def _write_text_durable(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write(payload)
        file.flush()
        os.fsync(file.fileno())


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return

    try:
        os.fsync(fd)
    finally:
        os.close(fd)
