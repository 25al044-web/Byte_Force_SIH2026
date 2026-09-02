"""Screening route endpoint.

MOCK / DEVELOPMENT IMPLEMENTATION:
This endpoint returns realistic mock data adhering strictly to the formal
API contract defined in docs/API_CONTRACT.md.
Real AI pipelines (OCR, MRZ parser, tamper detection, face biometric matching,
Gemini multimodal reasoning) are NOT implemented in this phase and will be
integrated in subsequent milestones.
"""

from fastapi import APIRouter, File, UploadFile, status

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
) -> ScreeningResponse:
    """Mock implementation of the identity and document screening pipeline.

    WARNING: MOCK / DEVELOPMENT ONLY.
    Does not run live AI inference (no Gemini, face recognition, or tamper models).
    """
    # Build simulated response following contract structure
    return ScreeningResponse(
        screening_id="SCR-2026-0001",
        document=DocumentExtractedData(
            document_type="passport",
            full_name="ARUN KUMAR",
            document_number="P1234567",
            nationality="IND",
            date_of_birth="2004-08-20",
            expiry_date="2032-08-14",
            sex="M",
        ),
        checks=ChecksContainer(
            mrz=MRZCheckResult(
                status=CheckStatus.PASS,
                score=0,
                reason="MRZ checksums valid",
            ),
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
            blacklist=BlacklistCheckResult(
                status=CheckStatus.PASS,
                reason="Document not found in demonstration blacklist",
            ),
        ),
        risk=RiskAssessment(
            score=27,
            level=RiskLevel.REVIEW,
        ),
        explanations=[
            "MRZ validation passed",
            "Document has not expired",
            "Possible compression inconsistency detected",
            "Face comparison passed",
        ],
    )
