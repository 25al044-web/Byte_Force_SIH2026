"""Tests for Audit Trail endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_audits_endpoint():
    """Verify that GET /api/audit returns 200 with audits list and blockchain status."""
    response = client.get("/api/audit")
    assert response.status_code == 200
    data = response.json()
    assert "audits" in data
    assert "total" in data
    assert "blockchain_configured" in data
    assert isinstance(data["audits"], list)


def test_verify_audit_endpoint_not_found():
    """Verify that GET /api/audit/{id} returns NOT_FOUND for non-existent ID."""
    response = client.get("/api/audit/NON_EXISTENT_ID")
    assert response.status_code == 200
    data = response.json()
    assert data["integrity_status"] == "NOT_FOUND"
