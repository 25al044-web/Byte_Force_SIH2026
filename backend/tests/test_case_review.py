"""Tests for Case Review endpoints."""

from fastapi.testclient import TestClient
from app.main import app
from app.services.case_service import save_case

client = TestClient(app)


def test_list_cases_endpoint():
    """Verify that GET /api/cases returns 200 with cases list."""
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert "total" in data
    assert isinstance(data["cases"], list)


def test_save_and_get_case():
    """Verify saving a case and fetching it via GET /api/cases/{screening_id}."""
    test_id = "SCR-TEST-REVIEW-001"
    save_case(
        screening_id=test_id,
        risk_score=78,
        risk_level="HIGH",
        recommendation="SECONDARY_INSPECTION_RECOMMENDED",
        main_reason="Visible vs MRZ mismatch detected",
        status="FAIL",
        extracted_identity={"full_name": "TEST PERSON", "document_number": "P999999"},
        detected_issues=["Name mismatch between visual and MRZ"],
        document_integrity_status="FAIL",
        face_match_status="PASS",
    )

    response = client.get(f"/api/cases/{test_id}")
    assert response.status_code == 200
    case = response.json()
    assert case["screening_id"] == test_id
    assert case["risk_score"] == 78
    assert case["risk_level"] == "HIGH"
    assert case["recommendation"] == "SECONDARY_INSPECTION_RECOMMENDED"
    assert case["extracted_identity"]["full_name"] == "TEST PERSON"


def test_get_case_not_found():
    """Verify 404 for invalid case ID."""
    response = client.get("/api/cases/INVALID_SCREENING_ID_999")
    assert response.status_code == 404
