from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from duri_api import timeline_index as _timeline_index

JsonObject = dict[str, Any]
PathHook = Callable[[Path, Path], None]
MessagesHook = Callable[[Path], None]

SCHEMA_VERSION = 1


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

        self._append_log(period, log)
        return log

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
        lock = self._lock_for(period)

        with lock:
            partition = self._partition_path(period)
            photos_dir = partition / "photos"
            photos_dir.mkdir(parents=True, exist_ok=True)

            final_path = photos_dir / self._photo_filename(
                log_id=log_id,
                created_at=created_at,
                original_filename=original_filename,
                mime_type=mime_type,
            )
            temp_path = partition / f".{final_path.name}.tmp"

            try:
                _write_bytes_durable(temp_path, photo_bytes)
                if self.hooks.before_media_rename is not None:
                    self.hooks.before_media_rename(temp_path, final_path)
                _verify_file_matches_bytes(temp_path, photo_bytes)
                os.replace(temp_path, final_path)
                _fsync_directory(photos_dir)
            except Exception as exc:
                temp_path.unlink(missing_ok=True)
                raise StorageWriteError("photo write failed before atomic rename") from exc

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

            self._append_log_locked(period, log)
            result = dict(log)
            result["media_ref"] = media_ref
            return result

    def regenerate_messages(self, period: str) -> str:
        partition = self._partition_path(period)
        metadata = self._read_metadata(period)
        content = _render_messages_markdown(metadata)
        messages_path = partition / "messages.md"
        self._write_messages(messages_path, content)
        return content

    def recover_orphan_media(self, period: str) -> list[JsonObject]:
        lock = self._lock_for(period)
        with lock:
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
            recovered: list[JsonObject] = []

            for media_path in sorted(path for path in photos_dir.iterdir() if path.is_file()):
                if media_path.name.startswith(".") or media_path.suffix == ".tmp":
                    continue

                relative_path = _relative_to_root(self.storage_root, media_path)
                if relative_path in referenced:
                    continue

                media_ref = self._media_ref(
                    log_id=_recovered_log_id(media_path),
                    media_path=media_path,
                    original_filename=media_path.name,
                    mime_type=(
                        mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
                    ),
                )
                log = self._base_log(
                    log_id=media_ref["log_id"],
                    log_type="Photo",
                    actor_id="system",
                    source="recovery_scan",
                    created_at=self._period_start(period),
                    ingested_at=datetime.now(tz=self._timezone),
                )
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

            if recovered:
                self._write_metadata(period, metadata)
                self._write_messages(partition / "messages.md", _render_messages_markdown(metadata))

            return recovered

    def _append_log(self, period: str, log: JsonObject) -> None:
        lock = self._lock_for(period)
        with lock:
            self._append_log_locked(period, log)

    def _append_log_locked(self, period: str, log: JsonObject) -> None:
        metadata = self._read_metadata(period)
        metadata["logs"].append(log)
        metadata["logs"] = _sorted_logs(metadata["logs"])
        self._write_metadata(period, metadata)
        self._write_messages(
            self._partition_path(period) / "messages.md",
            _render_messages_markdown(metadata),
        )

    def _read_metadata(self, period: str) -> JsonObject:
        metadata_path = self._metadata_path(period)
        if metadata_path.exists():
            metadata = cast(JsonObject, json.loads(metadata_path.read_text(encoding="utf-8")))
            metadata.setdefault("participants", self._participants_payload())
            metadata.setdefault("logs", [])
            return metadata

        return {
            "schema_version": SCHEMA_VERSION,
            "period": period,
            "timezone": self.app_timezone,
            "participants": self._participants_payload(),
            "logs": [],
        }

    def _write_metadata(self, period: str, metadata: JsonObject) -> None:
        partition = self._partition_path(period)
        partition.mkdir(parents=True, exist_ok=True)
        (partition / "photos").mkdir(exist_ok=True)
        metadata_path = self._metadata_path(period)
        temp_path = partition / "metadata.json.tmp"
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
        try:
            if self.hooks.before_messages_write is not None:
                self.hooks.before_messages_write(messages_path)
            _write_text_durable(messages_path, content)
            _fsync_directory(messages_path.parent)
        except Exception as exc:
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


def _sorted_logs(logs: list[JsonObject]) -> list[JsonObject]:
    return sorted(logs, key=lambda log: (log["created_at"], log["id"]))


def _as_app_datetime(value: datetime, timezone: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone)
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


def _recovered_log_id(media_path: Path) -> str:
    digest = hashlib.sha256(media_path.read_bytes()).hexdigest()[:26].upper()
    return f"RECOVERED_{digest}"


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
