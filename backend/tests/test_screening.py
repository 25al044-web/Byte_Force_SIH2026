"""Tests for the screening pipeline API endpoint and Pydantic models."""

import io
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.screening import (
    BlacklistCheckResult,
    ChecksContainer,
    CheckStatus,
    DocumentExtractedData,
    DuplicateIdentityCheckResult,
    ExpiryCheckResult,
    FaceMatchCheckResult,
    MRZCheckResult,
    RiskAssessment,
    RiskLevel,
    ScreeningResponse,
    TamperCheckResult,
)

client = TestClient(app)

ALLOWED_CHECK_STATUSES = {"PASS", "WARNING", "FAIL", "NOT_AVAILABLE"}
ALLOWED_RISK_LEVELS = {"LOW", "REVIEW", "HIGH"}

SAMPLE_PASSPORT_EXTRACTION = {
    "success": True,
    "document": {
        "document_type": "passport",
        "full_name": "SARAH JANE CONNOR",
        "document_number": "P1234567",
        "nationality": "IND",
        "date_of_birth": "2004-08-20",
        "expiry_date": "2032-08-14",
        "sex": "M",
        "issuing_authority": None,
        "institution_or_organization": None,
    },
    # Synthetic TD3 MRZ matching the document details
    "mrz_line_1": "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
    "mrz_line_2": "P1234567<1IND0408204M3208140<<<<<<<<<<<<<<<4",
    "warnings": [],
}

SAMPLE_STUDENT_ID_EXTRACTION = {
    "success": True,
    "document": {
        "document_type": "student_id",
        "full_name": "KARTHIKEYAN MARAN",
        "document_number": "REG-2026-99",
        "nationality": None,
        "date_of_birth": "2005-08-14",
        "expiry_date": None,
        "sex": None,
        "issuing_authority": None,
        "institution_or_organization": "R.M.D. Engineering College",
    },
    "mrz_line_1": None,
    "mrz_line_2": None,
    "warnings": ["MRZ not present on this document"],
}

SAMPLE_EXTRACTION_FAILURE = {
    "success": False,
    "document": {
        "document_type": None,
        "full_name": None,
        "document_number": None,
        "nationality": None,
        "date_of_birth": None,
        "expiry_date": None,
        "sex": None,
        "issuing_authority": None,
        "institution_or_organization": None,
    },
    "mrz_line_1": None,
    "mrz_line_2": None,
    "warnings": ["Document extraction unavailable"],
}


SAMPLE_FACE_PASS = {
    "status": "PASS",
    "similarity": 91.7,
    "reason": "Selfie matches document portrait (91.7% similarity)",
}


