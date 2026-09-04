"""Service layer package for business logic and screening modules."""

from app.services.blacklist_checker import check_blacklist
from app.services.document_extractor import extract_document
from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
from app.services.expiry_validator import validate_expiry
from app.services.face_matcher import compare_faces, extract_selfie_embedding
from app.services.mrz_validator import compute_mrz_check_digit, validate_td3_mrz
from app.services.risk_engine import calculate_risk
from app.services.tamper_detector import detect_tampering

__all__ = [
    "calculate_risk",
    "check_blacklist",
    "check_duplicate_identity",
    "compare_faces",
    "compute_mrz_check_digit",
    "detect_tampering",
    "extract_document",
    "extract_selfie_embedding",
    "store_embedding",
    "validate_expiry",
    "validate_td3_mrz",
]
