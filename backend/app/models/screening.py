"""Screening models and schema definitions for SIH26188."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(str, Enum):
    """Permitted status values for individual pipeline checks."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class RiskLevel(str, Enum):
    """Permitted risk classification levels."""
    LOW = "LOW"
    REVIEW = "REVIEW"
    HIGH = "HIGH"


class DocumentExtractedData(BaseModel):
    """Document fields extracted via OCR / MRZ parsers.
    
    Fields may be null if extraction fails. Values must not be fabricated.
    """
    model_config = ConfigDict(extra="ignore")

    document_type: Optional[str] = None
    full_name: Optional[str] = None
    document_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    expiry_date: Optional[str] = None
    sex: Optional[str] = None


class MRZCheckResult(BaseModel):
    """Result of Machine Readable Zone validation."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    score: Optional[Union[int, float]] = None
    reason: str
    details: Optional[Dict[str, bool]] = None


class ExpiryCheckResult(BaseModel):
    """Result of document expiration and validity checks."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    score: Optional[Union[int, float]] = None
    reason: str


class TamperCheckResult(BaseModel):
    """Result of document tamper, forgery, and integrity screening."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    risk: Optional[Union[int, float]] = None
    reason: str
    recommendation: Optional[str] = None
    confidence: Optional[str] = None
    document_quality: Optional[Dict[str, Any]] = None
    sub_checks: Optional[Dict[str, Any]] = None
    field_analysis: Optional[List[Dict[str, Any]]] = None
    highlighted_regions: Optional[List[Dict[str, Any]]] = None
    cross_field_consistency: Optional[Dict[str, Any]] = None
    ai_manipulation: Optional[Dict[str, Any]] = None


class FaceMatchCheckResult(BaseModel):
    """Result of biometric face comparison between document and selfie."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    similarity: Optional[float] = None
    reason: str


class DuplicateIdentityCheckResult(BaseModel):
    """Result of duplicate identity screening against historic records."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    similar_identity: Optional[Union[str, dict, Any]] = None
    reason: str


class BlacklistCheckResult(BaseModel):
    """Result of watchlist/blacklist cross-referencing."""
    model_config = ConfigDict(extra="ignore")

    status: CheckStatus
    reason: str
    match: Optional[Dict[str, Any]] = None


class ChecksContainer(BaseModel):
    """Aggregated checks container containing all pipeline check outcomes."""
    model_config = ConfigDict(extra="ignore")

    mrz: MRZCheckResult
    expiry: ExpiryCheckResult
    tamper: TamperCheckResult
    face_match: FaceMatchCheckResult
    duplicate_identity: DuplicateIdentityCheckResult
    blacklist: BlacklistCheckResult


class RiskAssessment(BaseModel):
    """Unified risk evaluation assessment."""
    model_config = ConfigDict(extra="ignore")

    score: int = Field(..., ge=0, le=100, description="Risk score as an integer between 0 and 100 inclusive")
    level: RiskLevel


class ScreeningResponse(BaseModel):
    """Full API response contract for POST /api/screen."""
    model_config = ConfigDict(extra="ignore")

    screening_id: str
    document: DocumentExtractedData
    checks: ChecksContainer
    risk: RiskAssessment
    explanations: List[str]
