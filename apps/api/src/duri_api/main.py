from __future__ import annotations

from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

APP_VERSION = "0.1.0"


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
        return {
            "service": "duri-api",
            "status": "ok",
            "version": APP_VERSION,
        }

    @app.websocket("/ws/probe")
    async def websocket_probe(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"type": "connection.ready"})

        try:
            while True:
                message: dict[str, Any] = await websocket.receive_json()
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                await websocket.send_json({"type": "echo", "payload": message})
        except WebSocketDisconnect:
            return

    return app


app = create_app()
