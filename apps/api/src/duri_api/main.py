from __future__ import annotations

from typing import Any, Protocol

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = "0.1.0"


class ProbeWebSocket(Protocol):
    async def accept(self) -> None: ...

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


def create_app() -> FastAPI:
    app = FastAPI(title="Duri API", version=APP_VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return health_payload()

    @app.websocket("/ws/probe")
    async def websocket_probe(websocket: WebSocket) -> None:
        await handle_websocket_probe(websocket)

    return app


app = create_app()
