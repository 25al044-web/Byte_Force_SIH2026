"""Verification script for the Jury Acceptance Test.

Version A: Genuine passport with holder 'ARUN KUMAR' matching MRZ.
Version B: Cleanly altered Name field 'RAHUL SHARMA' with untouched MRZ 'ARUN KUMAR'.

Verifies:
1. Version A returns Low Risk / CLEAR.
2. Version B is reliably flagged as FAIL / High Risk with explainable cross-field and typography reasons.
"""

import io
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure backend in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from app.main import app
from tests.test_document_integrity_redteam import _build_synthetic_passport_image

client = TestClient(app)

def run_acceptance_test():
    print("=" * 80)
    print("RUNNING JURY TEST SCENARIO: VERSION A vs VERSION B")
    print("=" * 80)

    # 1. Prepare images
    doc_a = _build_synthetic_passport_image(name="ARUN KUMAR", ai_text_overlay=False)
    doc_b = _build_synthetic_passport_image(name="RAHUL SHARMA", ai_text_overlay=True)
    selfie_bytes = _build_synthetic_passport_image()

    mock_gemini_a = {
        "success": True,
        "document": {
            "document_type": "passport",
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "nationality": "IND",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
            "sex": "M",
            "issuing_authority": None,
            "institution_or_organization": None,
        },
        "mrz_line_1": "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "mrz_line_2": "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        "warnings": [],
    }

    mock_gemini_b = {
        "success": True,
        "document": {
            "document_type": "passport",
            "full_name": "RAHUL SHARMA",  # Altered visual name!
            "document_number": "P1234567",
            "nationality": "IND",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
            "sex": "M",
            "issuing_authority": None,
            "institution_or_organization": None,
        },
        "mrz_line_1": "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "mrz_line_2": "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        "warnings": [],
    }

    # Execute Version A (Original)
    files_a = {
        "document_image": ("doc_a.jpg", io.BytesIO(doc_a), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(selfie_bytes), "image/jpeg"),
    }
    with patch("app.routes.screening.extract_document", return_value=mock_gemini_a), \
         patch("app.routes.screening.compare_faces", return_value={"status": "PASS", "similarity": 94.2, "reason": "Selfie matches portrait"}), \
         patch("app.routes.screening.check_duplicate_identity", return_value={"status": "PASS", "similar_identity": None, "reason": "No duplicate"}), \
         patch("app.routes.screening.extract_selfie_embedding", return_value=[0.1] * 512), \
         patch("app.routes.screening.store_embedding", return_value=True):
        res_a = client.post("/api/screen", files=files_a)

    assert res_a.status_code == 200
    data_a = res_a.json()

    print("\n[+] VERSION A (ORIGINAL DOCUMENT):")
    print(f"    Document Extracted Name : {data_a['document']['full_name']}")
    print(f"    Tamper Integrity Status : {data_a['checks']['tamper']['status']}")
    print(f"    Tamper Forensic Risk    : {data_a['checks']['tamper']['risk']}/100")
    print(f"    Recommendation          : {data_a['checks']['tamper']['recommendation']}")
    print(f"    Overall Screening Risk  : {data_a['risk']['score']}/100 ({data_a['risk']['level']})")
    print(f"    Explanations            : {data_a['explanations']}")

    # Execute Version B (Altered Name)
    files_b = {
        "document_image": ("doc_b.jpg", io.BytesIO(doc_b), "image/jpeg"),
        "selfie_image": ("selfie.jpg", io.BytesIO(selfie_bytes), "image/jpeg"),
    }
    with patch("app.routes.screening.extract_document", return_value=mock_gemini_b), \
         patch("app.routes.screening.compare_faces", return_value={"status": "PASS", "similarity": 94.2, "reason": "Selfie matches portrait"}), \
         patch("app.routes.screening.check_duplicate_identity", return_value={"status": "PASS", "similar_identity": None, "reason": "No duplicate"}), \
         patch("app.routes.screening.extract_selfie_embedding", return_value=[0.1] * 512), \
         patch("app.routes.screening.store_embedding", return_value=True):
        res_b = client.post("/api/screen", files=files_b)

    assert res_b.status_code == 200
    data_b = res_b.json()

    print("\n[+] VERSION B (CLEAN AI-EDITED NAME):")
    print(f"    Document Extracted Name : {data_b['document']['full_name']}")
    print(f"    Tamper Integrity Status : {data_b['checks']['tamper']['status']}")
    print(f"    Tamper Forensic Risk    : {data_b['checks']['tamper']['risk']}/100")
    print(f"    Recommendation          : {data_b['checks']['tamper']['recommendation']}")
    print(f"    Overall Screening Risk  : {data_b['risk']['score']}/100 ({data_b['risk']['level']})")
    print(f"    Reason                  : {data_b['checks']['tamper']['reason']}")

    # Highlighted regions
    print("\n[+] HIGHLIGHTED REGIONS ON VERSION B:")
    for region in data_b['checks']['tamper']['highlighted_regions']:
        if region['severity'] in ('warning', 'suspicious'):
            print(f"    -> Field: {region['label']} | Severity: {region['severity'].upper()} | Risk: {region['risk_score']} | Reason: {region['reason']}")

    # Assertions
    assert data_a['checks']['tamper']['status'] == "PASS"
    assert data_a['checks']['tamper']['risk'] < 25
    assert data_a['checks']['tamper']['recommendation'] == "CLEAR"

    assert data_b['checks']['tamper']['status'] == "FAIL"
    assert data_b['checks']['tamper']['risk'] >= 75
    assert data_b['checks']['tamper']['recommendation'] == "SECONDARY_INSPECTION_RECOMMENDED"
    assert data_b['risk']['level'] == "HIGH"

    print("\n" + "=" * 80)
    print("SUCCESS: JURY TEST SCENARIO IS 100% RESOLVED AND VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    run_acceptance_test()
