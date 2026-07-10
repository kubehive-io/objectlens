from fastapi.testclient import TestClient

from app.main import app


def test_list_providers() -> None:
    client = TestClient(app)
    response = client.get("/providers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_reload_providers() -> None:
    client = TestClient(app)
    response = client.post("/providers/reload")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
