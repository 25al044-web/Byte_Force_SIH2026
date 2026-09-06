"""Screening route endpoint for SIH26188.

Executes the end-to-end identity screening pipeline:
1. Real Google Gemini document identity and MRZ extraction.
2. Real ICAO TD3 MRZ validation (when MRZ is present).
3. Real document expiry validation.
4. Real SQLite blacklist screening.
5. Real biometric face match using InsightFace / ONNX.
6. Real selfie embedding extraction (InsightFace ArcFace).
7. Real duplicate identity detection against SQLite embedding store.
8. Store/update selfie embedding in SQLite for future comparisons.
9. Real explainable rule-based risk-scoring engine.
"""

import os
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
from app.services.document_extractor import extract_document
from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
from app.services.expiry_validator import validate_expiry
from app.services.face_matcher import compare_faces, extract_selfie_embedding
from app.services.mrz_validator import validate_td3_mrz
from app.services.risk_engine import calculate_risk
from app.services.tamper_detector import detect_tampering

router = APIRouter()


@router.post(
    "/screen",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
    summary="Screen Document and Selfie",
    description=(
        "Accepts identity document and selfie uploads, executing real Gemini document "
        "extraction, real MRZ verification, real expiry check, real blacklist check, "
        "real biometric face comparison, real duplicate identity detection, "
        "and explainable risk scoring adhering strictly to the API contract."
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
    """Execute identity and document screening pipeline."""
    # 1. Ingest document image bytes for extraction
    document_bytes = await document_image.read()
    mime_type = document_image.content_type or "image/jpeg"

    # 1b. Ingest selfie bytes for face comparison and embedding
    selfie_bytes = await selfie_image.read()
    selfie_mime_type = selfie_image.content_type or "image/jpeg"

    # 2. REAL Structured Document Extraction using Google Gemini API
    extraction_result = extract_document(image_bytes=document_bytes, mime_type=mime_type)
    doc_info = extraction_result.get("document", {})

    extracted_doc_number = doc_info.get("document_number")
    # Development override allows testing synthetic blacklist triggers in demo mode
    demo_enabled = os.getenv("DEMO_MODE", "true").strip().lower() in ("true", "1", "yes", "on")
    active_doc_number = (
        doc_number_override.strip().upper()
        if (doc_number_override and demo_enabled)
        else extracted_doc_number
    )

    # 3. REAL MRZ Validation (TD3 format if present)
    mrz_1 = extraction_result.get("mrz_line_1")
    mrz_2 = extraction_result.get("mrz_line_2")

    if mrz_1 and mrz_2 and len(mrz_1) == 44 and len(mrz_2) == 44:
        mrz_validation = validate_td3_mrz(mrz_1, mrz_2)
        mrz_check = MRZCheckResult(
            status=CheckStatus(mrz_validation["status"]),
            score=mrz_validation["score"],
            reason=mrz_validation["reason"],
            details=mrz_validation.get("details"),
        )
    else:
        # Non-passport documents (e.g. college IDs) or unreadable MRZ
        mrz_check = MRZCheckResult(
            status=CheckStatus.NOT_AVAILABLE,
            score=0,
            reason="MRZ is not present or could not be extracted from this document",
            details=None,
        )

    # 4. REAL Document Expiry Validation
    expiry_res = validate_expiry(doc_info.get("expiry_date"))
    expiry_check = ExpiryCheckResult(
        status=CheckStatus(expiry_res["status"]),
        score=expiry_res["score"],
        reason=expiry_res["reason"],
    )

    # 5. REAL SQLite Blacklist Screening
    blacklist_res = check_blacklist(
        document_number=active_doc_number,
        full_name=doc_info.get("full_name"),
        nationality=doc_info.get("nationality"),
        date_of_birth=doc_info.get("date_of_birth"),
    )
    blacklist_check = BlacklistCheckResult(
        status=CheckStatus(blacklist_res["status"]),
        reason=blacklist_res["reason"],
        match=blacklist_res.get("match"),
    )

    # 6. REAL Biometric Face Comparison
    face_res = compare_faces(
        document_image_bytes=document_bytes,
        document_mime_type=mime_type,
        selfie_image_bytes=selfie_bytes,
        selfie_mime_type=selfie_mime_type,
    )
    face_check = FaceMatchCheckResult(
        status=CheckStatus(face_res["status"]),
        similarity=face_res.get("similarity"),
        reason=face_res["reason"],
    )

    # 7. Extract selfie embedding for duplicate identity check
    selfie_embedding = extract_selfie_embedding(
        selfie_image_bytes=selfie_bytes,
        selfie_mime_type=selfie_mime_type,
    )

    # 8. REAL Duplicate Identity Detection
    dup_res = check_duplicate_identity(
        document_number=active_doc_number,
        full_name=doc_info.get("full_name"),
        embedding=selfie_embedding,
    )
    duplicate_check = DuplicateIdentityCheckResult(
        status=CheckStatus(dup_res["status"]),
        similar_identity=dup_res.get("similar_identity"),
        reason=dup_res["reason"],
    )

    # 9. Store/update embedding after lookup (so lookup uses pre-existing data)
    if active_doc_number and selfie_embedding is not None:
        store_embedding(
            document_number=active_doc_number,
            full_name=doc_info.get("full_name"),
            embedding=selfie_embedding,
        )

    # 10. REAL Layered Document Tamper & Integrity Screening
    tamper_res = detect_tampering(
        image_bytes=document_bytes,
        mime_type=mime_type,
        extracted_data=doc_info,
        mrz_lines=(mrz_1, mrz_2) if (mrz_1 and mrz_2) else None,
    )
    tamper_check = TamperCheckResult(
        status=CheckStatus(tamper_res["status"]),
        risk=tamper_res.get("risk"),
        reason=tamper_res["reason"],
        recommendation=tamper_res.get("recommendation"),
        confidence=tamper_res.get("confidence"),
        document_quality=tamper_res.get("document_quality"),
        sub_checks=tamper_res.get("sub_checks"),
        field_analysis=tamper_res.get("field_analysis"),
        highlighted_regions=tamper_res.get("highlighted_regions"),
        cross_field_consistency=tamper_res.get("cross_field_consistency"),
        ai_manipulation=tamper_res.get("ai_manipulation"),
    )

    # 11. Assemble checks container
    checks = ChecksContainer(
        mrz=mrz_check,
        expiry=expiry_check,
        tamper=tamper_check,
        face_match=face_check,
        duplicate_identity=duplicate_check,
        blacklist=blacklist_check,
    )

    # 11. REAL Explainable Risk Engine
    risk_evaluation = calculate_risk(checks)

    # 12. Return formal ScreeningResponse
    return ScreeningResponse(
        screening_id="SCR-2026-0001",
        document=DocumentExtractedData(
            document_type=doc_info.get("document_type"),
            full_name=doc_info.get("full_name"),
            document_number=active_doc_number,
            nationality=doc_info.get("nationality"),
            date_of_birth=doc_info.get("date_of_birth"),
            expiry_date=doc_info.get("expiry_date"),
            sex=doc_info.get("sex"),
        ),
        checks=checks,
        risk=RiskAssessment(
            score=risk_evaluation["score"],
            level=RiskLevel(risk_evaluation["level"]),
        ),
        explanations=risk_evaluation["explanations"],
    )
