"""Screening route endpoint.

MOCK / DEVELOPMENT IMPLEMENTATION:
This endpoint returns realistic mock data adhering strictly to the formal
API contract defined in docs/API_CONTRACT.md.
Real AI pipelines (OCR, MRZ parser, tamper detection, face biometric matching,
Gemini multimodal reasoning) are NOT implemented in this phase and will be
integrated in subsequent milestones.
"""

from typing import Optional
from fastapi import APIRouter, File, Query, UploadFile, status

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

from app.services.blacklist_checker import check_blacklist
from app.services.mrz_validator import validate_td3_mrz
from app.services.risk_engine import calculate_risk

# TEMPORARY DEVELOPMENT BRIDGE:
# Real OCR/multimodal document extraction is not implemented yet.
# We use a synthetic development TD3 MRZ matching the mock extracted document:
# Name: ARUN KUMAR, Country: IND, Doc#: P1234567, DOB: 040820, Expiry: 320814, Sex: M
DEV_SYNTHETIC_MRZ_LINE_1 = "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
DEV_SYNTHETIC_MRZ_LINE_2 = "P1234567<1IND0408204M3208140<<<<<<<<<<<<<<<4"

router = APIRouter()


@router.post(
    "/screen",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
    summary="Screen Document and Selfie (MOCK / DEVELOPMENT)",
    description=(
        "Accepts identity document and selfie uploads, returning simulated screening "
        "results adhering strictly to the API contract. MARKED AS MOCK / DEVELOPMENT."
    ),
)
async def screen_identity(
    document_image: UploadFile = File(..., description="Travel/identity document image or PDF"),
    selfie_image: UploadFile = File(..., description="Live applicant selfie/portrait image"),
    doc_number_override: Optional[str] = Query(
        None,
        description="Optional development parameter to test specific document numbers against blacklist",
    ),
) -> ScreeningResponse:
    """Mock implementation of the identity and document screening pipeline.

    WARNING: MOCK / DEVELOPMENT ONLY.
    Note: MRZ verification is running the REAL ICAO TD3 validator, blacklist
    screening is running against the REAL SQLite database, and the risk assessment
    is evaluated by the REAL explainable risk engine.
    """
    # Active document number for screening (defaults to standard mock passport)
    active_doc_number = doc_number_override.strip().upper() if doc_number_override else "P1234567"

    # Execute REAL MRZ validator on synthetic development bridge MRZ
    mrz_validation = validate_td3_mrz(DEV_SYNTHETIC_MRZ_LINE_1, DEV_SYNTHETIC_MRZ_LINE_2)
    mrz_check = MRZCheckResult(
        status=CheckStatus(mrz_validation["status"]),
        score=mrz_validation["score"],
        reason=mrz_validation["reason"],
        details=mrz_validation.get("details"),
    )

    # Execute REAL SQLite Blacklist Checker
    blacklist_res = check_blacklist(
        document_number=active_doc_number,
        full_name="ARUN KUMAR",
        nationality="IND",
        date_of_birth="2004-08-20",
    )
    blacklist_check = BlacklistCheckResult(
        status=CheckStatus(blacklist_res["status"]),
        reason=blacklist_res["reason"],
        match=blacklist_res.get("match"),
    )

    checks = ChecksContainer(
        mrz=mrz_check,
        expiry=ExpiryCheckResult(
            status=CheckStatus.PASS,
            score=0,
            reason="Document is valid",
        ),
        tamper=TamperCheckResult(
            status=CheckStatus.WARNING,
            risk=32,
            reason="Possible image compression inconsistency",
        ),
        face_match=FaceMatchCheckResult(
            status=CheckStatus.PASS,
            similarity=91.7,
            reason="Selfie is visually consistent with document portrait",
        ),
        duplicate_identity=DuplicateIdentityCheckResult(
            status=CheckStatus.PASS,
            similar_identity=None,
            reason="No matching face associated with another identity",
        ),
        blacklist=blacklist_check,
    )

    # Execute REAL explainable risk-scoring engine
    risk_evaluation = calculate_risk(checks)

    # Build response following contract structure with dynamic risk evaluation
    return ScreeningResponse(
        screening_id="SCR-2026-0001",
        document=DocumentExtractedData(
            document_type="passport",
            full_name="ARUN KUMAR",
            document_number=active_doc_number,
            nationality="IND",
            date_of_birth="2004-08-20",
            expiry_date="2032-08-14",
            sex="M",
        ),
        checks=checks,
        risk=RiskAssessment(
            score=risk_evaluation["score"],
            level=RiskLevel(risk_evaluation["level"]),
        ),
        explanations=risk_evaluation["explanations"],
    )
