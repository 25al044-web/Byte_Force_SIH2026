"""Tests for demo helper routes and reset endpoints."""

import sqlite3
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db

client = TestClient(app)


def test_demo_status_endpoint():
    """GET /api/demo/status returns demo_mode flag and ok status."""
    response = client.get("/api/demo/status")
    assert response.status_code == 200
    data = response.json()
    assert "demo_mode" in data
    assert data["status"] == "ok"


def test_demo_reset_endpoint(tmp_path, monkeypatch):
    """POST /api/demo/reset clears identity_embeddings table without altering blacklist."""
    test_db = str(tmp_path / "screening_test.db")
    init_db(test_db)
    monkeypatch.setenv("DATABASE_URL", test_db)
    monkeypatch.setenv("DEMO_MODE", "true")

    # Insert a dummy identity embedding and verify blacklist has seeds
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO identity_embeddings (document_number, full_name, embedding) VALUES ('TEST-DOC', 'JOHN', '[0.1, 0.2]')"
    )
    conn.commit()

    emb_count = conn.execute("SELECT COUNT(*) FROM identity_embeddings").fetchone()[0]
    bl_count = conn.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    conn.close()

    assert emb_count == 1
    assert bl_count >= 1

    # Call reset endpoint
    response = client.post("/api/demo/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "identity_embeddings" in data["cleared_table"]

    # Verify embeddings table is now empty, but blacklist is preserved
    conn = sqlite3.connect(test_db)
    post_emb_count = conn.execute("SELECT COUNT(*) FROM identity_embeddings").fetchone()[0]
    post_bl_count = conn.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    conn.close()

    assert post_emb_count == 0
    assert post_bl_count == bl_count


def test_demo_reset_forbidden_when_demo_mode_false(monkeypatch):
    """POST /api/demo/reset returns 403 Forbidden when DEMO_MODE=false."""
    monkeypatch.setenv("DEMO_MODE", "false")
    response = client.post("/api/demo/reset")
    assert response.status_code == 403
    assert "disabled in production mode" in response.json()["detail"].lower()
