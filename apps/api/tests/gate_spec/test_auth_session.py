from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import httpx
import pytest

from duri_api.auth import AuthError, AuthService
from duri_api.main import create_app, handle_timeline_websocket


def make_auth(tmp_path: Path, *, access_ttl_seconds: int = 300) -> AuthService:
    return AuthService(
        db_path=tmp_path / "auth.sqlite3",
        jwt_secret="test-secret",
        access_ttl_seconds=access_ttl_seconds,
    )


def register_user(
    auth: AuthService,
    *,
    code: str = "invite-slot-1",
    slot: int = 1,
    display_name: str = "Dohyeong",
    device_label: str = "phone",
) -> dict[str, Any]:
    auth.create_invite_code(code=code, intended_slot=slot)
    return auth.register_with_invite(
        code=code,
        display_name=display_name,
        device_label=device_label,
        device_fingerprint=f"fingerprint-{device_label}",
    )


def sqlite_bytes(path: Path) -> bytes:
    return path.read_bytes()


def sqlite_scalar(db_path: Path, query: str, params: tuple[object, ...] = ()) -> object:
    with sqlite3.connect(db_path) as connection:
        return connection.execute(query, params).fetchone()[0]


async def get_json(
    auth: AuthService,
    path: str,
    *,
    access_token: str | None = None,
) -> httpx.Response:
    app = create_app(auth_service=auth)
    headers = {}
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


class FakeDataWebSocket:
    def __init__(self, access_token: str | None = None) -> None:
        self.query_params = {}
        if access_token is not None:
            self.query_params["access_token"] = access_token
        self.accepted = False
        self.closed: tuple[int, str] | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.closed = (code, reason or "")

    async def send_json(self, _data: Any) -> None:
        return None

    async def receive_json(self) -> dict[str, Any]:
        raise RuntimeError("not used by unauthenticated rejection test")


@pytest.mark.gate_spec("B1-1. 유효한 초대 코드로 사용자 등록에 성공한다.")
def test_b1_1_valid_invite_code_registers_user(tmp_path: Path) -> None:
    """B1-1. 유효한 초대 코드로 사용자 등록에 성공한다."""
    auth = make_auth(tmp_path)

    result = register_user(auth, code="valid-invite", slot=1, display_name="Dohyeong")

    assert result["user"]["slot"] == 1
    assert result["user"]["display_name"] == "Dohyeong"
    assert result["access_token"]
    assert result["refresh_token"]


@pytest.mark.gate_spec("B1-2. 이미 사용된 초대 코드로는 등록할 수 없다 (1회 소모).")
def test_b1_2_consumed_invite_code_cannot_register_again(tmp_path: Path) -> None:
    """B1-2. 이미 사용된 초대 코드로는 등록할 수 없다 (1회 소모)."""
    auth = make_auth(tmp_path)
    register_user(auth, code="one-time-invite", slot=1)

    with pytest.raises(AuthError):
        auth.register_with_invite(
            code="one-time-invite",
            display_name="Partner",
            device_label="second-phone",
            device_fingerprint="second-fingerprint",
        )


@pytest.mark.gate_spec(
    "B1-3. 두 슬롯이 모두 등록된 상태에서는 어떤 경로로도 세 번째 사용자를 만들 수 없다."
)
def test_b1_3_no_third_user_can_be_created_after_two_slots_are_registered(
    tmp_path: Path,
) -> None:
    """B1-3. 두 슬롯이 모두 등록된 상태에서는 어떤 경로로도 세 번째 사용자를 만들 수 없다."""
    auth = make_auth(tmp_path)
    register_user(auth, code="slot-1", slot=1)
    register_user(auth, code="slot-2", slot=2, display_name="Partner", device_label="partner")
    auth.create_invite_code(code="third-attempt", intended_slot=1)

    with pytest.raises(AuthError):
        auth.register_with_invite(
            code="third-attempt",
            display_name="Third",
            device_label="third-device",
            device_fingerprint="third-fingerprint",
        )

    assert sqlite_scalar(auth.db_path, "SELECT COUNT(*) FROM users") == 2


@pytest.mark.gate_spec("B1-4. 같은 슬롯에 두 명이 등록될 수 없다 (slot 유일성).")
def test_b1_4_same_slot_cannot_be_registered_twice(tmp_path: Path) -> None:
    """B1-4. 같은 슬롯에 두 명이 등록될 수 없다 (slot 유일성)."""
    auth = make_auth(tmp_path)
    register_user(auth, code="slot-one-a", slot=1)
    auth.create_invite_code(code="slot-one-b", intended_slot=1)

    with pytest.raises(AuthError):
        auth.register_with_invite(
            code="slot-one-b",
            display_name="Duplicate",
            device_label="duplicate-device",
            device_fingerprint="duplicate-fingerprint",
        )


@pytest.mark.gate_spec(
    "B2-1. 초대 코드 원문은 DB·로그·`DuriStorage/` 어디에도 저장되지 않는다 (해시만 존재)."
)
def test_b2_1_invite_code_plaintext_is_never_stored(tmp_path: Path) -> None:
    """B2-1. 초대 코드 원문은 DB·로그·`DuriStorage/` 어디에도 저장되지 않는다 (해시만 존재)."""
    storage_root = tmp_path / "DuriStorage"
    storage_root.mkdir()
    auth = make_auth(tmp_path)
    raw_code = "plain-invite-secret"

    register_user(auth, code=raw_code, slot=1)

    assert raw_code.encode() not in sqlite_bytes(auth.db_path)
    assert sqlite_scalar(auth.db_path, "SELECT COUNT(*) FROM invite_codes WHERE code_hash != ''") == 1
    assert list(storage_root.rglob("*")) == []


