"""Document integrity and analysis subpackage."""

from .quality_assessor import assess_image_quality
from .field_detector import detect_document_regions, DocumentFieldRegion
from .image_forensics import analyze_local_field_forensics, analyze_copy_move_cloning
from .typography import analyze_typography_consistency
from .qr_validator import detect_and_decode_qr
from .mrz_parser import parse_td3_mrz, parse_td3_name
from .cross_validator import cross_validate_fields
from .ai_manipulation import detect_ai_manipulation
from .integrity_engine import run_document_integrity_pipeline

__all__ = [
    "assess_image_quality",
    "detect_document_regions",
    "DocumentFieldRegion",
    "analyze_local_field_forensics",
    "analyze_copy_move_cloning",
    "analyze_typography_consistency",
    "detect_and_decode_qr",
    "parse_td3_mrz",
    "parse_td3_name",
    "cross_validate_fields",
    "detect_ai_manipulation",
    "run_document_integrity_pipeline",
]
