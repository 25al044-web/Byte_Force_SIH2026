from app.services.blockchain.audit_service import _safe_report
from app.services.blockchain.hash_service import hash_report


def _result(score=75, recommendation="SECONDARY_INSPECTION_RECOMMENDED"):
    return {"risk": {"score": score, "level": "HIGH"}, "checks": {"tamper": {"status": "WARNING", "recommendation": recommendation}, "face_match": {"status": "PASS"}}}


def test_canonical_report_hash_is_deterministic():
    report = _safe_report("SCR-TEST", b"document", b"selfie", _result())
    assert hash_report(report) == hash_report(dict(reversed(list(report.items()))))


def test_modified_report_changes_hash_and_payload_has_no_pii():
    report = _safe_report("SCR-TEST", b"document", b"selfie", _result())
    changed = _safe_report("SCR-TEST", b"document", b"selfie", _result(score=15, recommendation="CLEAR"))
    assert hash_report(report) != hash_report(changed)
    assert not {"full_name", "date_of_birth", "document_number", "embedding", "image"} & set(report)
