"""Smoke tests for Phase 0 scaffold."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta() -> None:
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "commerce-engine"
    assert "version" in body
