"""Tests for blacklist management API routes.

Covers: POST /api/blacklist, GET /api/blacklist, PATCH /api/blacklist/{doc}/deactivate
and integration with the check_blacklist() service and screening pipeline.
"""

import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.database.session import init_db, get_db_connection
from app.services.blacklist_checker import check_blacklist
from app.main import app

client = TestClient(app)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def ensure_db():
    """Ensure the DB schema exists before each test."""
    init_db()


@pytest.fixture()
def cleanup_test_doc():
    """Remove any test record created during a test."""
    doc = "TEST-JURY-001"
    yield doc
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM blacklist WHERE UPPER(document_number) = ?;", (doc.upper(),))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def cleanup_sql_injection_doc():
    doc = "SQL-INJECT-TEST"
    yield doc
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM blacklist WHERE UPPER(document_number) = ?;", (doc.upper(),))
        conn.commit()
    finally:
        conn.close()


# ──────────────────────────────────────────────
# 1. Add valid blacklist record
# ──────────────────────────────────────────────

def test_add_valid_blacklist_record(cleanup_test_doc):
    """POST /api/blacklist with valid payload returns 201 and correct record."""
    payload = {
        "document_number": cleanup_test_doc,
        "full_name": "DEMO PERSON",
        "nationality": "IND",
        "date_of_birth": "1995-01-01",
        "reason": "Reported stolen document for jury demo",
        "severity": "HIGH",
    }
    res = client.post("/api/blacklist", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["success"] is True
    assert "added" in data["message"] or "reactivated" in data["message"]
    record = data["record"]
    assert record["document_number"] == cleanup_test_doc.upper()
    assert record["severity"] == "HIGH"
    assert record["is_active"] is True
    assert record["reason"] == "Reported stolen document for jury demo"
    assert "created_at" in record


# ──────────────────────────────────────────────
# 2. Missing document_number → validation error
# ──────────────────────────────────────────────

def test_add_missing_document_number():
    """POST /api/blacklist without document_number returns 422."""
    res = client.post("/api/blacklist", json={"reason": "test", "severity": "LOW"})
    assert res.status_code == 422


# ──────────────────────────────────────────────
# 3. Missing reason → validation error
# ──────────────────────────────────────────────

def test_add_missing_reason():
    """POST /api/blacklist without reason returns 422."""
    res = client.post("/api/blacklist", json={"document_number": "NOREASONTEST", "severity": "LOW"})
    assert res.status_code == 422


# ──────────────────────────────────────────────
# 4. Invalid severity → validation error
# ──────────────────────────────────────────────

def test_add_invalid_severity():
    """POST /api/blacklist with invalid severity returns 422."""
    res = client.post("/api/blacklist", json={
        "document_number": "BADSEVERITYTEST",
        "reason": "Some reason",
        "severity": "EXTREME",
    })
    assert res.status_code == 422
    detail = res.json()["detail"]
    assert any("severity" in str(d).lower() for d in (detail if isinstance(detail, list) else [detail]))


# ──────────────────────────────────────────────
# 5. Duplicate active record handled safely (409)
# ──────────────────────────────────────────────

def test_add_duplicate_active_record(cleanup_test_doc):
    """Adding the same active document number twice returns 409 Conflict."""
    payload = {
        "document_number": cleanup_test_doc,
        "reason": "First entry",
        "severity": "MEDIUM",
    }
    res1 = client.post("/api/blacklist", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/blacklist", json={**payload, "reason": "Duplicate attempt"})
    assert res2.status_code == 409
    assert "already active" in res2.json()["detail"].lower()


# ──────────────────────────────────────────────
# 6. List active blacklist records
# ──────────────────────────────────────────────

def test_list_blacklist_returns_active_records():
    """GET /api/blacklist returns only active records by default."""
    res = client.get("/api/blacklist")
    assert res.status_code == 200
    data = res.json()
    assert "records" in data
    assert "total" in data
    assert "disclaimer" in data
    for rec in data["records"]:
        assert rec["is_active"] is True


# ──────────────────────────────────────────────
# 7. Inactive record not returned in active-only listing
# ──────────────────────────────────────────────

def test_inactive_record_not_in_active_listing():
    """INACTIVE01 (is_active=0 seed) must not appear in default active listing."""
    res = client.get("/api/blacklist")
    assert res.status_code == 200
    doc_numbers = [r["document_number"] for r in res.json()["records"]]
    assert "INACTIVE01" not in doc_numbers


# ──────────────────────────────────────────────
# 8. Deactivate record
# ──────────────────────────────────────────────

def test_deactivate_record(cleanup_test_doc):
    """PATCH /api/blacklist/{doc}/deactivate sets is_active=0 without deleting."""
    # First add the record
    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "For deactivation test",
        "severity": "LOW",
    })

    res = client.patch(f"/api/blacklist/{cleanup_test_doc}/deactivate")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["success"] is True
    assert "deactivated" in data["message"].lower()

    # Verify it no longer appears in active listing
    listing = client.get("/api/blacklist")
    doc_numbers = [r["document_number"] for r in listing.json()["records"]]
    assert cleanup_test_doc.upper() not in doc_numbers

    # But appears in all-records listing
    listing_all = client.get("/api/blacklist?active_only=false")
    doc_numbers_all = [r["document_number"] for r in listing_all.json()["records"]]
    assert cleanup_test_doc.upper() in doc_numbers_all


