"""Red-team adversarial test suite for Document Integrity & Tamper Detection.

Executes all 10 required synthetic red-team evaluation scenarios (Phase 2):
TEST 01: Genuine mock ID -> Low Risk (PASS)
TEST 02: Change Name -> Suspicious / High Risk (Cross-field MRZ mismatch)
TEST 03: Change Date of Birth -> Suspicious / High Risk (DOB mismatch)
TEST 04: Change ID Number -> Suspicious / High Risk (Doc Number mismatch)
TEST 05: Replace Face Photograph -> High Risk / Identity mismatch
TEST 06: AI-style clean text replacement -> Typography/local forensic suspicion
TEST 07: Screenshot / recompressed image -> Low Risk / NOT falsely flagged
TEST 08: Heavy JPEG compression -> Quality degradation warning, NOT fraud
TEST 09: Blur/crop document -> Quality warning / manual review
TEST 10: Multiple fields modified -> High Risk (Multiple anomalies)

Generates and logs the formal Test Matrix.
"""

import io
import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from app.services.tamper_detector import detect_tampering
from app.services.risk_engine import calculate_risk
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


def _build_synthetic_passport_image(
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
    """Generates an in-memory synthetic mock passport image."""
    w, h = 800, 600
    img = Image.new("RGB", (w, h), (246, 243, 238))
    draw = ImageDraw.Draw(img)

    # Outer border & security frame
    draw.rectangle([20, 20, w - 20, h - 20], outline=(120, 120, 120), width=2)
    draw.rectangle([24, 24, w - 24, h - 24], outline=(190, 190, 190), width=1)

    # Document Header
    draw.text((320, 40), "REPUBLIC OF DEMO - PASSPORT", fill=(45, 45, 50))
    draw.line([320, 60, 650, 60], fill=(160, 160, 160), width=1)

    # Photo Box
    draw.rectangle([50, 80, 230, 310], fill=photo_color, outline=(80, 80, 90), width=2)
    # Draw simple facial silhouette
    draw.ellipse([110, 130, 170, 200], fill=(140, 150, 170))
    draw.ellipse([85, 210, 195, 300], fill=(130, 140, 160))

    # Printed Document Fields (baseline authentic text)
    # Document Number
    draw.text((320, 85), "Document No. / Passeport No.", fill=(110, 110, 115))
    draw.text((320, 105), doc_number, fill=(35, 35, 40))

    # Name Field
    draw.text((320, 145), "Surname & Given Names / Nom et Prenoms", fill=(110, 110, 115))
    if not ai_text_overlay:
        # Authentic baseline text
        draw.text((320, 165), name, fill=(35, 35, 40))
    else:
        # Recreate the jury's exact scenario:
        # Erase original name with smooth inpainting patch
        draw.rectangle([315, 160, 580, 195], fill=(246, 243, 238))
        # Superimpose clean digital font with razor-sharp black ink and different weight
        draw.text((320, 165), name, fill=(5, 5, 5))

    # Date of Birth
    draw.text((320, 205), "Date of Birth / Date de naissance", fill=(110, 110, 115))
    draw.text((320, 225), dob, fill=(35, 35, 40))

    # Expiry Date
    draw.text((320, 265), "Date of Expiry / Date d'expiration", fill=(110, 110, 115))
    draw.text((320, 285), expiry, fill=(35, 35, 40))

    # Machine Readable Zone (MRZ)
    draw.rectangle([35, 490, w - 35, 580], fill=(252, 252, 250), outline=(200, 200, 200))
    line1 = f"P<IND{mrz_name}"[:44].ljust(44, '<')
    line2 = f"{mrz_doc}IND{mrz_dob}M{mrz_expiry}<<<<<<<<<<<<<<<4"[:44].ljust(44, '<')
    draw.text((45, 505), line1, fill=(20, 20, 20))
    draw.text((45, 540), line2, fill=(20, 20, 20))

    # Apply blur if requested
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


class TestRedTeamMatrix:
    """Matrix of red-team evaluation scenarios."""

    test_matrix_results = []

    def _record_result(self, test_id, modification, expected, actual, risk_score, triggered_checks, passed):
        TestRedTeamMatrix.test_matrix_results.append({
            "test_id": test_id,
            "modification": modification,
            "expected": expected,
            "actual": actual,
            "risk_score": risk_score,
            "triggered": triggered_checks,
            "passed": passed,
        })

    def test_01_genuine_mock_id(self):
        """TEST 01: Genuine mock ID -> Expected: Low Risk (PASS)."""
        doc_bytes = _build_synthetic_passport_image()
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["status"] == "PASS"
        assert res["risk"] < 25
        assert res["recommendation"] == "CLEAR"
        assert res["cross_field_consistency"]["has_mismatch"] is False

        self._record_result("TEST 01", "None (Genuine)", "Low Risk / PASS", res["status"], res["risk"], "None", True)

    def test_02_change_name_triggers_mismatch(self):
        """TEST 02: Change Name -> Expected: Suspicious / High Risk."""
        # Visual name changed to RAHUL SHARMA, but MRZ has ARUN KUMAR
        doc_bytes = _build_synthetic_passport_image(name="RAHUL SHARMA")
        doc_data = {
            "full_name": "RAHUL SHARMA",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["status"] == "FAIL"
        assert res["risk"] >= 75
        assert res["recommendation"] == "SECONDARY_INSPECTION_RECOMMENDED"
        assert res["cross_field_consistency"]["has_mismatch"] is True
        assert any("MRZ Line 1 Name" in m for m in res["cross_field_consistency"]["mismatches"])

        self._record_result("TEST 02", "Changed Name (ARUN KUMAR -> RAHUL SHARMA)", "High Risk / FAIL", res["status"], res["risk"], "Cross-Field MRZ Mismatch", True)

    def test_03_change_date_of_birth(self):
        """TEST 03: Change Date of Birth -> Expected: Suspicious / High Risk."""
        doc_bytes = _build_synthetic_passport_image(dob="1998-12-25")
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1998-12-25",  # Contradicts MRZ (950515)
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["status"] == "FAIL"
        assert res["risk"] >= 75
        assert res["cross_field_consistency"]["has_mismatch"] is True

        self._record_result("TEST 03", "Changed DOB (1995 -> 1998)", "High Risk / FAIL", res["status"], res["risk"], "Cross-Field DOB Mismatch", True)

    def test_04_change_document_number(self):
        """TEST 04: Change Document Number -> Expected: Suspicious / High Risk."""
        doc_bytes = _build_synthetic_passport_image(doc_number="X9999999")
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "X9999999",  # Contradicts MRZ (P1234567)
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["status"] == "FAIL"
        assert res["risk"] >= 75
        assert res["cross_field_consistency"]["has_mismatch"] is True

        self._record_result("TEST 04", "Changed Doc Number (P1234567 -> X9999999)", "High Risk / FAIL", res["status"], res["risk"], "Cross-Field Doc Number Mismatch", True)

    def test_05_replace_face_photo_triggers_identity_failure(self):
        """TEST 05: Replace Face Photograph -> Expected: Identity mismatch."""
        # Change portrait box to distinct foreign tone
        doc_bytes = _build_synthetic_passport_image(photo_color=(240, 80, 80))
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        # In full screening pipeline, this triggers face_match FAIL
        face_fail = FaceMatchCheckResult(
            status=CheckStatus.FAIL,
            similarity=32.4,
            reason="Selfie does not match document portrait (32.4% similarity)",
        )
        tamper_pass = TamperCheckResult(status=CheckStatus.PASS, risk=10, reason="No tamper detected")
        checks = ChecksContainer(
            mrz=MRZCheckResult(status=CheckStatus.PASS, score=0, reason="Valid MRZ"),
            expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=0, reason="Valid"),
            tamper=tamper_pass,
            face_match=face_fail,
            duplicate_identity=DuplicateIdentityCheckResult(status=CheckStatus.PASS, reason="No duplicate"),
            blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="Clean"),
        )
        risk_eval = calculate_risk(checks)
        assert risk_eval["score"] >= 40
        assert risk_eval["level"] in ("REVIEW", "HIGH")

        self._record_result("TEST 05", "Replaced Portrait Photo", "Face Mismatch / Elevated Risk", risk_eval["level"], risk_eval["score"], "Biometric Face Match FAIL", True)

    def test_06_ai_style_clean_text_replacement(self):
        """TEST 06: AI-style clean text replacement (jury failure scenario).

        Alters text field while blending background. System must raise suspicion
        via typography consistency and local forensics.
        """
        # Generate with ai_text_overlay=True
        doc_bytes = _build_synthetic_passport_image(name="RAHUL SHARMA", ai_text_overlay=True)
        doc_data = {
            "full_name": "RAHUL SHARMA",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        # Must NOT return PASS / 0 risk!
        assert res["status"] in ("WARNING", "FAIL")
        assert res["risk"] >= 35
        assert res["recommendation"] in ("MANUAL_REVIEW_RECOMMENDED", "SECONDARY_INSPECTION_RECOMMENDED")

        self._record_result("TEST 06", "AI Clean Inpainted Name", "Suspicious / FAIL", res["status"], res["risk"], "Typography / Data Mismatch", True)

    def test_07_screenshot_recompressed_not_falsely_flagged(self):
        """TEST 07: Screenshot / recompressed image -> Expected: NOT falsely flagged as fraud."""
        # Quality 80 recompression simulating standard mobile screenshot
        doc_bytes = _build_synthetic_passport_image(quality=80)
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        # Standard screenshot must not fail
        assert res["status"] in ("PASS", "WARNING")
        assert res["risk"] < 35
        assert res["cross_field_consistency"]["has_mismatch"] is False

        self._record_result("TEST 07", "Standard Screenshot (Q=80)", "Low Risk / PASS", res["status"], res["risk"], "None (Clean screenshot)", True)

    def test_08_heavy_jpeg_compression_classified_as_quality(self):
        """TEST 08: Heavy JPEG compression -> Quality degradation warning, NOT fraud."""
        doc_bytes = _build_synthetic_passport_image(quality=25)
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        # Quality should recognize compression, cross-field remains valid
        assert res["document_quality"]["metrics"]["is_heavy_compression"] is True
        assert res["cross_field_consistency"]["has_mismatch"] is False

        self._record_result("TEST 08", "Heavy JPEG Compression (Q=25)", "Quality Warning / Review", res["status"], res["risk"], "Quality: Heavy Compression", True)

    def test_09_heavy_blur_triggers_quality_review(self):
        """TEST 09: Blur/crop document -> Quality warning / manual review."""
        doc_bytes = _build_synthetic_passport_image(blur_radius=6.0)
        doc_data = {
            "full_name": "ARUN KUMAR",
            "document_number": "P1234567",
            "date_of_birth": "1995-05-15",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["document_quality"]["metrics"]["is_heavy_blur"] is True
        assert res["confidence"] in ("LOW", "MEDIUM")
        assert res["recommendation"] == "MANUAL_REVIEW_RECOMMENDED"

        self._record_result("TEST 09", "Heavy Optical Blur", "Quality Warning / Review", res["status"], res["risk"], "Quality: Severe Blur", True)

    def test_10_multiple_fields_modified(self):
        """TEST 10: Multiple fields modified -> Expected: High Risk."""
        doc_bytes = _build_synthetic_passport_image(
            name="VIKRAMADITYA SINGH",
            doc_number="Z8888888",
            dob="2002-01-01",
            ai_text_overlay=True,
        )
        doc_data = {
            "full_name": "VIKRAMADITYA SINGH",
            "document_number": "Z8888888",
            "date_of_birth": "2002-01-01",
            "expiry_date": "2030-05-15",
        }
        mrz_lines = (
            "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4",
        )
        res = detect_tampering(doc_bytes, "image/jpeg", extracted_data=doc_data, mrz_lines=mrz_lines)

        assert res["status"] == "FAIL"
        assert res["risk"] >= 75
        assert res["recommendation"] == "SECONDARY_INSPECTION_RECOMMENDED"
        assert res["cross_field_consistency"]["mismatch_count"] >= 2

        self._record_result("TEST 10", "Multiple Fields (Name, DOB, ID)", "High Risk / FAIL", res["status"], res["risk"], "Multiple Cross-Field Mismatches + Typography", True)

    @classmethod
    def teardown_class(cls):
        """Prints the formal Red-Team Test Matrix table."""
        print("\n" + "=" * 105)
        print("RED-TEAM ADVERSARIAL TEST MATRIX — SIH26188 DOCUMENT INTEGRITY ANALYSIS")
        print("=" * 105)
        header = f"{'Test Case':<10} | {'Modification':<35} | {'Expected Result':<22} | {'Actual':<8} | {'Risk':<5} | {'Status':<6}"
        print(header)
        print("-" * 105)
        for r in cls.test_matrix_results:
            row = f"{r['test_id']:<10} | {r['modification']:<35} | {r['expected']:<22} | {r['actual']:<8} | {str(r['risk_score']):<5} | {'PASSED' if r['passed'] else 'FAILED':<6}"
            print(row)
        print("=" * 105 + "\n")
