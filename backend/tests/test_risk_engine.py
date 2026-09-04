"""Unit tests for the explainable rule-based risk-scoring engine."""

import pytest
from app.services.risk_engine import calculate_risk


def make_checks(
    mrz_status="PASS",
    expiry_status="PASS",
    tamper_status="PASS",
    tamper_risk=None,
    face_status="PASS",
    face_similarity=95.0,
    duplicate_status="PASS",
    blacklist_status="PASS",
):
    """Helper to generate checks dictionaries with customizable values."""
    return {
        "mrz": {"status": mrz_status, "score": 0, "reason": "OK"},
        "expiry": {"status": expiry_status, "score": 0, "reason": "OK"},
        "tamper": {"status": tamper_status, "risk": tamper_risk, "reason": "OK"},
        "face_match": {"status": face_status, "similarity": face_similarity, "reason": "OK"},
        "duplicate_identity": {"status": duplicate_status, "similar_identity": None, "reason": "OK"},
        "blacklist": {"status": blacklist_status, "reason": "OK"},
    }


def test_all_checks_pass():
    """All checks passing with high similarity should yield a score of 0 and LOW risk."""
    checks = make_checks(
        mrz_status="PASS",
        expiry_status="PASS",
        tamper_status="PASS",
        tamper_risk=10,
        face_status="PASS",
        face_similarity=95.0,
        duplicate_status="PASS",
        blacklist_status="PASS",
    )
    result = calculate_risk(checks)
    assert result["score"] == 0
    assert result["level"] == "LOW"
    assert result["contributions"]["mrz"] == 0
    assert result["contributions"]["expiry"] == 0
    assert result["contributions"]["tamper"] == 0
    assert result["contributions"]["face_match"] == 0
    assert result["contributions"]["duplicate_identity"] == 0
    assert result["contributions"]["blacklist"] == 0
    assert len(result["explanations"]) >= 6


def test_mrz_fail_increases_risk():
    """MRZ validation failure adds +25 risk."""
    checks = make_checks(mrz_status="FAIL", face_similarity=90.0)
    result = calculate_risk(checks)
    assert result["score"] == 25
    assert result["level"] == "LOW"  # 25 is within LOW (0-29)
    assert result["contributions"]["mrz"] == 25
    assert any("MRZ validation failed" in exp for exp in result["explanations"])


def test_expired_document_increases_risk():
    """Expired document adds +25 risk."""
    checks = make_checks(expiry_status="FAIL", face_similarity=90.0)
    result = calculate_risk(checks)
    assert result["score"] == 25
    assert result["level"] == "LOW"
    assert result["contributions"]["expiry"] == 25
    assert any("Document is expired" in exp for exp in result["explanations"])


def test_low_face_similarity_increases_risk():
    """Low face similarity increases risk according to defined brackets."""
    # 70-84.99 -> +10
    res_75 = calculate_risk(make_checks(face_similarity=75.0))
    assert res_75["contributions"]["face_match"] == 10
    assert any("Face similarity of 75.0% increased risk by 10" in exp for exp in res_75["explanations"])

    # 50-69.99 -> +25
    res_60 = calculate_risk(make_checks(face_similarity=60.0))
    assert res_60["contributions"]["face_match"] == 25
    assert any("Face similarity of 60.0% increased risk by 25" in exp for exp in res_60["explanations"])

    # < 50 -> +40
    res_35 = calculate_risk(make_checks(face_similarity=35.0))
    assert res_35["contributions"]["face_match"] == 40
    assert any("Face similarity of 35.0% increased risk by 40" in exp for exp in res_35["explanations"])


def test_face_fail_and_mrz_fail_critical_override():
    """Concurrent face FAIL and MRZ FAIL must trigger minimum risk 80 override."""
    # Base: MRZ fail (+25), Face fail (+40), rest pass (+0) -> 65.
    # Override should bump to 80.
    checks = make_checks(
        mrz_status="FAIL",
        face_status="FAIL",
        face_similarity=45.0,  # similarity 40, status 40 -> max(40,40)=40
    )
    result = calculate_risk(checks)
    assert result["score"] == 80
    assert result["level"] == "HIGH"
    assert any("critical risk threshold (80)" in exp for exp in result["explanations"])


def test_blacklist_fail_critical_override():
    """Blacklist FAIL must trigger minimum risk 85 override."""
    # Base: Blacklist fail (+70), rest pass (+0) -> 70.
    # Override should bump to 85.
    checks = make_checks(blacklist_status="FAIL")
    result = calculate_risk(checks)
    assert result["score"] == 85
    assert result["level"] == "HIGH"
    assert any("minimum high-risk threshold (85)" in exp for exp in result["explanations"])


def test_duplicate_identity_fail_critical_override():
    """Duplicate identity FAIL must trigger minimum risk 75 override."""
    # Base: Duplicate fail (+45), rest pass (+0) -> 45.
    # Override should bump to 75.
    checks = make_checks(duplicate_status="FAIL")
    result = calculate_risk(checks)
    assert result["score"] == 75
    assert result["level"] == "HIGH"
    assert any("minimum risk threshold (75)" in exp for exp in result["explanations"])


