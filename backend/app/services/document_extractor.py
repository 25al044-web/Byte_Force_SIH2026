"""Structured document extraction service using Google Gemini API.

Extracts identity information from generic identity document images (passports,
visas, national IDs, employee IDs, student/college IDs, driving licences, etc.).
Uses the official google-genai SDK with structured output enforcement.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Ensure .env is loaded from backend/.env or repo root
_env_backend = Path(__file__).resolve().parent.parent.parent / ".env"
_env_root = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_backend.exists():
    load_dotenv(_env_backend)
elif _env_root.exists():
    load_dotenv(_env_root)

# Google GenAI SDK
from google import genai
from google.genai import types

SUPPORTED_MIME_TYPES = ("image/jpeg", "image/png")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-3.7-flash"]

ALLOWED_DOCUMENT_TYPES = {
    "passport",
    "visa",
    "national_id",
    "employee_id",
    "student_id",
    "driving_licence",
    "residence_permit",
    "travel_document",
    "unknown",
}

DOC_TYPE_SYNONYMS = {
    "college_id": "student_id",
    "school_id": "student_id",
    "university_id": "student_id",
    "student": "student_id",
    "driver_license": "driving_licence",
    "driving_license": "driving_licence",
    "drivers_license": "driving_licence",
    "national_identity_card": "national_id",
    "id_card": "national_id",
    "work_id": "employee_id",
    "staff_id": "employee_id",
}


class ExtractedIdentitySchema(BaseModel):
    """Pydantic schema for Gemini structured JSON extraction."""

    document_type: Optional[str] = Field(
        None,
        description=(
            "Type of document. Must be one of: passport, visa, national_id, "
            "employee_id, student_id, driving_licence, residence_permit, "
            "travel_document, unknown."
        ),
    )
    full_name: Optional[str] = Field(
        None, description="Full name of document holder visibly printed on the document."
    )
    document_number: Optional[str] = Field(
        None,
        description="Official document number, roll/registration number, or unique ID string.",
    )
    nationality: Optional[str] = Field(
        None,
        description="3-letter ICAO country code (e.g., IND, USA, GBR) if clearly present, else null.",
    )
    date_of_birth: Optional[str] = Field(
        None, description="Date of birth normalized to YYYY-MM-DD if visibly present, else null."
    )
    expiry_date: Optional[str] = Field(
        None,
        description="Expiration/validity date normalized to YYYY-MM-DD if visibly present, else null.",
    )
    sex: Optional[str] = Field(
        None, description="Gender/sex visibly indicated: M, F, X, or null."
    )
    issuing_authority: Optional[str] = Field(
        None, description="Issuing country, governmental department, or authority if visible."
    )
    institution_or_organization: Optional[str] = Field(
        None,
        description="School, college, university, or corporate employer name if applicable.",
    )
    mrz_line_1: Optional[str] = Field(
        None,
        description="Exact 44-character first line of TD3 Machine Readable Zone if present, else null.",
    )
    mrz_line_2: Optional[str] = Field(
        None,
        description="Exact 44-character second line of TD3 Machine Readable Zone if present, else null.",
    )


EXTRACTION_PROMPT = """You are a high-precision border security and identity document transcription engine.
Analyze the provided image of an identity document and transcribe all visibly printed text into the requested structured format.

CRITICAL RULES:
1. Extract ONLY information that is VISIBLY PRESENT and legible in the document image.
2. DO NOT GUESS, infer, or fabricate any information. If a field is not present or illegible, return null.
3. DO NOT ASSUME the document is a passport. Generic documents such as student / college IDs, employee IDs, national IDs, and driver's licenses are valid identity documents.
4. For college / student IDs:
   - Extract the student's name into full_name.
   - Extract the roll number, registration number, or student ID into document_number.
   - Extract the college or university name into institution_or_organization.
   - If fields like nationality, expiry date, sex, or MRZ are not present, return null.
5. Normalization:
   - document_type: one of 'passport', 'visa', 'national_id', 'employee_id', 'student_id', 'driving_licence', 'residence_permit', 'travel_document', 'unknown'.
   - date_of_birth & expiry_date: format strictly as YYYY-MM-DD.
   - sex: M, F, X, or null.
   - nationality: 3-letter ICAO code if clearly identified, else null.
   - document_number: preserve exact alphanumeric string except trimming whitespace.
   - mrz_line_1 & mrz_line_2: if a Machine Readable Zone is visible, transcribe the exact 44 characters per line (A-Z, 0-9, '<'). If no MRZ exists, return null for both lines.
