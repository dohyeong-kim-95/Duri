from __future__ import annotations

import asyncio

import httpx

from duri_api.main import create_app


def test_health_endpoint_reports_service_status() -> None:
    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {
        "service": "duri-api",
        "status": "ok",
        "version": "0.1.0",
    }
