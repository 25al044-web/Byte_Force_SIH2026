"""Tests for System Status dashboard endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_status_endpoint():
    """Verify GET /api/system/status returns all expected service statuses."""
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "ONLINE"
    assert data["database"] in ("CONNECTED", "ERROR")
    assert data["ai_extraction"] in ("AVAILABLE", "UNAVAILABLE")
    assert data["face_verification"] in ("AVAILABLE", "UNAVAILABLE")
    assert data["blockchain"] in ("CONNECTED", "UNAVAILABLE")
    assert data["frontend"] == "RUNNING"


def test_health_endpoint_detailed():
    """Verify GET /api/health?detailed=true returns detailed system status."""
    response = client.get("/api/health?detailed=true")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "database" in data
    assert "blockchain" in data
