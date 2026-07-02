from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]

MAX_USERS = 2
DEFAULT_REFRESH_TTL_SECONDS = 60 * 60 * 24 * 180


class AuthError(RuntimeError):
    """Raised when authentication or session state is invalid."""


@dataclass(frozen=True, slots=True)
class AuthIdentity:
    user_id: int
    device_id: int
    session_id: int

    def as_dict(self) -> JsonObject:
        return {
            "user_id": self.user_id,
            "device_id": self.device_id,
            "session_id": self.session_id,
        }


class AuthService:
    def __init__(
        self,
        *,
        db_path: Path,
        jwt_secret: str,
        access_ttl_seconds: int = 60 * 15,
        refresh_ttl_seconds: int = DEFAULT_REFRESH_TTL_SECONDS,
    ) -> None:
        if not jwt_secret:
            raise ValueError("jwt_secret is required")

        self.db_path = db_path
        self._jwt_secret = jwt_secret.encode("utf-8")
        self.access_ttl_seconds = access_ttl_seconds
        self.refresh_ttl_seconds = refresh_ttl_seconds
        self._initialize_schema()

    def create_invite_code(
        self,
        *,
        code: str,
        intended_slot: int,
        ttl_seconds: int | None = None,
    ) -> JsonObject:
        self._validate_slot(intended_slot)
        created_at = _now()
        expires_at = created_at + ttl_seconds if ttl_seconds is not None else None

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO invite_codes (
                  code_hash, intended_slot, created_at, expires_at, consumed_at, consumed_by_user_id
                )
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (
                    self._hash_secret(code),
                    intended_slot,
                    created_at,
                    expires_at,
                ),
            )
            connection.commit()

        return {
            "id": _last_insert_id(cursor),
            "intended_slot": intended_slot,
            "created_at": _unix_to_iso(created_at),
            "expires_at": _unix_to_iso(expires_at) if expires_at is not None else None,
        }

    def register_with_invite(
        self,
        *,
        code: str,
        display_name: str,
        device_label: str,
        device_fingerprint: str,
    ) -> JsonObject:
        now = _now()
        code_hash = self._hash_secret(code)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            invite = _one(
                connection.execute(
                    """
                    SELECT id, intended_slot, expires_at, consumed_at
                    FROM invite_codes
                    WHERE code_hash = ?
                    """,
                    (code_hash,),
                )
            )
            if invite is None:
                raise AuthError("invalid invite code")
            if invite["consumed_at"] is not None:
                raise AuthError("invite code already consumed")
            if invite["expires_at"] is not None and cast(float, invite["expires_at"]) <= now:
                raise AuthError("invite code expired")

            intended_slot = cast(int, invite["intended_slot"])
            self._assert_registration_slot_available(connection, intended_slot)

            user_cursor = connection.execute(
                """
                INSERT INTO users (slot, display_name, created_at, status)
                VALUES (?, ?, ?, 'active')
                """,
                (intended_slot, display_name, now),
            )
            user_id = _last_insert_id(user_cursor)
            device = self._create_device(
                connection,
                user_id=user_id,
                device_label=device_label,
                device_fingerprint=device_fingerprint,
                now=now,
            )
            session = self._create_session(
                connection,
                user_id=user_id,
                device_id=cast(int, device["id"]),
                now=now,
            )
            connection.execute(
                """
                UPDATE invite_codes
                SET consumed_at = ?, consumed_by_user_id = ?
                WHERE id = ?
                """,
                (now, user_id, invite["id"]),
            )
            connection.commit()

        user = {
            "id": user_id,
            "slot": intended_slot,
            "display_name": display_name,
            "created_at": _unix_to_iso(now),
            "status": "active",
        }
        return self._session_payload(user=user, device=device, session=session)

    def create_device_session(
        self,
        *,
        user_id: int,
        device_label: str,
        device_fingerprint: str,
    ) -> JsonObject:
        now = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            user = _one(
                connection.execute(
                    """
                    SELECT id, slot, display_name, created_at, status
                    FROM users
                    WHERE id = ? AND status = 'active'
                    """,
                    (user_id,),
                )
            )
            if user is None:
                raise AuthError("user not found")

            device = self._create_device(
                connection,
                user_id=user_id,
                device_label=device_label,
                device_fingerprint=device_fingerprint,
                now=now,
            )
            session = self._create_session(
                connection,
                user_id=user_id,
                device_id=cast(int, device["id"]),
                now=now,
            )
            connection.commit()

        return self._session_payload(user=dict(user), device=device, session=session)

    def issue_access_token(
        self,
        *,
        user_id: int,
        device_id: int,
        session_id: int,
        ttl_seconds: int | None = None,
    ) -> str:
        now = _now()
        ttl = self.access_ttl_seconds if ttl_seconds is None else ttl_seconds
        payload: JsonObject = {
            "typ": "access",
            "sub": user_id,
            "device_id": device_id,
            "session_id": session_id,
            "jti": secrets.token_urlsafe(16),
            "iat": now,
            "exp": now + ttl,
        }
        return self._encode_token(payload)

    def validate_access_token(self, token: str) -> AuthIdentity:
        payload = self._decode_token(token)
        if payload.get("typ") != "access":
            raise AuthError("invalid token type")
        if cast(float, payload.get("exp", 0)) <= _now():
            raise AuthError("access token expired")

        identity = AuthIdentity(
            user_id=int(cast(int | float, payload["sub"])),
            device_id=int(cast(int | float, payload["device_id"])),
            session_id=int(cast(int | float, payload["session_id"])),
        )
        self._assert_active_identity(identity)
        return identity

    def refresh_access_token(self, refresh_token: str) -> JsonObject:
        now = _now()
        refresh_token_hash = self._hash_secret(refresh_token)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = _one(
                connection.execute(
                    """
                    SELECT
                      sessions.id AS session_id,
                      sessions.user_id AS user_id,
                      sessions.device_id AS device_id,
                      sessions.expires_at AS expires_at,
                      sessions.revoked_at AS session_revoked_at,
                      users.status AS user_status,
                      devices.revoked_at AS device_revoked_at
                    FROM sessions
                    JOIN users ON users.id = sessions.user_id
                    JOIN devices ON devices.id = sessions.device_id
                    WHERE sessions.refresh_token_hash = ?
                    """,
                    (refresh_token_hash,),
                )
            )
            if row is None:
                raise AuthError("refresh session not found")
            if row["session_revoked_at"] is not None or row["device_revoked_at"] is not None:
                raise AuthError("refresh session revoked")
            if row["user_status"] != "active":
                raise AuthError("user inactive")
            if cast(float, row["expires_at"]) <= now:
                raise AuthError("refresh session expired")

            connection.execute(
                "UPDATE sessions SET last_used_at = ? WHERE id = ?",
                (now, row["session_id"]),
            )
            connection.commit()

        access_token = self.issue_access_token(
            user_id=cast(int, row["user_id"]),
            device_id=cast(int, row["device_id"]),
            session_id=cast(int, row["session_id"]),
        )
        return {"access_token": access_token}

    def revoke_device(self, device_id: int) -> None:
        now = _now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            device_exists = _one(
                connection.execute("SELECT id FROM devices WHERE id = ?", (device_id,))
            )
            if device_exists is None:
                raise AuthError("device not found")

            connection.execute(
                """
                UPDATE devices
                SET revoked_at = ?
                WHERE id = ? AND revoked_at IS NULL
                """,
                (now, device_id),
            )
            connection.execute(
                """
                UPDATE sessions
                SET revoked_at = ?
                WHERE device_id = ? AND revoked_at IS NULL
                """,
                (now, device_id),
            )
            connection.commit()

    def _session_payload(
        self,
        *,
        user: JsonObject,
        device: JsonObject,
        session: JsonObject,
    ) -> JsonObject:
        return {
            "user": user,
            "device": device,
            "session": session,
            "access_token": self.issue_access_token(
                user_id=cast(int, user["id"]),
                device_id=cast(int, device["id"]),
                session_id=cast(int, session["id"]),
            ),
            "refresh_token": cast(str, session["refresh_token"]),
        }

    def _initialize_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  slot INTEGER NOT NULL UNIQUE CHECK (slot IN (1, 2)),
                  display_name TEXT NOT NULL,
                  created_at REAL NOT NULL,
                  status TEXT NOT NULL CHECK (status IN ('active', 'disabled'))
                );

                CREATE TABLE IF NOT EXISTS invite_codes (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code_hash TEXT NOT NULL UNIQUE,
                  intended_slot INTEGER NOT NULL CHECK (intended_slot IN (1, 2)),
                  created_at REAL NOT NULL,
                  expires_at REAL,
                  consumed_at REAL,
                  consumed_by_user_id INTEGER REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS devices (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL REFERENCES users(id),
                  label TEXT NOT NULL,
                  fingerprint_hash TEXT NOT NULL,
                  created_at REAL NOT NULL,
                  last_seen_at REAL NOT NULL,
                  revoked_at REAL,
                  UNIQUE (user_id, fingerprint_hash)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL REFERENCES users(id),
                  device_id INTEGER NOT NULL REFERENCES devices(id),
                  refresh_token_hash TEXT NOT NULL UNIQUE,
                  issued_at REAL NOT NULL,
                  expires_at REAL NOT NULL,
                  last_used_at REAL NOT NULL,
                  revoked_at REAL
                );
                """
            )
            connection.commit()

    def _assert_registration_slot_available(
        self,
        connection: sqlite3.Connection,
        intended_slot: int,
    ) -> None:
        self._validate_slot(intended_slot)
        user_count = cast(int, connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        if user_count >= MAX_USERS:
            raise AuthError("maximum users already registered")

        slot_user = _one(
            connection.execute("SELECT id FROM users WHERE slot = ?", (intended_slot,))
        )
        if slot_user is not None:
            raise AuthError("slot already registered")

    def _assert_active_identity(self, identity: AuthIdentity) -> None:
        with self._connect() as connection:
            row = _one(
                connection.execute(
                    """
                    SELECT
                      users.status AS user_status,
                      devices.revoked_at AS device_revoked_at,
                      sessions.revoked_at AS session_revoked_at,
                      sessions.expires_at AS session_expires_at
                    FROM sessions
                    JOIN users ON users.id = sessions.user_id
                    JOIN devices ON devices.id = sessions.device_id
                    WHERE sessions.id = ?
                      AND sessions.user_id = ?
                      AND sessions.device_id = ?
                    """,
                    (identity.session_id, identity.user_id, identity.device_id),
                )
            )

        if row is None:
            raise AuthError("session not found")
        if row["user_status"] != "active":
            raise AuthError("user inactive")
        if row["device_revoked_at"] is not None or row["session_revoked_at"] is not None:
            raise AuthError("session revoked")
        if cast(float, row["session_expires_at"]) <= _now():
            raise AuthError("refresh session expired")

    def _create_device(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: int,
        device_label: str,
        device_fingerprint: str,
        now: float,
    ) -> JsonObject:
        cursor = connection.execute(
            """
            INSERT INTO devices (
              user_id, label, fingerprint_hash, created_at, last_seen_at, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (user_id, device_label, self._hash_secret(device_fingerprint), now, now),
        )
        return {
            "id": _last_insert_id(cursor),
            "user_id": user_id,
            "label": device_label,
            "created_at": _unix_to_iso(now),
            "last_seen_at": _unix_to_iso(now),
            "revoked_at": None,
        }

    def _create_session(
        self,
        connection: sqlite3.Connection,
        *,
        user_id: int,
        device_id: int,
        now: float,
    ) -> JsonObject:
        refresh_token = secrets.token_urlsafe(48)
        expires_at = now + self.refresh_ttl_seconds
        cursor = connection.execute(
            """
            INSERT INTO sessions (
              user_id, device_id, refresh_token_hash, issued_at, expires_at,
              last_used_at, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                user_id,
                device_id,
                self._hash_secret(refresh_token),
                now,
                expires_at,
                now,
            ),
        )
        return {
            "id": _last_insert_id(cursor),
            "user_id": user_id,
            "device_id": device_id,
            "refresh_token": refresh_token,
            "issued_at": _unix_to_iso(now),
            "expires_at": _unix_to_iso(expires_at),
            "last_used_at": _unix_to_iso(now),
            "revoked_at": None,
        }

    def _encode_token(self, payload: JsonObject) -> str:
        header: JsonObject = {"alg": "HS256", "typ": "JWT"}
        header_segment = _base64url_json(header)
        payload_segment = _base64url_json(payload)
        signed = f"{header_segment}.{payload_segment}".encode("ascii")
        signature = hmac.new(self._jwt_secret, signed, hashlib.sha256).digest()
        return f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"

    def _decode_token(self, token: str) -> JsonObject:
        try:
            header_segment, payload_segment, signature_segment = token.split(".", 2)
            signed = f"{header_segment}.{payload_segment}".encode("ascii")
            expected = hmac.new(self._jwt_secret, signed, hashlib.sha256).digest()
            actual = _base64url_decode(signature_segment)
            if not hmac.compare_digest(expected, actual):
                raise AuthError("token signature mismatch")

            payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthError("invalid token") from exc

        if not isinstance(payload, dict):
            raise AuthError("invalid token payload")
        return cast(JsonObject, payload)

    def _hash_secret(self, raw: str) -> str:
        return hmac.new(self._jwt_secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _validate_slot(slot: int) -> None:
        if slot not in {1, 2}:
            raise AuthError("slot must be 1 or 2")


def _one(cursor: sqlite3.Cursor) -> sqlite3.Row | None:
    return cast(sqlite3.Row | None, cursor.fetchone())


def _last_insert_id(cursor: sqlite3.Cursor) -> int:
    if cursor.lastrowid is None:
        raise AuthError("insert did not return a row id")
    return cursor.lastrowid


def _now() -> float:
    return time.time()


def _unix_to_iso(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))


def _base64url_json(payload: JsonObject) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(encoded)


def _base64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _base64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(f"{payload}{padding}".encode("ascii"))
