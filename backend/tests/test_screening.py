"""Tests for the screening pipeline API endpoint and Pydantic models."""

import io
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


def test_screen_endpoint_success():
    """Verify POST /api/screen returns 200 and conforms to the API contract."""
    files = {
        "document_image": ("passport.jpg", io.BytesIO(b"fake_doc_image_bytes"), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie_image_bytes"), "image/jpeg"),
    }
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200

    data = response.json()

    # Validate against Pydantic model
    validated = ScreeningResponse.model_validate(data)
    assert validated.screening_id == "SCR-2026-0001"

    # Validate document structure
    assert validated.document.document_type == "passport"
    assert validated.document.full_name == "ARUN KUMAR"
    assert validated.document.document_number == "P1234567"
    assert validated.document.nationality == "IND"

    # Validate checks
    checks = validated.checks
    for check_name, check_obj in [
        ("mrz", checks.mrz),
        ("expiry", checks.expiry),
        ("tamper", checks.tamper),
        ("face_match", checks.face_match),
        ("duplicate_identity", checks.duplicate_identity),
        ("blacklist", checks.blacklist),
    ]:
        assert check_obj.status.value in ALLOWED_CHECK_STATUSES, (
            f"Check {check_name} has invalid status {check_obj.status}"
        )
        assert isinstance(check_obj.reason, str) and len(check_obj.reason) > 0

    # Specific check fields
    assert checks.mrz.status == CheckStatus.PASS
    assert checks.mrz.score == 0
    assert checks.mrz.reason == "All MRZ checksums are valid"
    assert checks.mrz.details is not None
    assert checks.mrz.details["composite_valid"] is True
    assert checks.tamper.risk == 32
    assert checks.face_match.similarity == 91.7
    assert checks.duplicate_identity.similar_identity is None
    # Blacklist check dynamically evaluated by SQLite blacklist service
    assert checks.blacklist.status == CheckStatus.PASS
    assert "not found in demonstration blacklist" in checks.blacklist.reason
    assert checks.blacklist.match is None

    # Validate dynamic risk assessment computed by risk_engine
    assert 0 <= validated.risk.score <= 100
    assert isinstance(validated.risk.score, int)
    assert validated.risk.level.value in ALLOWED_RISK_LEVELS
    # For default mock inputs (tamper risk 32 adds +10, rest 0), score is 10 and level is LOW
    assert validated.risk.score == 10
    assert validated.risk.level == RiskLevel.LOW

    # Validate explanations
    assert isinstance(validated.explanations, list)
    assert len(validated.explanations) >= 6
    assert all(isinstance(exp, str) and len(exp.strip()) > 0 for exp in validated.explanations)
    assert any("Tamper screening detected minor anomaly" in exp for exp in validated.explanations)


def test_screen_endpoint_with_blacklisted_document():
    """Verify that a blacklisted document triggers FAIL and activates the risk engine override."""
    files = {
        "document_image": ("passport.jpg", io.BytesIO(b"fake_doc_image_bytes"), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(b"fake_selfie_image_bytes"), "image/jpeg"),
    }
    response = client.post("/api/screen?doc_number_override=TEST0001", files=files)
    assert response.status_code == 200

    data = response.json()
    validated = ScreeningResponse.model_validate(data)

    # Document number should match the override
    assert validated.document.document_number == "TEST0001"

    # Blacklist check must report FAIL
    assert validated.checks.blacklist.status == CheckStatus.FAIL
    assert "matched active demonstration blacklist record" in validated.checks.blacklist.reason
    assert validated.checks.blacklist.match is not None
    assert validated.checks.blacklist.match["document_number"] == "TEST0001"
    assert validated.checks.blacklist.match["severity"] == "HIGH"

    # Risk Engine must trigger critical override to at least 85 and HIGH risk level
    assert validated.risk.score >= 85
    assert validated.risk.level == RiskLevel.HIGH
    assert any("Blacklist match triggered minimum high-risk threshold (85)" in exp for exp in validated.explanations)
    assert any("Document/identity found on blacklist: +70 risk." in exp for exp in validated.explanations)


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
