"""Tests for tamper_detector.py forensic screening service — SIH26188.

Validates:
1. Clean synthetic document -> PASS (low risk)
2. Blurred image -> warning / low-confidence signal
3. Strong pasted region -> elevated risk
4. Duplicate region -> elevated risk
5. Extreme local sharpness difference -> elevated risk
6. Corrupted bytes -> NOT_AVAILABLE
7. Unsupported MIME -> NOT_AVAILABLE
8. Tiny image -> NOT_AVAILABLE
9. Score clamped 0-100
10. Deterministic output
11. No single weak signal causes false FAIL
12. Pipeline uses real tamper result
13. Tamper risk feeds real risk engine
"""

import io
import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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
from app.services.risk_engine import calculate_risk
from app.services.tamper_detector import detect_tampering


# ---------------------------------------------------------------------------
# Synthetic Image Generation Helpers
# ---------------------------------------------------------------------------

def _create_clean_document_bytes(width=800, height=600, quality=95) -> bytes:
    """Generate clean synthetic travel/identity document JPEG bytes."""
    img = Image.new("RGB", (width, height), (245, 242, 238))
    draw = ImageDraw.Draw(img)
    # Outer border
    draw.rectangle([30, 30, width - 30, height - 30], outline=(100, 100, 100), width=2)
    # Photo box with mild tone
    draw.rectangle([50, 60, 220, 280], fill=(210, 210, 220), outline=(60, 60, 60))
    # Text lines
    for y in range(70, height - 70, 26):
        draw.line([250, y, width - 50, y], fill=(40, 40, 40), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _create_blurred_document_bytes(radius=7) -> bytes:
    """Generate heavily blurred document JPEG bytes."""
    clean = Image.open(io.BytesIO(_create_clean_document_bytes())).convert("RGB")
    blurred = clean.filter(ImageFilter.GaussianBlur(radius=radius))
    buf = io.BytesIO()
    blurred.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _create_pasted_patch_document_bytes() -> bytes:
    """Generate document with a foreign noisy spliced patch."""
    clean = Image.open(io.BytesIO(_create_clean_document_bytes())).convert("RGB")
    # Foreign patch with distinct noise and sharp rectangular boundary
    patch = Image.new("RGB", (220, 120), (255, 255, 255))
    pd = ImageDraw.Draw(patch)
    pd.rectangle([0, 0, 219, 119], outline=(0, 0, 0), width=4)
    pd.text((20, 45), "FORGED ALTERED TEXT", fill=(0, 0, 0))
    p_arr = np.array(patch, dtype=np.float32)
    # Add heavy local deterministic noise
    rng = np.random.RandomState(42)
    p_arr += rng.normal(0, 60.0, p_arr.shape)
    noisy_patch = Image.fromarray(np.clip(p_arr, 0, 255).astype(np.uint8))
    # Recompress patch at very low JPEG quality 10
    p_buf = io.BytesIO()
    noisy_patch.save(p_buf, format="JPEG", quality=10)
    p_buf.seek(0)
    clean.paste(Image.open(p_buf), (300, 200))
    buf = io.BytesIO()
    clean.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _create_duplicate_stamp_document_bytes() -> bytes:
    """Generate document with duplicate cloned graphical regions."""
    clean = Image.open(io.BytesIO(_create_clean_document_bytes())).convert("RGB")
    # Draw stamp
    stamp = Image.new("RGB", (90, 90), (220, 120, 120))
    sd = ImageDraw.Draw(stamp)
    sd.ellipse([10, 10, 80, 80], outline=(80, 20, 20), width=4)
    sd.line([25, 45, 65, 45], fill=(80, 20, 20), width=3)
    sd.line([45, 25, 45, 65], fill=(80, 20, 20), width=3)
    # Paste stamp in two distinct 2D positions
    clean.paste(stamp, (80, 350))
    clean.paste(stamp, (450, 180))
    buf = io.BytesIO()
    clean.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestTamperDetector:
    def test_clean_synthetic_document_returns_pass_or_low_risk(self):
        """Clean authentic document should receive PASS status and low risk score."""
        image_bytes = _create_clean_document_bytes()
        res = detect_tampering(image_bytes, "image/jpeg")
        assert res["status"] == "PASS"
        assert 0 <= res["risk"] < 20
        assert "No significant visual tamper indicators" in res["reason"]

    def test_blurred_image_triggers_sharpness_warning(self):
        """Blurred document should trigger blur indicator without crashing."""
        image_bytes = _create_blurred_document_bytes(radius=8)
        res = detect_tampering(image_bytes, "image/jpeg")
        # Blur contributes to score but alone does not cause false FAIL
        assert res["status"] in ("PASS", "WARNING")
        blur_check = next((c for c in res["checks"] if c["name"] == "blur_quality"), None)
        assert blur_check is not None
        assert blur_check["status"] == "WARNING"
        assert blur_check["score"] > 0

    def test_strong_pasted_region_elevates_risk(self):
        """Document with spliced noisy patch should elevate tamper risk."""
        image_bytes = _create_pasted_patch_document_bytes()
        res = detect_tampering(image_bytes, "image/jpeg")
        assert res["risk"] >= 20
        assert res["status"] in ("WARNING", "FAIL")

    def test_duplicate_region_elevates_risk(self):
        """Document with cloned stamp regions should detect duplicate features."""
        image_bytes = _create_duplicate_stamp_document_bytes()
        res = detect_tampering(image_bytes, "image/jpeg")
        assert res["risk"] >= 15
        dup_check = next((c for c in res["checks"] if c["name"] == "duplicate_regions"), None)
        assert dup_check is not None
        assert dup_check["score"] > 0

    def test_extreme_local_sharpness_difference(self):
        """Sharp pasted box on a soft document elevates edge and sharpness risk."""
        clean = Image.open(io.BytesIO(_create_clean_document_bytes())).convert("RGB")
        soft = clean.filter(ImageFilter.GaussianBlur(radius=3))
        # Insert sharp high-contrast rectangle
        sd = ImageDraw.Draw(soft)
        sd.rectangle([350, 150, 550, 280], fill=(0, 0, 0), outline=(255, 255, 255), width=5)
        buf = io.BytesIO()
        soft.save(buf, format="JPEG", quality=95)

        res = detect_tampering(buf.getvalue(), "image/jpeg")
        assert res["risk"] >= 15

    def test_corrupted_bytes_returns_not_available(self):
        """Corrupted image bytes should yield NOT_AVAILABLE without crashing."""
        res = detect_tampering(b"random_corrupted_garbage_bytes", "image/jpeg")
        assert res["status"] == "NOT_AVAILABLE"
        assert res["risk"] is None
        assert "unavailable" in res["reason"].lower()

    def test_unsupported_mime_type_returns_not_available(self):
        """Unsupported MIME type should yield NOT_AVAILABLE."""
        res = detect_tampering(b"some_bytes", "application/pdf")
        assert res["status"] == "NOT_AVAILABLE"
        assert res["risk"] is None
        assert "unsupported mime" in res["reason"].lower()

    def test_tiny_image_returns_not_available(self):
        """Image smaller than minimum resolution (50x50) returns NOT_AVAILABLE."""
        tiny = Image.new("RGB", (30, 30), (255, 255, 255))
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        res = detect_tampering(buf.getvalue(), "image/jpeg")
        assert res["status"] == "NOT_AVAILABLE"
        assert res["risk"] is None
        assert "too small" in res["reason"].lower()

    def test_score_clamped_between_0_and_100(self):
        """Tamper risk score must always be strictly between 0 and 100."""
        clean_bytes = _create_clean_document_bytes()
        res = detect_tampering(clean_bytes, "image/jpeg")
        assert 0 <= res["risk"] <= 100

        pasted_bytes = _create_pasted_patch_document_bytes()
        res_p = detect_tampering(pasted_bytes, "image/jpeg")
        assert 0 <= res_p["risk"] <= 100

    def test_deterministic_output(self):
        """Repeated calls with identical bytes must produce identical scores."""
        clean_bytes = _create_clean_document_bytes()
        res1 = detect_tampering(clean_bytes, "image/jpeg")
        res2 = detect_tampering(clean_bytes, "image/jpeg")
        assert res1["status"] == res2["status"]
        assert res1["risk"] == res2["risk"]
        assert res1["reason"] == res2["reason"]

    def test_no_single_weak_signal_causes_false_fail(self):
        """A single minor anomaly (such as slight blur or missing EXIF) must not trigger FAIL."""
        blurred_bytes = _create_blurred_document_bytes(radius=4)
        res = detect_tampering(blurred_bytes, "image/jpeg")
        # Single blur anomaly adds 15 points, so risk < 50 (never FAIL)
        assert res["status"] != "FAIL"
        assert res["risk"] < 50

    def test_pipeline_uses_real_tamper_result_model(self):
        """TamperCheckResult Pydantic model successfully parses detector output."""
        clean_bytes = _create_clean_document_bytes()
        res = detect_tampering(clean_bytes, "image/jpeg")
        model = TamperCheckResult(
            status=CheckStatus(res["status"]),
            risk=res.get("risk"),
            reason=res["reason"],
        )
        assert model.status == CheckStatus.PASS
        assert model.risk == res["risk"]
        assert model.reason == res["reason"]

    def test_tamper_risk_feeds_real_risk_engine(self):
        """Elevated tamper risk score directly increases composite risk score in risk engine."""
        checks_low_tamper = ChecksContainer(
            mrz=MRZCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            tamper=TamperCheckResult(status=CheckStatus.PASS, risk=5, reason="Clean"),
            face_match=FaceMatchCheckResult(status=CheckStatus.PASS, similarity=95.0, reason="ok"),
            duplicate_identity=DuplicateIdentityCheckResult(status=CheckStatus.PASS, similar_identity=None, reason="ok"),
            blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
        )
        res_low = calculate_risk(checks_low_tamper)

        checks_high_tamper = ChecksContainer(
            mrz=MRZCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            tamper=TamperCheckResult(status=CheckStatus.FAIL, risk=75, reason="Altered"),
            face_match=FaceMatchCheckResult(status=CheckStatus.PASS, similarity=95.0, reason="ok"),
            duplicate_identity=DuplicateIdentityCheckResult(status=CheckStatus.PASS, similar_identity=None, reason="ok"),
            blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
        )
        res_high = calculate_risk(checks_high_tamper)

        # Tamper risk 75 should add 30 risk points compared to tamper risk 5 (0 risk points)
        assert res_high["score"] > res_low["score"]
        assert res_high["contributions"]["tamper"] == 30
        assert res_low["contributions"]["tamper"] == 0
        assert "Tamper screening detected elevated risk (75/100): +30 risk." in res_high["explanations"]