def test_high_tamper_risk():
    """Tamper risk value should scale correctly into risk score."""
    # tamper risk 32 -> bracket 20-39 -> +10
    res_32 = calculate_risk(make_checks(tamper_risk=32))
    assert res_32["contributions"]["tamper"] == 10

    # tamper risk 55 -> bracket 40-59 -> +20
    res_55 = calculate_risk(make_checks(tamper_risk=55))
    assert res_55["contributions"]["tamper"] == 20

    # tamper risk 72 -> bracket 60-79 -> +30
    res_72 = calculate_risk(make_checks(tamper_risk=72))
    assert res_72["contributions"]["tamper"] == 30

    # tamper risk 92 -> bracket 80-100 -> +40
    res_92 = calculate_risk(make_checks(tamper_risk=92))
    assert res_92["contributions"]["tamper"] == 40


def test_tamper_fallback_without_risk_score():
    """Tamper checks without numeric risk score use status fallbacks."""
    # FAIL without risk -> +30
    res_fail = calculate_risk(make_checks(tamper_status="FAIL", tamper_risk=None))
    assert res_fail["contributions"]["tamper"] == 30

    # WARNING without risk -> +15
    res_warn = calculate_risk(make_checks(tamper_status="WARNING", tamper_risk=None))
    assert res_warn["contributions"]["tamper"] == 15

    # PASS without risk -> +0
    res_pass = calculate_risk(make_checks(tamper_status="PASS", tamper_risk=None))
    assert res_pass["contributions"]["tamper"] == 0


def test_not_available_checks_handled_safely():
    """Checks with NOT_AVAILABLE status should contribute baseline default risk and not crash."""
    checks = {
        "mrz": {"status": "NOT_AVAILABLE"},
        "expiry": {"status": "NOT_AVAILABLE"},
        "tamper": {"status": "NOT_AVAILABLE"},
        "face_match": {"status": "NOT_AVAILABLE"},
        "duplicate_identity": {"status": "NOT_AVAILABLE"},
        "blacklist": {"status": "NOT_AVAILABLE"},
    }
    result = calculate_risk(checks)
    # Sum: MRZ(5) + Expiry(5) + Tamper(5) + Face(10) + Dup(5) + Blacklist(10) = 40
    assert result["score"] == 40
    assert result["level"] == "REVIEW"
    assert all("not available" in exp for exp in result["explanations"])


def test_empty_checks_handled_safely():
    """Completely empty checks input should default gracefully without crashing."""
    result = calculate_risk({})
    assert result["score"] == 40
    assert result["level"] == "REVIEW"

    result_none = calculate_risk(None)
    assert result_none["score"] == 40
    assert result_none["level"] == "REVIEW"


def test_score_clamping_upper_limit():
    """Multiple critical failures must be clamped to 100 maximum."""
    checks = make_checks(
        mrz_status="FAIL",             # +25
        expiry_status="FAIL",          # +25
        tamper_risk=95,                # +40
        face_status="FAIL",            # +40
        face_similarity=20.0,
        duplicate_status="FAIL",       # +45
        blacklist_status="FAIL",       # +70
    )
    result = calculate_risk(checks)
    assert result["score"] == 100
    assert result["level"] == "HIGH"


def test_score_clamping_lower_limit():
    """Risk score must never be negative."""
    checks = make_checks(face_similarity=100.0)
    result = calculate_risk(checks)
    assert result["score"] >= 0


def test_risk_level_mapping_low():
    """Score 0-29 maps to LOW."""
    res_0 = calculate_risk(make_checks(face_similarity=95.0))
    assert res_0["score"] == 0
    assert res_0["level"] == "LOW"

    # Score 20: Tamper risk 50 (+20)
    res_20 = calculate_risk(make_checks(tamper_risk=50, face_similarity=95.0))
    assert res_20["score"] == 20
    assert res_20["level"] == "LOW"


def test_risk_level_mapping_review():
    """Score 30-59 maps to REVIEW."""
    # Tamper risk 50 (+20) + Expiry warning (+10) = 30
    res_30 = calculate_risk(make_checks(tamper_risk=50, expiry_status="WARNING", face_similarity=95.0))
    assert res_30["score"] == 30
    assert res_30["level"] == "REVIEW"

    # Expiry fail (+25) + Face similarity 60 (+25) = 50
    res_50 = calculate_risk(make_checks(expiry_status="FAIL", face_similarity=60.0))
    assert res_50["score"] == 50
    assert res_50["level"] == "REVIEW"


def test_risk_level_mapping_high():
    """Score 60-100 maps to HIGH."""
    # Expiry fail (+25) + Tamper fail (+30) + Face similarity 80 (+10) = 65
    res_65 = calculate_risk(make_checks(expiry_status="FAIL", tamper_status="FAIL", face_similarity=80.0))
    assert res_65["score"] == 65
    assert res_65["level"] == "HIGH"


def test_human_readable_explanations():
    """Explanations list contains clean, non-empty, descriptive strings."""
    checks = make_checks(
        mrz_status="PASS",
        expiry_status="FAIL",
        tamper_risk=32,
        face_status="PASS",
        face_similarity=91.7,
        duplicate_status="PASS",
        blacklist_status="PASS",
    )
    result = calculate_risk(checks)
    assert isinstance(result["explanations"], list)
    assert len(result["explanations"]) == 6
    for exp in result["explanations"]:
        assert isinstance(exp, str)
        assert len(exp.strip()) > 0
