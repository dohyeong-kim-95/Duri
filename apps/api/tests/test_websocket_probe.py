from fastapi.testclient import TestClient

from duri_api.main import create_app


def test_websocket_probe_accepts_connection_and_replies_to_ping() -> None:
    client = TestClient(create_app())

    with client.websocket_connect("/ws/probe") as websocket:
        assert websocket.receive_json() == {"type": "connection.ready"}

        websocket.send_json({"type": "ping"})

        assert websocket.receive_json() == {"type": "pong"}