# ──────────────────────────────────────────────
# 9. Newly added document is detected by check_blacklist()
# ──────────────────────────────────────────────

def test_newly_added_document_detected_by_service(cleanup_test_doc):
    """After POST /api/blacklist, check_blacklist() returns FAIL for that doc."""
    # Confirm PASS before adding
    before = check_blacklist(cleanup_test_doc)
    assert before["status"] == "PASS"

    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "Integration test entry",
        "severity": "HIGH",
    })

    after = check_blacklist(cleanup_test_doc)
    assert after["status"] == "FAIL"
    assert after["match"]["document_number"] == cleanup_test_doc.upper()
    assert after["match"]["severity"] == "HIGH"


# ──────────────────────────────────────────────
# 10. HIGH severity record causes blacklist FAIL
# ──────────────────────────────────────────────

def test_high_severity_record_triggers_fail(cleanup_test_doc):
    """A HIGH severity record correctly returns FAIL with correct severity in match."""
    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "High severity test",
        "severity": "HIGH",
    })
    result = check_blacklist(cleanup_test_doc)
    assert result["status"] == "FAIL"
    assert result["match"]["severity"] == "HIGH"


# ──────────────────────────────────────────────
# 11. Deactivated record no longer triggers FAIL in check_blacklist()
# ──────────────────────────────────────────────

def test_deactivated_record_does_not_trigger_fail(cleanup_test_doc):
    """After deactivation, check_blacklist() returns PASS for that document."""
    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "Lifecycle test",
        "severity": "CRITICAL",
    })
    assert check_blacklist(cleanup_test_doc)["status"] == "FAIL"

    client.patch(f"/api/blacklist/{cleanup_test_doc}/deactivate")
    after = check_blacklist(cleanup_test_doc)
    assert after["status"] == "PASS"
    assert after["match"] is None


# ──────────────────────────────────────────────
# 12. SQL injection-like input treated as plain data
# ──────────────────────────────────────────────

def test_sql_injection_input_treated_as_plain_data(cleanup_sql_injection_doc):
    """Input containing SQL-like syntax is stored as literal data, not executed."""
    injected_reason = "'; DROP TABLE blacklist; --"
    res = client.post("/api/blacklist", json={
        "document_number": cleanup_sql_injection_doc,
        "reason": injected_reason,
        "severity": "LOW",
    })
    assert res.status_code == 201
    # Table must still exist and be queryable
    listing = client.get("/api/blacklist")
    assert listing.status_code == 200
    # The reason was stored literally, not executed
    records = listing.json()["records"]
    match = next((r for r in records if r["document_number"] == cleanup_sql_injection_doc.upper()), None)
    assert match is not None
    assert match["reason"] == injected_reason


# ──────────────────────────────────────────────
# 13. Severity filter on GET /api/blacklist
# ──────────────────────────────────────────────

def test_get_blacklist_severity_filter():
    """GET /api/blacklist?severity=CRITICAL returns only CRITICAL records."""
    res = client.get("/api/blacklist?severity=CRITICAL")
    assert res.status_code == 200
    for rec in res.json()["records"]:
        assert rec["severity"] == "CRITICAL"


# ──────────────────────────────────────────────
# 14. Search filter on GET /api/blacklist
# ──────────────────────────────────────────────

def test_get_blacklist_search_filter(cleanup_test_doc):
    """GET /api/blacklist?search=<partial> returns matching records."""
    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "full_name": "JURY DEMO PERSON",
        "reason": "Search filter test",
        "severity": "MEDIUM",
    })
    res = client.get(f"/api/blacklist?search=JURY-001")
    assert res.status_code == 200
    doc_numbers = [r["document_number"] for r in res.json()["records"]]
    assert cleanup_test_doc.upper() in doc_numbers


# ──────────────────────────────────────────────
# 15. Deactivate non-existent record → 404
# ──────────────────────────────────────────────

def test_deactivate_nonexistent_record_returns_404():
    """PATCH deactivate for a document not in the DB returns 404."""
    res = client.patch("/api/blacklist/DOES-NOT-EXIST-XYZ/deactivate")
    assert res.status_code == 404


# ──────────────────────────────────────────────
# 16. Reactivate deactivated record via POST
# ──────────────────────────────────────────────

def test_reactivate_deactivated_record_via_post(cleanup_test_doc):
    """Adding a document that was deactivated reactivates it."""
    client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "Initial entry",
        "severity": "LOW",
    })
    client.patch(f"/api/blacklist/{cleanup_test_doc}/deactivate")
    assert check_blacklist(cleanup_test_doc)["status"] == "PASS"

    res = client.post("/api/blacklist", json={
        "document_number": cleanup_test_doc,
        "reason": "Reactivated entry",
        "severity": "HIGH",
    })
    assert res.status_code == 201
    assert "reactivated" in res.json()["message"].lower()
    assert check_blacklist(cleanup_test_doc)["status"] == "FAIL"
    assert check_blacklist(cleanup_test_doc)["match"]["severity"] == "HIGH"
