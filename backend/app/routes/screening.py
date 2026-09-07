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
import uuid
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
    TrustedRegistryCheckResult,
)

import cv2

from app.services.blacklist_checker import check_blacklist
from app.services.document_extractor import extract_document
from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
from app.services.expiry_validator import validate_expiry
from app.services.face_matcher import compare_faces, extract_selfie_embedding
from app.services.mrz_validator import validate_td3_mrz
from app.services.risk_engine import calculate_risk
from app.services.tamper_detector import detect_tampering, _decode_and_sanitize_image
from app.services.trusted_registry import cross_verify_identity
import logging
from app.services.blockchain.audit_service import create_audit
from app.services.blockchain.audit_service import record_event
from app.services.case_service import save_case

logger = logging.getLogger(__name__)

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

    # Decode document image once to share across face comparison and forensic tamper analysis
    doc_bgr, doc_metadata, _ = _decode_and_sanitize_image(document_bytes, mime_type)
    doc_gray = cv2.cvtColor(doc_bgr, cv2.COLOR_BGR2GRAY) if doc_bgr is not None else None

    # 6. REAL Biometric Face Comparison (reuses pre-decoded document array)
    face_res = compare_faces(
        document_image_bytes=document_bytes,
        document_mime_type=mime_type,
        selfie_image_bytes=selfie_bytes,
        selfie_mime_type=selfie_mime_type,
        precomputed_doc_bgr=doc_bgr,
    )
    face_check = FaceMatchCheckResult(
        status=CheckStatus(face_res["status"]),
        similarity=face_res.get("similarity"),
        reason=face_res["reason"],
    )

    # 7. Extract selfie embedding for duplicate identity check (reuse if already checked)
    if face_res.get("_selfie_checked"):
        selfie_embedding = face_res.get("_selfie_embedding")
    else:
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

    # 10. REAL Layered Document Tamper & Integrity Screening (reuses pre-decoded image and grayscale)
    tamper_res = detect_tampering(
        image_bytes=document_bytes,
        mime_type=mime_type,
        extracted_data=doc_info,
        mrz_lines=(mrz_1, mrz_2) if (mrz_1 and mrz_2) else None,
        precomputed_bgr=doc_bgr,
        precomputed_metadata=doc_metadata,
        precomputed_gray=doc_gray,
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

    # 10.5 REAL Trusted Identity Registry Cross-Verification
    doc_embedding = face_res.get("_doc_embedding")
    trusted_registry_res = cross_verify_identity(
        extracted_data={
            "document_number": active_doc_number,
            "full_name": doc_info.get("full_name"),
            "date_of_birth": doc_info.get("date_of_birth"),
            "nationality": doc_info.get("nationality"),
            "document_type": doc_info.get("document_type"),
        },
        doc_embedding=doc_embedding,
        selfie_embedding=selfie_embedding,
    )
    trusted_registry_check = TrustedRegistryCheckResult(
        status=trusted_registry_res["status"],
        record_found=trusted_registry_res["record_found"],
        registry_id=trusted_registry_res.get("registry_id"),
        reason=trusted_registry_res["reason"],
        mismatches=trusted_registry_res.get("mismatches"),
        stored_record=trusted_registry_res.get("stored_record"),
        comparisons=trusted_registry_res.get("comparisons"),
        tri_face_match=trusted_registry_res.get("tri_face_match"),
        risk_level=trusted_registry_res.get("risk_level"),
    )

    # 11. Assemble checks container
    checks = ChecksContainer(
        mrz=mrz_check,
        expiry=expiry_check,
        tamper=tamper_check,
        face_match=face_check,
        duplicate_identity=duplicate_check,
        blacklist=blacklist_check,
        trusted_registry=trusted_registry_check,
    )

    # 12. REAL Explainable Risk Engine
    risk_evaluation = calculate_risk(checks)

    # 13. Build the completed result, then append the isolated fail-open audit.
    screening_id = f"SCR-2026-{uuid.uuid4().hex[:8].upper()}"
    record_event("SCREENING_CREATED", "SCREENING", screening_id, "SCREENING_CREATED", {"screening_id": screening_id})
    result_payload = {
        "risk": {"score": risk_evaluation["score"], "level": risk_evaluation["level"]},
        "checks": {
            "tamper": {"status": tamper_res["status"], "recommendation": tamper_res.get("recommendation")},
            "face_match": {"status": face_res["status"]},
            "blacklist": {"status": blacklist_res["status"]},
            "trusted_registry": {"status": trusted_registry_res["status"], "record_found": trusted_registry_res["record_found"]},
        },
    }
    blockchain_audit = create_audit(screening_id, document_bytes, selfie_bytes, result_payload)
    if blacklist_res["status"] == "FAIL":
        record_event("BLACKLIST_MATCH", "SCREENING", screening_id, "BLACKLIST_MATCH", {"screening_id": screening_id, "blacklist_status": "FAIL"})

    # Determine recommendation & main reason for case review
    recommendation = tamper_res.get("recommendation") or "MANUAL_REVIEW_RECOMMENDED"
    if trusted_registry_res["status"] == "MISMATCH":
        if recommendation != "REJECT_FRAUDULENT":
            recommendation = "SECONDARY_INSPECTION_RECOMMENDED"

    main_reason = (
        trusted_registry_res["reason"]
        if trusted_registry_res["status"] == "MISMATCH"
        else (risk_evaluation["explanations"][0] if risk_evaluation["explanations"] else (tamper_res.get("reason") or "Screening completed"))
    )

    # 14. Persist screening case for case review
    try:
        save_case(
            screening_id=screening_id,
            risk_score=risk_evaluation["score"],
            risk_level=risk_evaluation["level"],
            recommendation=recommendation,
            main_reason=main_reason,
            status=tamper_res["status"],
            extracted_identity={
                "document_type": doc_info.get("document_type"),
                "full_name": doc_info.get("full_name"),
                "document_number": active_doc_number,
                "nationality": doc_info.get("nationality"),
                "date_of_birth": doc_info.get("date_of_birth"),
                "expiry_date": doc_info.get("expiry_date"),
                "sex": doc_info.get("sex"),
            },
            detected_issues=risk_evaluation["explanations"],
            document_integrity_status=tamper_res["status"],
            face_match_status=face_res["status"],
        )
    except Exception as save_err:
        logger.warning("Failed to persist screening case: %s", save_err)

    # 15. Return formal ScreeningResponse
    return ScreeningResponse(
        screening_id=screening_id,
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
        blockchain_audit=blockchain_audit,
        trusted_registry=trusted_registry_check,
    )