@pytest.mark.gate_spec("B2-2. Refresh token 원문도 동일하다.")
def test_b2_2_refresh_token_plaintext_is_never_stored(tmp_path: Path) -> None:
    """B2-2. Refresh token 원문도 동일하다."""
    auth = make_auth(tmp_path)

    result = register_user(auth, code="refresh-secret", slot=1)

    assert result["refresh_token"].encode() not in sqlite_bytes(auth.db_path)
    assert sqlite_scalar(auth.db_path, "SELECT COUNT(*) FROM sessions WHERE refresh_token_hash != ''") == 1


@pytest.mark.gate_spec(
    "B2-3. `DuriStorage/` 트리 안에 auth 운영 데이터(해시 포함)가 존재하지 않는다."
)
def test_b2_3_auth_operating_data_is_not_written_inside_duri_storage(tmp_path: Path) -> None:
    """B2-3. `DuriStorage/` 트리 안에 auth 운영 데이터(해시 포함)가 존재하지 않는다."""
    storage_root = tmp_path / "DuriStorage"
    storage_root.mkdir()
    auth = make_auth(tmp_path)

    result = register_user(auth, code="storage-boundary", slot=1)
    auth.refresh_access_token(result["refresh_token"])

    assert list(storage_root.rglob("*")) == []


@pytest.mark.gate_spec(
    "B3-1. 인증 없는 요청은 모든 데이터 엔드포인트(Timeline, 사진, 검색, WebSocket)에서 거부된다."
)
def test_b3_1_unauthenticated_requests_are_rejected_for_all_data_endpoints(
    tmp_path: Path,
) -> None:
    """B3-1. 인증 없는 요청은 모든 데이터 엔드포인트(Timeline, 사진, 검색, WebSocket)에서 거부된다."""
    auth = make_auth(tmp_path)

    assert asyncio.run(get_json(auth, "/timeline")).status_code == 401
    assert asyncio.run(get_json(auth, "/photos/2026/2026-07/example.jpg")).status_code == 401
    assert asyncio.run(get_json(auth, "/search")).status_code == 401

    websocket = FakeDataWebSocket()
    asyncio.run(handle_timeline_websocket(websocket, auth))
    assert not websocket.accepted
    assert websocket.closed == (1008, "authentication required")


@pytest.mark.gate_spec("B3-2. 만료된 access token은 거부된다.")
def test_b3_2_expired_access_token_is_rejected(tmp_path: Path) -> None:
    """B3-2. 만료된 access token은 거부된다."""
    auth = make_auth(tmp_path)
    result = register_user(auth, code="expired-access", slot=1)
    expired = auth.issue_access_token(
        user_id=result["user"]["id"],
        device_id=result["device"]["id"],
        session_id=result["session"]["id"],
        ttl_seconds=-1,
    )

    response = asyncio.run(get_json(auth, "/timeline", access_token=expired))

    assert response.status_code == 401


@pytest.mark.gate_spec("B3-3. 유효한 refresh session으로 access token을 갱신할 수 있다.")
def test_b3_3_valid_refresh_session_can_issue_new_access_token(tmp_path: Path) -> None:
    """B3-3. 유효한 refresh session으로 access token을 갱신할 수 있다."""
    auth = make_auth(tmp_path)
    result = register_user(auth, code="refresh-access", slot=1)

    refreshed = auth.refresh_access_token(result["refresh_token"])
    response = asyncio.run(get_json(auth, "/timeline", access_token=refreshed["access_token"]))

    assert refreshed["access_token"] != result["access_token"]
    assert response.status_code == 200


@pytest.mark.gate_spec(
    "B4-1. 특정 기기의 세션을 폐기하면 그 기기의 refresh token은 거부된다."
)
def test_b4_1_revoked_device_refresh_token_is_rejected(tmp_path: Path) -> None:
    """B4-1. 특정 기기의 세션을 폐기하면 그 기기의 refresh token은 거부된다."""
    auth = make_auth(tmp_path)
    result = register_user(auth, code="device-revoke", slot=1)

    auth.revoke_device(result["device"]["id"])

    with pytest.raises(AuthError):
        auth.refresh_access_token(result["refresh_token"])


@pytest.mark.gate_spec(
    "B4-2. 한 기기의 폐기는 같은 사용자의 다른 기기 세션에 영향을 주지 않는다."
)
def test_b4_2_revoking_one_device_does_not_affect_another_device_session(
    tmp_path: Path,
) -> None:
    """B4-2. 한 기기의 폐기는 같은 사용자의 다른 기기 세션에 영향을 주지 않는다."""
    auth = make_auth(tmp_path)
    first = register_user(auth, code="multi-device", slot=1)
    second = auth.create_device_session(
        user_id=first["user"]["id"],
        device_label="tablet",
        device_fingerprint="tablet-fingerprint",
    )

    auth.revoke_device(first["device"]["id"])

    with pytest.raises(AuthError):
        auth.refresh_access_token(first["refresh_token"])

    refreshed = auth.refresh_access_token(second["refresh_token"])
    assert refreshed["access_token"]
