"""Unit tests for Gemini document extraction service.

All Gemini API calls are strictly mocked. Zero API credits are consumed during testing.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from app.services.document_extractor import extract_document


class MockResponse:
    """Mock Gemini response containing a JSON text attribute."""

    def __init__(self, text: str):
        self.text = text


def create_mock_client(response_dict: dict = None, raw_text: str = None, error: Exception = None):
    """Helper to create a mock google-genai Client."""
    mock_client = MagicMock()
    if error:
        mock_client.models.generate_content.side_effect = error
    else:
        text = raw_text if raw_text is not None else json.dumps(response_dict or {})
        mock_client.models.generate_content.return_value = MockResponse(text)
    return mock_client


def test_passport_structured_response():
    """Passport with full fields and MRZ lines extracts correctly."""
    passport_data = {
        "document_type": "passport",
        "full_name": "SARAH JANE CONNOR",
        "document_number": "A1234567",
        "nationality": "USA",
        "date_of_birth": "1965-02-28",
        "expiry_date": "2030-05-15",
        "sex": "F",
        "issuing_authority": "US Department of State",
        "institution_or_organization": None,
        "mrz_line_1": "P<USACONNOR<<SARAH<JANE<<<<<<<<<<<<<<<<<<<<<",
        "mrz_line_2": "A1234567<5USA6502288F3005152<<<<<<<<<<<<<<<4",
    }
    client = create_mock_client(response_dict=passport_data)
    result = extract_document(b"fake_image_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is True
    doc = result["document"]
    assert doc["document_type"] == "passport"
    assert doc["full_name"] == "SARAH JANE CONNOR"
    assert doc["document_number"] == "A1234567"
    assert doc["nationality"] == "USA"
    assert doc["date_of_birth"] == "1965-02-28"
    assert doc["expiry_date"] == "2030-05-15"
    assert doc["sex"] == "F"
    assert result["mrz_line_1"] == "P<USACONNOR<<SARAH<JANE<<<<<<<<<<<<<<<<<<<<<"
    assert result["mrz_line_2"] == "A1234567<5USA6502288F3005152<<<<<<<<<<<<<<<4"
    assert len(result["warnings"]) == 0


def test_student_college_id_structured_response():
    """Student/college ID extracts generic fields without passport requirements."""
    student_data = {
        "document_type": "student_id",
        "full_name": "KARTHIKEYAN MARAN",
        "document_number": "REG-2026-99",
        "nationality": None,
        "date_of_birth": "2005-08-14",
        "expiry_date": None,
        "sex": None,
        "issuing_authority": None,
        "institution_or_organization": "R.M.D. Engineering College",
        "mrz_line_1": None,
        "mrz_line_2": None,
    }
    client = create_mock_client(response_dict=student_data)
    result = extract_document(b"fake_id_bytes", mime_type="image/png", client=client)

    assert result["success"] is True
    doc = result["document"]
    assert doc["document_type"] == "student_id"
    assert doc["full_name"] == "KARTHIKEYAN MARAN"
    assert doc["document_number"] == "REG-2026-99"
    assert doc["nationality"] is None
    assert doc["date_of_birth"] == "2005-08-14"
    assert doc["expiry_date"] is None
    assert doc["institution_or_organization"] == "R.M.D. Engineering College"
    assert result["mrz_line_1"] is None
    assert result["mrz_line_2"] is None
    assert "MRZ not present on this document" in result["warnings"]


def test_national_id_response():
    """National identity card maps to national_id taxonomy correctly."""
    national_id_data = {
        "document_type": "national_identity_card",
        "full_name": "MOHAMMED AL-MANSOOR",
        "document_number": "784-1992-1234567-1",
        "nationality": "ARE",
        "date_of_birth": "1992-04-10",
        "expiry_date": "2032-04-09",
        "sex": "M",
        "issuing_authority": "Federal Authority for Identity and Citizenship",
        "institution_or_organization": None,
        "mrz_line_1": None,
        "mrz_line_2": None,
    }
    client = create_mock_client(response_dict=national_id_data)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is True
    assert result["document"]["document_type"] == "national_id"
    assert result["document"]["document_number"] == "784-1992-1234567-1"


def test_missing_optional_fields_return_null():
    """Omitted or null fields in the Gemini response safely map to null/None."""
    minimal_data = {
        "document_type": "unknown",
        "full_name": "JANE DOE",
        "document_number": None,
        "nationality": None,
        "date_of_birth": None,
        "expiry_date": None,
        "sex": None,
        "issuing_authority": None,
        "institution_or_organization": None,
        "mrz_line_1": None,
        "mrz_line_2": None,
    }
    client = create_mock_client(response_dict=minimal_data)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is True
    doc = result["document"]
    assert doc["full_name"] == "JANE DOE"
    assert doc["document_number"] is None
    assert doc["nationality"] is None
    assert doc["date_of_birth"] is None
    assert doc["expiry_date"] is None
    assert doc["sex"] is None


def test_document_with_no_mrz():
    """Document lacking MRZ lines returns None for lines and a warning."""
    data = {
        "document_type": "employee_id",
        "full_name": "ALEX RIVERA",
        "document_number": "EMP-456",
        "mrz_line_1": None,
        "mrz_line_2": None,
    }
    client = create_mock_client(response_dict=data)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is True
    assert result["mrz_line_1"] is None
    assert result["mrz_line_2"] is None
    assert any("MRZ not present" in w for w in result["warnings"])


def test_malformed_gemini_output():
    """Non-JSON or corrupted response from Gemini returns empty failure object."""
    client = create_mock_client(raw_text="This is not valid JSON at all")
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is False
    assert result["document"]["full_name"] is None
    assert any("Failed to parse Gemini JSON output" in w for w in result["warnings"])


def test_gemini_api_failure():
    """API exception during generate_content returns graceful failure object."""
    client = create_mock_client(error=RuntimeError("Quota exceeded or connection error"))
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is False
    assert result["document"]["full_name"] is None
    assert any("Gemini extraction API call failed" in w for w in result["warnings"])


def test_missing_gemini_api_key_without_injected_client(monkeypatch):
    """Missing GEMINI_API_KEY environment variable fails gracefully."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=None)

    assert result["success"] is False
    assert result["document"]["full_name"] is None
    assert any("GEMINI_API_KEY environment variable is not configured" in w for w in result["warnings"])


