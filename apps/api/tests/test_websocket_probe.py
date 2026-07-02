from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocketDisconnect

from duri_api.main import handle_websocket_probe


class FakeProbeWebSocket:
    def __init__(self, incoming: list[dict[str, Any]]) -> None:
        self.accepted = False
        self.incoming = incoming
        self.sent: list[dict[str, Any]] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Any) -> None:
        self.sent.append(data)

    async def receive_json(self) -> dict[str, Any]:
        if not self.incoming:
            raise WebSocketDisconnect(code=1000)
        return self.incoming.pop(0)


def test_websocket_probe_accepts_connection_and_replies_to_ping() -> None:
    websocket = FakeProbeWebSocket([{"type": "ping"}])

    asyncio.run(handle_websocket_probe(websocket))

    assert websocket.accepted
    assert websocket.sent == [{"type": "connection.ready"}, {"type": "pong"}]
