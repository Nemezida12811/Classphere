from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


def test_healthcheck():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == settings.PROJECT_NAME