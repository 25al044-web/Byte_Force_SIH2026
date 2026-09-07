"""Security regression tests for the officer-only registry boundary."""
import os
os.environ["REGISTRY_OFFICER_PIN"] = "123456"

from fastapi.testclient import TestClient
from app.main import app

def test_registry_requires_server_side_officer_session():
    client = TestClient(app)
    assert client.get("/api/registry").status_code == 401
    assert client.post("/api/registry/auth/unlock", json={"pin": "12ab56"}).status_code == 401
    response = client.post("/api/registry/auth/unlock", json={"pin": "123456"})
    assert response.status_code == 200
    token = response.json()["token"]
    assert "pin" not in response.json()
    assert client.get("/api/registry", headers={"X-Registry-Session": token}).status_code == 200
    assert client.post("/api/registry/auth/lock", headers={"X-Registry-Session": token}).status_code == 200
    assert client.get("/api/registry", headers={"X-Registry-Session": token}).status_code == 401

def test_pin_attempt_lockout():
    from app.services.registry_auth import _attempts
    _attempts.clear()
    client = TestClient(app)
    for _ in range(5): client.post("/api/registry/auth/unlock", json={"pin": "000000"})
    assert client.post("/api/registry/auth/unlock", json={"pin": "123456"}).status_code == 429
