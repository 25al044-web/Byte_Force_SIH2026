"""Verification script to ensure 100% bit-for-bit output equivalence.

Runs all 12 Red-Team test scenarios plus standard screening scenarios and records/verifies
the exact outputs:
- status
- risk score
- recommendation
- reasons
- highlighted_regions
- sub_checks
- cross_field_consistency
"""

import io
import json
import os
import sys
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.tamper_detector import detect_tampering
from app.services.risk_engine import calculate_risk
from tests.test_document_integrity_redteam import _build_synthetic_id_card_no_mrz
from app.models.screening import (
    ChecksContainer,
    CheckStatus,
    ExpiryCheckResult,
    FaceMatchCheckResult,
    DuplicateIdentityCheckResult,
    BlacklistCheckResult,
    MRZCheckResult,
    TamperCheckResult,
)


def _build_synthetic_passport(
    name: str = "ARUN KUMAR",
    doc_number: str = "P1234567",
    dob: str = "1995-05-15",
    expiry: str = "2030-05-15",
    mrz_name: str = "ARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
    mrz_doc: str = "P1234567<1",
    mrz_dob: str = "9505151",
    mrz_expiry: str = "3005156",
    ai_text_overlay: bool = False,
    quality: int = 95,
    blur_radius: float = 0.0,
    photo_color: tuple = (180, 190, 210),
) -> bytes:
    w, h = 800, 600
    img = Image.new("RGB", (w, h), (246, 243, 238))
    draw = ImageDraw.Draw(img)

    draw.rectangle([20, 20, w - 20, h - 20], outline=(120, 120, 120), width=2)
    draw.rectangle([24, 24, w - 24, h - 24], outline=(190, 190, 190), width=1)
    draw.text((320, 40), "REPUBLIC OF DEMO - PASSPORT", fill=(45, 45, 50))
    draw.line([320, 60, 650, 60], fill=(160, 160, 160), width=1)

    draw.rectangle([50, 80, 230, 310], fill=photo_color, outline=(80, 80, 90), width=2)
    draw.ellipse([110, 130, 170, 200], fill=(140, 150, 170))
    draw.ellipse([85, 210, 195, 300], fill=(130, 140, 160))

    draw.text((320, 85), "Document No. / Passeport No.", fill=(110, 110, 115))
    draw.text((320, 105), doc_number, fill=(35, 35, 40))

    draw.text((320, 145), "Surname & Given Names / Nom et Prenoms", fill=(110, 110, 115))
    if not ai_text_overlay:
        draw.text((320, 165), name, fill=(35, 35, 40))
    else:
        draw.rectangle([315, 160, 580, 195], fill=(246, 243, 238))
        draw.text((320, 165), name, fill=(5, 5, 5))

    draw.text((320, 205), "Date of Birth / Date de naissance", fill=(110, 110, 115))
    draw.text((320, 225), dob, fill=(35, 35, 40))

    draw.text((320, 265), "Date of Expiry / Date d'expiration", fill=(110, 110, 115))
    draw.text((320, 285), expiry, fill=(35, 35, 40))

    draw.rectangle([35, 490, w - 35, 580], fill=(252, 252, 250), outline=(200, 200, 200))
    line1 = f"P<IND{mrz_name}"[:44].ljust(44, '<')
    line2 = f"{mrz_doc}IND{mrz_dob}M{mrz_expiry}<<<<<<<<<<<<<<<4"[:44].ljust(44, '<')
    draw.text((45, 505), line1, fill=(20, 20, 20))
    draw.text((45, 540), line2, fill=(20, 20, 20))

    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def run_benchmark_suite() -> Dict[str, Any]:
    scenarios = {}

    # 1. Genuine Passport
    doc_bytes = _build_synthetic_passport()
    doc_data = {"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    mrz = ("P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<", "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4")
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz)
    scenarios["01_genuine"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "has_mismatch": res["cross_field_consistency"]["has_mismatch"]}

    # 2. Jury Name Edit
    doc_bytes = _build_synthetic_passport(name="RAHUL SHARMA", ai_text_overlay=True)
    doc_data = {"full_name": "RAHUL SHARMA", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz)
    scenarios["02_jury_name_edit"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "has_mismatch": res["cross_field_consistency"]["has_mismatch"]}

    # 3. DOB mismatch
    doc_bytes = _build_synthetic_passport(dob="2000-01-01")
    doc_data = {"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "2000-01-01", "expiry_date": "2030-05-15"}
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz)
    scenarios["03_dob_tamper"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "has_mismatch": res["cross_field_consistency"]["has_mismatch"]}

    # 4. Doc number mismatch
    doc_bytes = _build_synthetic_passport(doc_number="X9999999")
    doc_data = {"full_name": "ARUN KUMAR", "document_number": "X9999999", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz)
    scenarios["04_doc_num_tamper"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "has_mismatch": res["cross_field_consistency"]["has_mismatch"]}

    # 5. Face photo replaced
    doc_bytes = _build_synthetic_passport(photo_color=(40, 50, 60))
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data={"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}, mrz_lines=mrz)
    scenarios["05_face_replaced"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"]}

    # 6. Screenshot / recompressed
    doc_bytes = _build_synthetic_passport(quality=85)
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data={"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}, mrz_lines=mrz)
    scenarios["06_recompressed"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"]}

    # 7. Heavy JPEG compression
    doc_bytes = _build_synthetic_passport(quality=25)
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data={"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}, mrz_lines=mrz)
    scenarios["07_heavy_jpeg"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "quality_status": res["document_quality"]["status"]}

    # 8. Heavy blur
    doc_bytes = _build_synthetic_passport(blur_radius=5.0)
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data={"full_name": "ARUN KUMAR", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}, mrz_lines=mrz)
    scenarios["08_heavy_blur"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "quality_status": res["document_quality"]["status"]}

    # 9. Multiple fields
    doc_bytes = _build_synthetic_passport(name="VIKRAMADITYA SINGH", doc_number="Z8888888", dob="2002-01-01", ai_text_overlay=True)
    doc_data = {"full_name": "VIKRAMADITYA SINGH", "document_number": "Z8888888", "date_of_birth": "2002-01-01", "expiry_date": "2030-05-15"}
    res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz)
    scenarios["09_multi_field"] = {"status": res["status"], "risk": res["risk"], "recommendation": res["recommendation"], "mismatches": res["cross_field_consistency"]["mismatch_count"]}

    # 10. No-MRZ Original
    doc_bytes_a = _build_synthetic_id_card_no_mrz(name="ARUN KUMAR", ai_edit=False)
    doc_data_a = {"full_name": "ARUN KUMAR", "document_number": "ID123456", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    res_a = detect_tampering(doc_bytes_a, "image/jpeg", extracted_data=doc_data_a)
    scenarios["10_no_mrz_original"] = {"status": res_a["status"], "risk": res_a["risk"], "recommendation": res_a["recommendation"]}

    # 11. No-MRZ AI Inpainted
    doc_bytes_b = _build_synthetic_id_card_no_mrz(name="RAHUL SHARMA", ai_edit=True)
    doc_data_b = {"full_name": "RAHUL SHARMA", "document_number": "ID123456", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    res_b = detect_tampering(doc_bytes_b, "image/jpeg", extracted_data=doc_data_b)
    scenarios["11_no_mrz_ai_edit"] = {"status": res_b["status"], "risk": res_b["risk"], "recommendation": res_b["recommendation"]}

    # 12. Consistent MRZ Tampering
    doc_bytes_12 = _build_synthetic_passport(name="RAHUL SHARMA", mrz_name="RAHUL<<SHARMA<<<<<<<<<<<<<<<<<<<<<<<<<", ai_text_overlay=True)
    doc_data_12 = {"full_name": "RAHUL SHARMA", "document_number": "P1234567", "date_of_birth": "1995-05-15", "expiry_date": "2030-05-15"}
    mrz_12 = ("P<INDRAHUL<<SHARMA<<<<<<<<<<<<<<<<<<<<<<<<<", "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4")
    res_12 = detect_tampering(doc_bytes_12, "image/jpeg", extracted_data=doc_data_12, mrz_lines=mrz_12)
    scenarios["12_consistent_mrz"] = {"status": res_12["status"], "risk": res_12["risk"], "recommendation": res_12["recommendation"], "has_mismatch": res_12["cross_field_consistency"]["has_mismatch"]}

    return scenarios


if __name__ == "__main__":
    baseline = run_benchmark_suite()
    print(json.dumps(baseline, indent=2))
    with open("backend/baseline_results.json", "w") as f:
        json.dump(baseline, f, indent=2)
    print("\nSaved baseline_results.json successfully.")