"""

# Simplified OpenAPI-compliant JSON Schema with nullable fields for robust Gemini structured generation
SIMPLIFIED_DOCUMENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "document_type": {
            "type": "STRING",
            "nullable": True,
            "description": "One of: passport, visa, national_id, employee_id, student_id, driving_licence, residence_permit, travel_document, unknown.",
        },
        "full_name": {
            "type": "STRING",
            "nullable": True,
            "description": "Full name of document holder visibly printed on the document.",
        },
        "document_number": {
            "type": "STRING",
            "nullable": True,
            "description": "Official document number, roll/registration number, or unique ID string.",
        },
        "nationality": {
            "type": "STRING",
            "nullable": True,
            "description": "3-letter ICAO country code (e.g. IND, USA, GBR) if clearly present, else null.",
        },
        "date_of_birth": {
            "type": "STRING",
            "nullable": True,
            "description": "Date of birth in YYYY-MM-DD format if visible, else null.",
        },
        "expiry_date": {
            "type": "STRING",
            "nullable": True,
            "description": "Expiration/validity date in YYYY-MM-DD format if visible, else null.",
        },
        "sex": {
            "type": "STRING",
            "nullable": True,
            "description": "Gender/sex visibly indicated: M, F, X, or null.",
        },
        "issuing_authority": {
            "type": "STRING",
            "nullable": True,
            "description": "Issuing country or governmental authority if visible.",
        },
        "institution_or_organization": {
            "type": "STRING",
            "nullable": True,
            "description": "School, college, university, or corporate employer name if applicable.",
        },
        "mrz_line_1": {
            "type": "STRING",
            "nullable": True,
            "description": "Exact 44-character line 1 of TD3 MRZ if present, else null.",
        },
        "mrz_line_2": {
            "type": "STRING",
            "nullable": True,
            "description": "Exact 44-character line 2 of TD3 MRZ if present, else null.",
        },
    },
}


def _normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalizes date string to YYYY-MM-DD if valid, else returns None."""
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    if cleaned.lower() in ("null", "none", "n/a", "not available"):
        return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _normalize_doc_type(doc_type: Optional[str]) -> Optional[str]:
    """Normalizes document_type string to standard taxonomy."""
    if not doc_type or not isinstance(doc_type, str):
        return "unknown"
    cleaned = doc_type.strip().lower().replace(" ", "_").replace("-", "_")
    if cleaned in ALLOWED_DOCUMENT_TYPES:
        return cleaned
    if cleaned in DOC_TYPE_SYNONYMS:
        return DOC_TYPE_SYNONYMS[cleaned]
    return "unknown"


def _normalize_mrz_line(line: Optional[str]) -> Optional[str]:
    """Normalizes MRZ line characters to uppercase A-Z, 0-9, and '<'."""
    if not line or not isinstance(line, str):
        return None
    cleaned = line.strip().upper()
    if cleaned.lower() in ("null", "none", "n/a"):
        return None
    # Validate allowable TD3 MRZ characters
    if re.fullmatch(r"[A-Z0-9<]{44}", cleaned):
        return cleaned
    # If not 44 chars or invalid chars, keep only if reasonably clean, else None
    sanitized = re.sub(r"[^A-Z0-9<]", "", cleaned)
    if len(sanitized) == 44:
        return sanitized
    return None


def _build_empty_response(warnings: List[str]) -> Dict[str, Any]:
    """Builds a safe, null-filled response dictionary when extraction fails."""
    return {
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
        "warnings": warnings,
    }


_cached_genai_client = None
_cached_genai_key = None


def _get_genai_client(api_key: str):
    global _cached_genai_client, _cached_genai_key
    if _cached_genai_client is None or _cached_genai_key != api_key:
        _cached_genai_client = genai.Client(api_key=api_key)
        _cached_genai_key = api_key
    return _cached_genai_client


