"""Unit tests for SQLite blacklist screening service and database initialization."""

import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.database.session import (
    SYNTHETIC_BLACKLIST_SEEDS,
    get_db_connection,
    init_db,
    seed_blacklist_data,
)
from app.services.blacklist_checker import check_blacklist
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_database_initialized():
    """Ensure database schema is created and seeded before tests."""
    init_db()


def test_non_blacklisted_document_returns_pass():
    """A standard document number not on the blacklist returns PASS."""
    res = check_blacklist("CLEAN12345")
    assert res["status"] == "PASS"
    assert "not found in demonstration blacklist" in res["reason"]
    assert res["match"] is None


def test_blacklisted_document_returns_fail():
    """A blacklisted synthetic document number returns FAIL."""
    res = check_blacklist("TEST0001")
    assert res["status"] == "FAIL"
    assert "matched active demonstration blacklist record" in res["reason"]
    assert res["match"] is not None
    assert res["match"]["document_number"] == "TEST0001"
    assert res["match"]["severity"] == "HIGH"
    assert res["match"]["reason"] == "Synthetic stolen-document demonstration record"


def test_returned_severity_and_reason_correct():
    """Check that severity and reason match the database record for other synthetic entries."""
    res = check_blacklist("DEMO9999")
    assert res["status"] == "FAIL"
    assert res["match"]["severity"] == "CRITICAL"
    assert res["match"]["reason"] == "Synthetic financial sanctions watchlist demonstration record"

    res_alpha = check_blacklist("BLACKLIST01")
    assert res_alpha["status"] == "FAIL"
    assert res_alpha["match"]["severity"] == "MEDIUM"


def test_inactive_blacklist_entry_does_not_produce_fail():
    """An inactive blacklist record (is_active = 0) must not cause a FAIL result."""
    # INACTIVE01 is seeded with is_active = 0
    res = check_blacklist("INACTIVE01")
    assert res["status"] == "PASS"
    assert res["match"] is None


def test_missing_document_number_handled_safely():
    """Missing, None, or whitespace-only document number returns NOT_AVAILABLE safely."""
    res_none = check_blacklist(None)
    assert res_none["status"] == "NOT_AVAILABLE"
    assert res_none["match"] is None

    res_empty = check_blacklist("")
    assert res_empty["status"] == "NOT_AVAILABLE"

    res_spaces = check_blacklist("   ")
    assert res_spaces["status"] == "NOT_AVAILABLE"


def test_database_unavailable_handled_as_not_available():
    """If the database connection encounters an error, service fails gracefully with NOT_AVAILABLE."""
    # Create a dummy connection and close it immediately to simulate a broken/unavailable database
    dead_conn = sqlite3.connect(":memory:")
    dead_conn.close()

    res = check_blacklist("TEST0001", db_conn=dead_conn)
    assert res["status"] == "NOT_AVAILABLE"
    assert "database temporarily unavailable" in res["reason"]
    assert res["match"] is None


def test_seed_operation_is_idempotent():
    """Running seed_blacklist_data multiple times does not duplicate records."""
    conn = get_db_connection()
    try:
        # First check current count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM blacklist;")
        initial_count = cursor.fetchone()[0]
        assert initial_count >= len(SYNTHETIC_BLACKLIST_SEEDS)

        # Run seed again
        newly_inserted = seed_blacklist_data(conn)
        assert newly_inserted == 0

        # Verify count has not changed
        cursor.execute("SELECT COUNT(*) FROM blacklist;")
        final_count = cursor.fetchone()[0]
        assert final_count == initial_count
    finally:
        conn.close()


def test_service_does_not_leak_internal_fields():
    """Match dictionary must only expose sanitized public fields (no primary keys, timestamps, etc.)."""
    res = check_blacklist("TEST0001")
    assert res["status"] == "FAIL"
    match = res["match"]
    assert set(match.keys()) == {"document_number", "reason", "severity"}
    assert "id" not in match
    assert "created_at" not in match
    assert "is_active" not in match


def test_case_insensitive_and_whitespace_trimming():
    """Document number matching should be case-insensitive and tolerate surrounding spaces."""
    res = check_blacklist("  test0001  ")
    assert res["status"] == "FAIL"
    assert res["match"]["document_number"] == "TEST0001"


def test_get_blacklist_endpoint():
    """GET /api/blacklist returns active records by default; active_only=false returns all seeds."""
    # Active-only (default): INACTIVE01 must NOT appear
    response = client.get("/api/blacklist")
    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data
    assert "DEMONSTRATION" in data["disclaimer"]
    assert isinstance(data["records"], list)
    for rec in data["records"]:
        assert rec["is_active"] is True

    # Fetch all records (active_only=false) to verify seeds are present
    response_all = client.get("/api/blacklist?active_only=false")
    assert response_all.status_code == 200
    data_all = response_all.json()
    assert data_all["total"] >= len(SYNTHETIC_BLACKLIST_SEEDS)
    doc_numbers_all = [r["document_number"] for r in data_all["records"]]
    assert "TEST0001" in doc_numbers_all
    assert "DEMO9999" in doc_numbers_all
    assert "INACTIVE01" in doc_numbers_all
