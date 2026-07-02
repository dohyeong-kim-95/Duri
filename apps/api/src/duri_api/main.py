from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from duri_api.auth import AuthError, AuthIdentity, AuthService
from duri_api.timeline import read_timeline_logs, search_timeline_logs

APP_VERSION = "0.1.0"


class ProbeWebSocket(Protocol):
    async def accept(self) -> None: ...

    async def send_json(self, data: Any) -> None: ...

    async def receive_json(self) -> dict[str, Any]: ...


class TimelineWebSocket(Protocol):
    @property
    def query_params(self) -> Mapping[str, str]: ...

    async def accept(self) -> None: ...

    async def close(self, code: int = 1000, reason: str | None = None) -> None: ...

    async def send_json(self, data: Any) -> None: ...

    async def receive_json(self) -> dict[str, Any]: ...


def health_payload() -> dict[str, str]:
    return {
        "service": "duri-api",
        "status": "ok",
        "version": APP_VERSION,
    }


async def handle_websocket_probe(websocket: ProbeWebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connection.ready"})

    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            await websocket.send_json({"type": "echo", "payload": message})
    except WebSocketDisconnect:
        return


async def handle_timeline_websocket(
    websocket: TimelineWebSocket,
    auth_service: AuthService | None,
) -> None:
    token = websocket.query_params.get("access_token")
    if auth_service is None or token is None:
        await websocket.close(code=1008, reason="authentication required")
        return

    try:
        identity = auth_service.validate_access_token(token)
    except AuthError:
        await websocket.close(code=1008, reason="authentication required")
        return

    await websocket.accept()
    await websocket.send_json({"type": "timeline.ready", "identity": identity.as_dict()})

    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            await websocket.send_json({"type": "echo", "payload": message})
    except WebSocketDisconnect:
        return


def create_app(
    auth_service: AuthService | None = None,
    storage_root: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Duri API", version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def require_identity(request: Request) -> AuthIdentity:
        if auth_service is None:
            raise HTTPException(status_code=401, detail="authentication required")

        auth_header = request.headers.get("authorization", "")
        prefix = "Bearer "
        if not auth_header.startswith(prefix):
            raise HTTPException(status_code=401, detail="authentication required")

        try:
            return auth_service.validate_access_token(auth_header[len(prefix) :].strip())
        except AuthError as exc:
            raise HTTPException(status_code=401, detail="authentication required") from exc

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return health_payload()

    @app.get("/timeline", tags=["data"])
    async def timeline(request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        return {"items": read_timeline_logs(storage_root), "identity": identity.as_dict()}

    @app.get("/photos/{photo_path:path}", tags=["data"])
    async def photo(photo_path: str, request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        return {"photo_path": photo_path, "identity": identity.as_dict()}

    @app.get("/search", tags=["data"])
    async def search(request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        query = request.query_params.get("q", "")
        return {
            "results": search_timeline_logs(storage_root, query),
            "identity": identity.as_dict(),
        }

    @app.websocket("/ws/probe")
    async def websocket_probe(websocket: WebSocket) -> None:
        await handle_websocket_probe(websocket)

    @app.websocket("/ws/timeline")
    async def websocket_timeline(websocket: WebSocket) -> None:
        await handle_timeline_websocket(websocket, auth_service)

    return app


app = create_app()
