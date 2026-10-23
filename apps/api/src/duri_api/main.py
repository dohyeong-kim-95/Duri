from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from duri_api.auth import AuthError, AuthIdentity, AuthService
from duri_api.timeline import (
    read_timeline_logs,
    read_timeline_summary,
    resolve_storage_path,
    search_timeline_logs,
)

APP_VERSION = "0.1.0"
DEFAULT_CORS_ORIGINS = ["http://localhost:3000"]
MIN_SECRET_BYTES = 32
REQUIRED_ENV_VARS = ("DURI_STORAGE_ROOT", "DURI_AUTH_DB", "DURI_JWT_SECRET", "DURI_HASH_SECRET")


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
            # Re-check on every message so revoking a device also cuts open sockets.
            try:
                auth_service.assert_active_identity(identity)
            except AuthError:
                await websocket.close(code=1008, reason="session revoked")
                return

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            await websocket.send_json({"type": "echo", "payload": message})
    except WebSocketDisconnect:
        return


def create_app(
    auth_service: AuthService | None = None,
    storage_root: Path | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Duri API", version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins is not None else DEFAULT_CORS_ORIGINS,
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

    # Data handlers are plain `def`: they read files synchronously, so FastAPI runs
    # them in its threadpool instead of blocking the event loop (and WebSockets).
    @app.get("/timeline", tags=["data"])
    def timeline(request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        return {
            "items": read_timeline_logs(
                storage_root,
                period=request.query_params.get("period"),
                log_type=request.query_params.get("type"),
            ),
            "identity": identity.as_dict(),
        }

    @app.get("/timeline/summary", tags=["data"])
    def timeline_summary(request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        return {
            **read_timeline_summary(storage_root),
            "identity": identity.as_dict(),
        }

    @app.get("/photos/{photo_path:path}", tags=["data"])
    def photo(photo_path: str, request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        if storage_root is not None and resolve_storage_path(storage_root, photo_path) is None:
            raise HTTPException(status_code=400, detail="invalid photo path")
        return {"photo_path": photo_path, "identity": identity.as_dict()}

    @app.get("/search", tags=["data"])
    def search(request: Request) -> dict[str, Any]:
        identity = require_identity(request)
        query = request.query_params.get("q", "")
        return {
            "results": search_timeline_logs(
                storage_root,
                query,
                period=request.query_params.get("period"),
                log_type=request.query_params.get("type"),
            ),
            "identity": identity.as_dict(),
        }

    @app.websocket("/ws/probe")
    async def websocket_probe(websocket: WebSocket) -> None:
        await handle_websocket_probe(websocket)

    @app.websocket("/ws/timeline")
    async def websocket_timeline(websocket: WebSocket) -> None:
        await handle_timeline_websocket(websocket, auth_service)

    return app


def create_app_from_env(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Build the real app from environment variables.

    Run with: uvicorn --factory duri_api.main:create_app_from_env

    Variables:
        DURI_STORAGE_ROOT: DuriStorage directory (required).
        DURI_AUTH_DB: auth SQLite path, outside DuriStorage (required).
        DURI_JWT_SECRET: token signing key, at least 32 bytes (required).
        DURI_HASH_SECRET: hash key, at least 32 bytes, different from the signing key
            (required).
        DURI_CORS_ORIGINS: comma-separated allowed origins (default localhost:3000).

    Args:
        environ: Variables to read (None reads os.environ).

    Returns:
        The configured FastAPI app. Raises ValueError if a variable is missing or weak.
    """
    if environ is None:
        environ = os.environ

    missing = [name for name in REQUIRED_ENV_VARS if not environ.get(name)]
    if missing:
        raise ValueError(f"missing required environment variables: {', '.join(missing)}")

    for name in ("DURI_JWT_SECRET", "DURI_HASH_SECRET"):
        if len(environ[name].encode("utf-8")) < MIN_SECRET_BYTES:
            raise ValueError(f"{name} must be at least {MIN_SECRET_BYTES} bytes")

    cors_origins = DEFAULT_CORS_ORIGINS
    cors_text = environ.get("DURI_CORS_ORIGINS", "")
    if cors_text.strip():
        cors_origins = [origin.strip() for origin in cors_text.split(",") if origin.strip()]

    auth_service = AuthService(
        db_path=Path(environ["DURI_AUTH_DB"]),
        jwt_secret=environ["DURI_JWT_SECRET"],
        hash_secret=environ["DURI_HASH_SECRET"],
    )
    return create_app(
        auth_service=auth_service,
        storage_root=Path(environ["DURI_STORAGE_ROOT"]),
        cors_origins=cors_origins,
    )


# Unconfigured default: every data endpoint answers 401 (deny by default).
# Use create_app_from_env for a real server.
app = create_app()
