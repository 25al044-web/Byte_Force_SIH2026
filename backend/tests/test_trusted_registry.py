"""Comprehensive unit and integration tests for Trusted Identity Registry and Cross-Verification."""

import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db_connection, init_db, seed_trusted_registry
from app.main import app
from app.services.face_matcher import compute_embedding_similarity
from app.services.risk_engine import calculate_risk
from app.services.trusted_registry import (
    cross_verify_identity,
    deactivate_trusted_identity,
    get_trusted_identity,
    list_trusted_identities,
    lookup_trusted_identity,
    normalize_date,
    normalize_doc_number,
    normalize_doc_type,
    normalize_name,
    register_trusted_identity,
    update_trusted_identity,
)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure database schema and synthetic seeds are initialized for each test run."""
    init_db()


# ---------------------------------------------------------------------------
# 1. Normalization Utility Tests
# ---------------------------------------------------------------------------

def test_normalization_name():
    assert normalize_name("  arun   kumar  ") == "ARUN KUMAR"
    assert normalize_name("John O'Connor-Smith") == "JOHN O'CONNOR-SMITH"
    assert normalize_name("") == ""
    assert normalize_name(None) == ""


def test_normalization_doc_number():
    assert normalize_doc_number(" ID-123 456_ ") == "ID123456"
    assert normalize_doc_number("pass_998877") == "PASS998877"
    assert normalize_doc_number(None) == ""


def test_normalization_date():
    assert normalize_date("15-05-1995") == "1995-05-15"
    assert normalize_date("15/05/1995") == "1995-05-15"
    assert normalize_date("1995-05-15") == "1995-05-15"
    assert normalize_date("1995/05/15") == "1995-05-15"
    assert normalize_date("15.05.1995") == "1995-05-15"
    assert normalize_date(None) == ""


def test_normalization_doc_type():
    assert normalize_doc_type("passport") == "PASSPORT"
    assert normalize_doc_type("driving licence") == "DRIVING_LICENSE"
    assert normalize_doc_type("DRIVING_LICENSE") == "DRIVING_LICENSE"
    assert normalize_doc_type("identity card") == "NATIONAL_ID"
    assert normalize_doc_type("aadhaar") == "AADHAAR"


# ---------------------------------------------------------------------------
# 2. Registry CRUD Tests
# ---------------------------------------------------------------------------

def test_register_and_get_trusted_identity():
    doc_num = "TESTREG001"
    res = register_trusted_identity(
        full_name="TEST USER ALPHA",
        document_number=doc_num,
        document_type="PASSPORT",
        date_of_birth="1990-01-01",
        nationality="IND",
        notes="Synthetic test record",
    )
    assert res["document_number"] == "TESTREG001"
    assert res["full_name"] == "TEST USER ALPHA"
    assert res["is_active"] is True

    # Retrieve by registry_id
    rec = get_trusted_identity(res["registry_id"])
    assert rec is not None
    assert rec["full_name"] == "TEST USER ALPHA"
    assert rec["document_number"] == "TESTREG001"


def test_lookup_trusted_identity_normalized():
    # Synthetic seed ARUN KUMAR with ID123456 exists from startup
    rec = lookup_trusted_identity("ID-123456")
    assert rec is not None
    assert rec["full_name"] == "ARUN KUMAR"
    assert rec["document_number"] == "ID123456"

    # Case insensitivity & spaces
    rec_spaces = lookup_trusted_identity("id 123456")
    assert rec_spaces is not None
    assert rec_spaces["full_name"] == "ARUN KUMAR"


def test_deactivate_trusted_identity():
    doc_num = "DEACT001"
    created = register_trusted_identity(
        full_name="DEACTIVATE ME",
        document_number=doc_num,
        document_type="NATIONAL_ID",
        date_of_birth="1985-10-20",
    )
    reg_id = created["registry_id"]

    # Active lookup succeeds
    assert lookup_trusted_identity(doc_num) is not None

    # Deactivate
    assert deactivate_trusted_identity(reg_id) is True

    # Active lookup now returns None
    assert lookup_trusted_identity(doc_num) is None

    # But direct record still retrievable with is_active = False
    rec = get_trusted_identity(reg_id)
    assert rec is not None
    assert rec["is_active"] is False


# ---------------------------------------------------------------------------
# 3. Cross-Verification Engine Tests
# ---------------------------------------------------------------------------

def test_cross_verify_exact_match():
    # ARUN KUMAR, ID123456, 1995-05-15, PASSPORT, IND
    extracted = {
        "document_number": "ID123456",
        "full_name": "ARUN KUMAR",
        "date_of_birth": "1995-05-15",
        "document_type": "PASSPORT",
        "nationality": "IND",
    }
    result = cross_verify_identity(extracted)
    assert result["status"] == "MATCH"
    assert result["record_found"] is True
    assert result["risk_level"] == "LOW"
    assert len(result["mismatches"]) == 0
    assert result["comparisons"]["full_name"]["matches"] is True
    assert result["comparisons"]["date_of_birth"]["matches"] is True


def test_cross_verify_core_jury_name_mismatch():
    """Core acceptance demo test:

    Presented document has Name = RAHUL SHARMA on ID123456,
    while trusted registry record has Name = ARUN KUMAR on ID123456.
    Must detect MISMATCH, HIGH risk, and explicit mismatch explanation.
    """
    extracted = {
        "document_number": "ID123456",
        "full_name": "RAHUL SHARMA",
        "date_of_birth": "1995-05-15",
        "document_type": "PASSPORT",
        "nationality": "IND",
    }
    result = cross_verify_identity(extracted)
    assert result["status"] == "MISMATCH"
    assert result["record_found"] is True
    assert result["risk_level"] == "HIGH"
    assert len(result["mismatches"]) >= 1

    name_mismatch = next((m for m in result["mismatches"] if m["field"] == "full_name"), None)
    assert name_mismatch is not None
    assert name_mismatch["severity"] == "HIGH"
    assert "ARUN KUMAR" in name_mismatch["reason"]
    assert "RAHUL SHARMA" in name_mismatch["reason"]
    assert "ARUN KUMAR" in result["reason"]
    assert "RAHUL SHARMA" in result["reason"]


def test_cross_verify_dob_mismatch():
    extracted = {
        "document_number": "ID123456",
        "full_name": "ARUN KUMAR",
        "date_of_birth": "1980-01-01",  # Different DOB
        "document_type": "PASSPORT",
    }
    result = cross_verify_identity(extracted)
    assert result["status"] == "MISMATCH"
    assert result["risk_level"] == "HIGH"
    dob_mismatch = next((m for m in result["mismatches"] if m["field"] == "date_of_birth"), None)
    assert dob_mismatch is not None
    assert dob_mismatch["severity"] == "HIGH"


def test_cross_verify_not_found():
    extracted = {
        "document_number": "UNKNOWN999999",
        "full_name": "NON REGISTERED USER",
    }
    result = cross_verify_identity(extracted)
    assert result["status"] == "NOT_FOUND"
    assert result["record_found"] is False
    assert result["risk_level"] == "LOW"
    assert len(result["mismatches"]) == 0


def test_cross_verify_with_face_biometrics():
    # Register an identity with a synthetic 512-d unit vector
    doc_num = "BIOMETRIC001"
    synthetic_emb = [0.0] * 512
    synthetic_emb[0] = 1.0  # Unit vector along dimension 0

    register_trusted_identity(
        full_name="BIOMETRIC SUBJECT",
        document_number=doc_num,
        document_type="PASSPORT",
        date_of_birth="1990-01-01",
        precomputed_embedding=synthetic_emb,
    )

    # 1. Matching document portrait (same vector -> 100% similarity)
    matching_doc_emb = [0.0] * 512
    matching_doc_emb[0] = 1.0

    res_match = cross_verify_identity(
        extracted_data={"document_number": doc_num, "full_name": "BIOMETRIC SUBJECT", "date_of_birth": "1990-01-01"},
        doc_embedding=matching_doc_emb,
    )
    assert res_match["status"] == "MATCH"
    assert res_match["tri_face_match"] is not None
    assert res_match["tri_face_match"]["trusted_vs_document"] >= 95.0

    # 2. Conflicting document portrait (orthogonal vector -> ~50% similarity, below 60% threshold)
    conflicting_doc_emb = [0.0] * 512
    conflicting_doc_emb[1] = 1.0  # Orthogonal vector

    res_conflict = cross_verify_identity(
        extracted_data={"document_number": doc_num, "full_name": "BIOMETRIC SUBJECT", "date_of_birth": "1990-01-01"},
        doc_embedding=conflicting_doc_emb,
    )
    assert res_conflict["status"] == "MISMATCH"
    assert any("face_biometric" in m["field"] for m in res_conflict["mismatches"])


# ---------------------------------------------------------------------------
# 4. Risk Engine Integration Tests
# ---------------------------------------------------------------------------

def test_risk_engine_with_trusted_mismatch():
    checks = {
        "mrz": {"status": "PASS"},
        "expiry": {"status": "PASS"},
        "tamper": {"status": "PASS", "risk": 0},
        "face_match": {"status": "PASS", "similarity": 95.0},
        "duplicate_identity": {"status": "PASS"},
        "blacklist": {"status": "PASS"},
        "trusted_registry": {
            "status": "MISMATCH",
            "mismatches": [{"field": "full_name", "severity": "HIGH"}],
            "reason": "Presented identity name conflicts with trusted registry (Stored: ARUN KUMAR, Presented: RAHUL SHARMA)",
        },
    }
    risk = calculate_risk(checks)
    assert risk["score"] >= 75
    assert risk["level"] == "HIGH"
    assert risk["contributions"]["trusted_registry"] == 60
    assert any("Trusted identity registry conflict" in exp for exp in risk["explanations"])
    assert any("high-risk threshold (75)" in exp for exp in risk["explanations"])


def test_risk_engine_with_trusted_match():
    checks = {
        "mrz": {"status": "PASS"},
        "expiry": {"status": "PASS"},
        "tamper": {"status": "PASS", "risk": 0},
        "face_match": {"status": "PASS", "similarity": 95.0},
        "duplicate_identity": {"status": "PASS"},
        "blacklist": {"status": "PASS"},
        "trusted_registry": {
            "status": "MATCH",
            "mismatches": [],
            "reason": "Presented document matches trusted identity registry",
        },
    }
    risk = calculate_risk(checks)
    assert risk["score"] == 0
    assert risk["level"] == "LOW"
    assert risk["contributions"]["trusted_registry"] == 0
    assert any("matches trusted identity registry" in exp for exp in risk["explanations"])


def test_risk_engine_with_trusted_not_found():
    checks = {
        "mrz": {"status": "PASS"},
        "expiry": {"status": "PASS"},
        "tamper": {"status": "PASS", "risk": 0},
        "face_match": {"status": "PASS", "similarity": 95.0},
        "duplicate_identity": {"status": "PASS"},
        "blacklist": {"status": "PASS"},
        "trusted_registry": {
            "status": "NOT_FOUND",
            "mismatches": [],
        },
    }
    risk = calculate_risk(checks)
    assert risk["score"] == 0
    assert risk["level"] == "LOW"
    assert risk["contributions"]["trusted_registry"] == 0


# ---------------------------------------------------------------------------
# 5. FastAPI Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_api_trusted_identities_endpoints():
    client = TestClient(app)

    # 1. List
    res_list = client.get("/api/trusted-identities")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert "records" in data_list
    assert data_list["total"] >= 1

    # 2. Register new via JSON
    new_doc = "APITEST999"
    res_create = client.post(
        "/api/trusted-identities",
        json={
            "full_name": "API TEST USER",
            "document_number": new_doc,
            "document_type": "PASSPORT",
            "date_of_birth": "1992-06-15",
            "nationality": "IND",
            "notes": "Created via API test",
        },
    )
    assert res_create.status_code == 201
    created_rec = res_create.json()["record"]
    assert created_rec["document_number"] == new_doc

    # 3. Lookup by document number
    res_lookup = client.get(f"/api/trusted-identities/lookup/{new_doc}")
    assert res_lookup.status_code == 200
    assert res_lookup.json()["record"]["full_name"] == "API TEST USER"

    # 4. Deactivate
    reg_id = created_rec["registry_id"]
    res_deact = client.post(f"/api/trusted-identities/{reg_id}/deactivate")
    assert res_deact.status_code == 200
    assert res_deact.json()["is_active"] is False

    # 5. Lookup after deactivation returns 404
    res_lookup_after = client.get(f"/api/trusted-identities/lookup/{new_doc}")
    assert res_lookup_after.status_code == 404


def test_blockchain_audit_invariance():
    """Ensure blockchain audit hashes only canonical results without raw embeddings or photos."""
    from app.services.blockchain.audit_service import create_audit

    screening_id = "SCR-AUDIT-TEST-001"
    doc_bytes = b"synthetic-doc-bytes"
    selfie_bytes = b"synthetic-selfie-bytes"
    result_payload = {
        "risk": {"score": 75, "level": "HIGH"},
        "checks": {
            "tamper": {"status": "PASS", "recommendation": "SECONDARY_INSPECTION_RECOMMENDED"},
            "face_match": {"status": "PASS"},
            "trusted_registry": {"status": "MISMATCH", "record_found": True},
        },
    }

    audit = create_audit(screening_id, doc_bytes, selfie_bytes, result_payload)
    assert audit["screening_id"] == screening_id
    assert audit["report_hash"] is not None
    # Verify no raw biometric or PII is leaked in audit representation
    assert "full_name" not in audit
    assert "photo_embedding" not in audit
