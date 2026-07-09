from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from duri_api.auth import AuthService
from duri_api.main import create_app
from duri_api.storage import DuriStorageWriter

PARTICIPANTS = {
    "01J_USER_1": "Dohyeong",
    "01J_USER_2": "Partner",
}


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def make_auth(tmp_path: Path) -> dict[str, Any]:
    auth = AuthService(
        db_path=tmp_path / "auth.sqlite3",
        jwt_secret="test-signing-secret",
        hash_secret="test-hash-secret",
    )
    auth.create_invite_code(code="timeline-invite", intended_slot=1)
    session = auth.register_with_invite(
        code="timeline-invite",
        display_name="Dohyeong",
        device_label="phone",
        device_fingerprint="phone-fingerprint",
    )
    return {"service": auth, "access_token": session["access_token"]}


def make_writer(storage_root: Path) -> DuriStorageWriter:
    return DuriStorageWriter(
        storage_root=storage_root,
        participants=PARTICIPANTS,
        app_timezone="Asia/Seoul",
    )


async def get_json(
    *,
    auth: AuthService,
    storage_root: Path,
    access_token: str,
    path: str,
) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app(auth_service=auth, storage_root=storage_root))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers={"Authorization": f"Bearer {access_token}"})


def test_timeline_endpoint_reads_logs_from_duri_storage(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    writer = make_writer(storage_root)
    writer.append_message(
        log_id="01J_MSG_SECOND",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:29:00+09:00"),
        message_id="01J_MESSAGE_SECOND",
        text="두 번째 메시지",
    )
    writer.append_message(
        log_id="01J_MSG_FIRST",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_FIRST",
        text="첫 번째 메시지",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/timeline",
        )
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == ["01J_MSG_FIRST", "01J_MSG_SECOND"]
    assert items[0]["actor_display_name"] == "Dohyeong"
    assert items[1]["actor_display_name"] == "Partner"


def test_timeline_endpoint_filters_by_period_and_type(tmp_path: Path) -> None:
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
        created_at=dt("2026-07-12T19:30:00+09:00"),
        photo_bytes=b"july photo",
        original_filename="july.jpg",
        mime_type="image/jpeg",
    )
    writer.append_message(
        log_id="01J_MSG_AUGUST",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_AUGUST",
        text="8월 메시지",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/timeline?period=2026-07&type=Message",
        )
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["01J_MSG_JULY"]


def test_timeline_summary_endpoint_reports_period_and_type_facets(tmp_path: Path) -> None:
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
        created_at=dt("2026-07-12T19:30:00+09:00"),
        photo_bytes=b"july photo",
        original_filename="july.jpg",
        mime_type="image/jpeg",
    )
    writer.append_message(
        log_id="01J_MSG_AUGUST",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_AUGUST",
        text="8월 메시지",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/timeline/summary",
        )
    )

    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 3
    assert summary["types"] == {"Message": 2, "Photo": 1}
    assert summary["periods"] == [
        {"period": "2026-08", "total": 1, "types": {"Message": 1}},
        {"period": "2026-07", "total": 2, "types": {"Message": 1, "Photo": 1}},
    ]


def test_search_endpoint_filters_timeline_logs_from_duri_storage(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    writer = make_writer(storage_root)
    writer.append_message(
        log_id="01J_MSG_MATCH",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_MATCH",
        text="김치찌개 먹으러 가자",
    )
    writer.append_message(
        log_id="01J_MSG_OTHER",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:29:00+09:00"),
        message_id="01J_MESSAGE_OTHER",
        text="산책도 좋아",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/search?q=찌개",
        )
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["id"] for item in results] == ["01J_MSG_MATCH"]


def test_search_endpoint_combines_query_period_and_type_filters(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    writer = make_writer(storage_root)
    writer.append_message(
        log_id="01J_MSG_JULY_MATCH",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_JULY_MATCH",
        text="파스타 먹자",
    )
    writer.append_photo(
        log_id="01J_PHOTO_JULY_MATCH",
        actor_id="01J_USER_2",
        created_at=dt("2026-07-12T19:30:00+09:00"),
        photo_bytes=b"pasta photo",
        original_filename="pasta.jpg",
        mime_type="image/jpeg",
    )
    writer.append_message(
        log_id="01J_MSG_AUGUST_MATCH",
        actor_id="01J_USER_1",
        created_at=dt("2026-08-01T09:00:00+09:00"),
        message_id="01J_MESSAGE_AUGUST_MATCH",
        text="파스타 또 먹자",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/search?q=파스타&period=2026-07&type=Message",
        )
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["results"]] == ["01J_MSG_JULY_MATCH"]


def test_search_endpoint_returns_empty_results_for_blank_query(tmp_path: Path) -> None:
    storage_root = tmp_path / "DuriStorage"
    make_writer(storage_root).append_message(
        log_id="01J_MSG_BLANK_QUERY",
        actor_id="01J_USER_1",
        created_at=dt("2026-07-12T19:28:00+09:00"),
        message_id="01J_MESSAGE_BLANK_QUERY",
        text="빈 검색어에는 나오면 안 된다",
    )
    auth_context = make_auth(tmp_path)

    response = asyncio.run(
        get_json(
            auth=auth_context["service"],
            storage_root=storage_root,
            access_token=auth_context["access_token"],
            path="/search?q=+",
        )
    )

    assert response.status_code == 200
    assert response.json()["results"] == []
