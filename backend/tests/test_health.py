"""Tests for health check endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that /api/health returns HTTP 200 and status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint():
    """Verify that / returns API metadata and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" not in data or data["status"] != "error"
    assert "/api/health" in data.get("health", "")
