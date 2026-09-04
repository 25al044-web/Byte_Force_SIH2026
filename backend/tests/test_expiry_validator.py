"""Unit tests for document expiry validation service."""

from datetime import date, timedelta
import pytest
from app.services.expiry_validator import validate_expiry


@pytest.fixture
def ref_date():
    """Deterministic reference date: 2026-06-01."""
    return date(2026, 6, 1)


def test_future_expiry_more_than_180_days_returns_pass(ref_date):
    """Document expiring >180 days in the future returns PASS with score 0."""
    # 365 days in future
    future_date = (ref_date + timedelta(days=365)).isoformat()
    res = validate_expiry(future_date, reference_date=ref_date)
    assert res["status"] == "PASS"
    assert res["score"] == 0
    assert "Document is valid until" in res["reason"]


def test_expiry_within_180_days_returns_warning(ref_date):
    """Document expiring within 180 days returns WARNING with score 10."""
    # 60 days in future
    soon_date = (ref_date + timedelta(days=60)).isoformat()
    res = validate_expiry(soon_date, reference_date=ref_date)
    assert res["status"] == "WARNING"
    assert res["score"] == 10
    assert "Document is nearing expiration" in res["reason"]

    # Exactly 180 days
    boundary_date = (ref_date + timedelta(days=180)).isoformat()
    res_bound = validate_expiry(boundary_date, reference_date=ref_date)
    assert res_bound["status"] == "WARNING"
    assert res_bound["score"] == 10


def test_expired_document_returns_fail(ref_date):
    """Document whose expiry date is in the past returns FAIL with score 25."""
    past_date = (ref_date - timedelta(days=30)).isoformat()
    res = validate_expiry(past_date, reference_date=ref_date)
    assert res["status"] == "FAIL"
    assert res["score"] == 25
    assert "Document expired on" in res["reason"]


def test_missing_expiry_date_returns_not_available(ref_date):
    """Missing, None, or empty expiry date returns NOT_AVAILABLE safely."""
    res_none = validate_expiry(None, reference_date=ref_date)
    assert res_none["status"] == "NOT_AVAILABLE"
    assert res_none["score"] == 0
    assert "unavailable" in res_none["reason"]

    res_empty = validate_expiry("", reference_date=ref_date)
    assert res_empty["status"] == "NOT_AVAILABLE"

    res_null_str = validate_expiry("null", reference_date=ref_date)
    assert res_null_str["status"] == "NOT_AVAILABLE"


def test_malformed_expiry_date_returns_not_available(ref_date):
    """Malformed or non-date string returns NOT_AVAILABLE without crashing."""
    res = validate_expiry("invalid-date-string", reference_date=ref_date)
    assert res["status"] == "NOT_AVAILABLE"
    assert res["score"] == 0
    assert "invalid or unparseable" in res["reason"]
