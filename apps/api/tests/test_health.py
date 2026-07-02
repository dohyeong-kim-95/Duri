from fastapi.testclient import TestClient

from duri_api.main import create_app


def test_health_endpoint_reports_service_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "duri-api",
        "status": "ok",
        "version": "0.1.0",
    }