@patch("app.routes.screening.compare_faces", return_value=SAMPLE_FACE_PASS)
@patch("app.routes.screening.extract_document", return_value=SAMPLE_PASSPORT_EXTRACTION)
def test_screen_endpoint_success(mock_extract, mock_face):
    """Verify POST /api/screen returns 200 and conforms to the API contract with passport."""
    files = {
        "document_image": ("passport.jpg", io.BytesIO(b"fake_doc_image_bytes"), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie_image_bytes"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = ScreeningResponse.model_validate(data)
    assert validated.screening_id == "SCR-2026-0001"

    # Extracted document fields
    assert validated.document.document_type == "passport"
    assert validated.document.full_name == "SARAH JANE CONNOR"
    assert validated.document.document_number == "P1234567"
    assert validated.document.nationality == "IND"

    # Checks verification
    checks = validated.checks
    assert checks.mrz.status == CheckStatus.PASS
    assert checks.mrz.score == 0
    assert checks.mrz.details is not None
    assert checks.mrz.details["composite_valid"] is True

    # Real expiry verification
    assert checks.expiry.status == CheckStatus.PASS
    assert checks.expiry.score == 0

    # Real blacklist verification
    assert checks.blacklist.status == CheckStatus.PASS
    assert "not found in demonstration blacklist" in checks.blacklist.reason

    # Face match check (mocked PASS)
    assert checks.face_match.status == CheckStatus.PASS
    assert checks.face_match.similarity == 91.7

    # Risk assessment — tamper WARNING (+10) is the only contributor; score=10, level=LOW
    assert 0 <= validated.risk.score <= 100
    assert validated.risk.score == 10
    assert validated.risk.level == RiskLevel.LOW
    assert len(validated.explanations) >= 6


@patch("app.routes.screening.extract_document", return_value=SAMPLE_STUDENT_ID_EXTRACTION)
def test_screen_endpoint_with_student_id_no_mrz(mock_extract):
    """Verify generic student/college ID without MRZ yields NOT_AVAILABLE (not FAIL)."""
    files = {
        "document_image": ("student_id.png", io.BytesIO(b"fake_id_image_bytes"), "image/png"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie_image_bytes"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = ScreeningResponse.model_validate(data)

    assert validated.document.document_type == "student_id"
    assert validated.document.full_name == "KARTHIKEYAN MARAN"
    assert validated.document.document_number == "REG-2026-99"
    assert validated.document.nationality is None
    assert validated.document.expiry_date is None

    # MRZ check must NOT fail simply because it's a student ID
    assert validated.checks.mrz.status == CheckStatus.NOT_AVAILABLE
    assert "MRZ is not present or could not be extracted" in validated.checks.mrz.reason

    # Expiry check should be NOT_AVAILABLE
    assert validated.checks.expiry.status == CheckStatus.NOT_AVAILABLE

    # Blacklist check should pass for clean ID
    assert validated.checks.blacklist.status == CheckStatus.PASS

    # Composite risk score should not be marked HIGH simply for missing MRZ
    assert validated.risk.level in (RiskLevel.LOW, RiskLevel.REVIEW)


@patch("app.routes.screening.extract_document", return_value=SAMPLE_EXTRACTION_FAILURE)
def test_screen_endpoint_extraction_failure_produces_null_fields(mock_extract):
    """Extraction failure returns null document fields, never hardcoded ARUN KUMAR."""
    files = {
        "document_image": ("blurry.jpg", io.BytesIO(b"unreadable_bytes"), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = ScreeningResponse.model_validate(data)

    # Document fields MUST be null, not mock data
    assert validated.document.full_name is None
    assert validated.document.full_name != "ARUN KUMAR"
    assert validated.document.document_number is None
    assert validated.document.nationality is None

    # Checks become NOT_AVAILABLE
    assert validated.checks.mrz.status == CheckStatus.NOT_AVAILABLE
    assert validated.checks.expiry.status == CheckStatus.NOT_AVAILABLE
    assert validated.checks.blacklist.status == CheckStatus.NOT_AVAILABLE


@patch("app.routes.screening.extract_document", return_value=SAMPLE_PASSPORT_EXTRACTION)
def test_screen_endpoint_with_blacklisted_document(mock_extract):
    """Verify blacklisted document override triggers FAIL and activates high risk override."""
    files = {
        "document_image": ("passport.jpg", io.BytesIO(b"fake_doc_image_bytes"), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie_image_bytes"), "image/jpeg"),
    }
    response = client.post("/api/screen?doc_number_override=TEST0001", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = ScreeningResponse.model_validate(data)

    assert validated.document.document_number == "TEST0001"
    assert validated.checks.blacklist.status == CheckStatus.FAIL
    assert "matched active demonstration blacklist record" in validated.checks.blacklist.reason
    assert validated.checks.blacklist.match["document_number"] == "TEST0001"

    # Risk Engine must trigger critical override to at least 85 and HIGH risk level
    assert validated.risk.score >= 85
    assert validated.risk.level == RiskLevel.HIGH


def test_screen_endpoint_missing_document_image():
    """Verify that omitting document_image triggers a 422 Unprocessable Entity error."""
    files = {
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 422


def test_screen_endpoint_missing_selfie_image():
    """Verify that omitting selfie_image triggers a 422 Unprocessable Entity error."""
    files = {
        "document_image": ("passport.jpg", io.BytesIO(b"fake_doc"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 422


def test_document_extracted_data_nullability():
    """Verify that all document fields can be null without failing validation."""
    doc = DocumentExtractedData(
        document_type=None,
        full_name=None,
        document_number=None,
        nationality=None,
        date_of_birth=None,
        expiry_date=None,
        sex=None,
    )
    assert doc.full_name is None
    assert doc.document_number is None


def test_pydantic_schema_invalid_check_status():
    """Verify that an invalid check status raises a ValidationError."""
    with pytest.raises(ValidationError):
        MRZCheckResult(
            status="UNKNOWN_STATUS",  # type: ignore[arg-type]
            reason="Invalid status test",
        )


def test_pydantic_schema_invalid_risk_score():
    """Verify that risk score must be between 0 and 100 inclusive."""
    with pytest.raises(ValidationError):
        RiskAssessment(score=101, level=RiskLevel.HIGH)

    with pytest.raises(ValidationError):
        RiskAssessment(score=-1, level=RiskLevel.LOW)


def test_pydantic_schema_invalid_risk_level():
    """Verify that an invalid risk level raises a ValidationError."""
    with pytest.raises(ValidationError):
        RiskAssessment(score=50, level="EXTREME")  # type: ignore[arg-type]