def test_unsupported_mime_type():
    """Unsupported MIME type (e.g. PDF or BMP) is rejected immediately."""
    result = extract_document(b"fake_pdf_bytes", mime_type="application/pdf")

    assert result["success"] is False
    assert any("Unsupported MIME type" in w for w in result["warnings"])


def test_mrz_preserved_exactly():
    """Exact 44-character MRZ lines are preserved accurately."""
    mrz_1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    mrz_2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    data = {
        "document_type": "passport",
        "full_name": "ANNA MARIA ERIKSSON",
        "document_number": "L898902C3",
        "mrz_line_1": mrz_1,
        "mrz_line_2": mrz_2,
    }
    client = create_mock_client(response_dict=data)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["mrz_line_1"] == mrz_1
    assert result["mrz_line_2"] == mrz_2


def test_no_fallback_to_arun_kumar():
    """Extraction failure must never fall back to ARUN KUMAR or demo data."""
    client = create_mock_client(error=Exception("Network error"))
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is False
    assert result["document"]["full_name"] != "ARUN KUMAR"
    assert result["document"]["full_name"] is None
    assert result["document"]["document_number"] is None


def test_unknown_document_type_handled_safely():
    """Unrecognized document types default safely to 'unknown'."""
    data = {
        "document_type": "superhero_membership_badge",
        "full_name": "CLARK KENT",
    }
    client = create_mock_client(response_dict=data)
    result = extract_document(b"fake_bytes", mime_type="image/jpeg", client=client)

    assert result["success"] is True
    assert result["document"]["document_type"] == "unknown"