def extract_document(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """Extracts structured identity data from a document image using Google Gemini API.

    Args:
        image_bytes: Raw binary bytes of the document image.
        mime_type: Image MIME type (image/jpeg or image/png).
        client: Optional injected GenAI client (for testing).

    Returns:
        Structured dictionary matching internal response specification.
    """
    # 1. Validate MIME type
    if mime_type not in SUPPORTED_MIME_TYPES:
        return _build_empty_response(
            [f"Unsupported MIME type: {mime_type}. Supported types: {', '.join(SUPPORTED_MIME_TYPES)}"]
        )

    # 2. Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key and client is None:
        return _build_empty_response(["GEMINI_API_KEY environment variable is not configured"])

    # 3. Initialize GenAI Client if not injected (uses cached singleton)
    ai_client = client
    if ai_client is None:
        try:
            ai_client = _get_genai_client(api_key)
        except Exception as exc:
            return _build_empty_response([f"Failed to initialize Gemini client: {str(exc)}"])

    # 4. Prepare and execute extraction API call
    response = None
    last_error = None
    models_to_try = [DEFAULT_MODEL] if client is not None else [DEFAULT_MODEL] + FALLBACK_MODELS

    for model_name in models_to_try:
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            response = ai_client.models.generate_content(
                model=model_name,
                contents=[image_part, EXTRACTION_PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SIMPLIFIED_DOCUMENT_SCHEMA,
                    temperature=0.0,
                ),
            )
            last_error = None
            break
        except Exception as exc:
            last_error = exc
            if client is not None:
                break
            err_str = str(exc)
            # Only try next model on transient quota exhaustion or service overload
            if (
                "503" not in err_str
                and "429" not in err_str
                and "UNAVAILABLE" not in err_str
                and "RESOURCE_EXHAUSTED" not in err_str
            ):
                break

    if last_error is not None and response is None:
        return _build_empty_response([f"Gemini extraction API call failed: {str(last_error)}"])

    # 5. Parse response JSON (check response.parsed first, fallback to response.text)
    parsed_data = None
    if hasattr(response, "parsed") and response.parsed is not None:
        if isinstance(response.parsed, dict):
            parsed_data = response.parsed
        elif isinstance(response.parsed, BaseModel):
            parsed_data = response.parsed.model_dump()
        elif hasattr(response.parsed, "__dict__"):
            parsed_data = vars(response.parsed)

    if not parsed_data:
        raw_text = response.text if hasattr(response, "text") else ""
        if not raw_text or not raw_text.strip():
            return _build_empty_response(["Gemini API returned an empty response"])

        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text)
        try:
            parsed_data = json.loads(cleaned_text)
        except Exception as exc:
            return _build_empty_response([f"Failed to parse Gemini JSON output: {str(exc)}"])

    # Validate with Pydantic model
    try:
        validated_schema = ExtractedIdentitySchema.model_validate(parsed_data)
        parsed_dict = validated_schema.model_dump()
    except Exception:
        parsed_dict = parsed_data if isinstance(parsed_data, dict) else {}

    # 6. Normalize fields
    doc_type = _normalize_doc_type(parsed_dict.get("document_type"))
    dob = _normalize_date(parsed_dict.get("date_of_birth"))
    expiry = _normalize_date(parsed_dict.get("expiry_date"))

    raw_sex = parsed_dict.get("sex")
    sex = None
    if raw_sex and isinstance(raw_sex, str):
        clean_sex = raw_sex.strip().upper()
        if clean_sex in ("M", "F", "X"):
            sex = clean_sex

    raw_nat = parsed_dict.get("nationality")
    nationality = None
    if raw_nat and isinstance(raw_nat, str):
        clean_nat = raw_nat.strip().upper()
        if len(clean_nat) == 3 and clean_nat.isalpha():
            nationality = clean_nat

    raw_doc_num = parsed_dict.get("document_number")
    document_number = (
        raw_doc_num.strip() if raw_doc_num and isinstance(raw_doc_num, str) else None
    )
    if document_number and document_number.lower() in ("null", "none", "n/a"):
        document_number = None

    raw_name = parsed_dict.get("full_name")
    full_name = raw_name.strip() if raw_name and isinstance(raw_name, str) else None
    if full_name and full_name.lower() in ("null", "none", "n/a"):
        full_name = None

    mrz_1 = _normalize_mrz_line(parsed_dict.get("mrz_line_1"))
    mrz_2 = _normalize_mrz_line(parsed_dict.get("mrz_line_2"))

    warnings = []
    if not mrz_1 or not mrz_2:
        warnings.append("MRZ not present on this document")

    return {
        "success": True,
        "document": {
            "document_type": doc_type,
            "full_name": full_name,
            "document_number": document_number,
            "nationality": nationality,
            "date_of_birth": dob,
            "expiry_date": expiry,
            "sex": sex,
            "issuing_authority": parsed_dict.get("issuing_authority"),
            "institution_or_organization": parsed_dict.get("institution_or_organization"),
        },
        "mrz_line_1": mrz_1,
        "mrz_line_2": mrz_2,
        "warnings": warnings,
    }
