"""Tests for face_matcher.py — SIH26188.

All InsightFace / ONNX calls are fully mocked so the tests run without any
model weights, GPU, network access, or heavy computation.

13 test scenarios:
 1.  High-similarity pair → PASS
 2.  Borderline-similarity pair → WARNING
 3.  Low-similarity pair → FAIL
 4.  Bad document image bytes → NOT_AVAILABLE
 5.  Bad selfie image bytes → NOT_AVAILABLE
 6.  No face detected in document image → NOT_AVAILABLE
 7.  No face detected in selfie image → NOT_AVAILABLE
 8.  InsightFace app.get() raises Exception → NOT_AVAILABLE
 9.  similarity exactly at PASS_THRESHOLD (75) → PASS
10.  similarity exactly at WARNING_THRESHOLD (55) → WARNING
11.  similarity just below WARNING_THRESHOLD (54.9) → FAIL
12.  similarity == 100.0 → PASS, reason contains %
13.  similarity == 0.0 → FAIL, reason contains %
"""

import io
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jpeg_bytes(width: int = 10, height: int = 10) -> bytes:
    """Create a minimal valid JPEG image in memory."""
    img = Image.new("RGB", (width, height), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


GOOD_DOC_BYTES = _make_jpeg_bytes()
GOOD_SELFIE_BYTES = _make_jpeg_bytes()
BAD_BYTES = b"not-an-image"


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _make_face(embedding: np.ndarray, bbox=(0, 0, 100, 100)) -> MagicMock:
    """Build a mock InsightFace Face object."""
    face = MagicMock()
    face.embedding = embedding
    face.bbox = list(bbox)
    return face


def _make_app_mock(doc_faces, selfie_faces) -> MagicMock:
    """Build a mock InsightFace FaceAnalysis app."""
    app = MagicMock()
    app.get.side_effect = [doc_faces, selfie_faces]
    return app


def _emb_with_cosine(target_cosine: float) -> tuple:
    """Return two unit embeddings whose cosine similarity equals target_cosine.

    Both vectors are 512-d (ArcFace output size).
    emb1 is always [1, 0, 0, ...] (unit x-axis).
    emb2 is constructed so that dot(emb1, emb2) = target_cosine.
    """
    dim = 512
    emb1 = np.zeros(dim, dtype=np.float32)
    emb1[0] = 1.0

    # emb2 = [target_cosine, sqrt(1 - target_cosine^2), 0, ...]
    emb2 = np.zeros(dim, dtype=np.float32)
    emb2[0] = float(target_cosine)
    remainder = 1.0 - target_cosine ** 2
    if remainder > 0:
        emb2[1] = float(remainder ** 0.5)
    emb2 /= np.linalg.norm(emb2)  # ensure unit length
    return emb1, emb2


def _percent_from_cosine(cosine: float) -> float:
    """Mirror the _cosine_to_percent formula from face_matcher.py."""
    return round(min(100.0, max(0.0, (cosine + 1.0) / 2.0 * 100.0)), 1)


GET_APP = "app.services.face_matcher._get_face_app"


# ---------------------------------------------------------------------------
# _bytes_to_bgr
# ---------------------------------------------------------------------------

class TestBytesToBgr:
    def test_valid_jpeg_returns_bgr_array(self):
        from app.services.face_matcher import _bytes_to_bgr
        arr = _bytes_to_bgr(GOOD_DOC_BYTES, "image/jpeg")
        assert arr.ndim == 3
        assert arr.shape[2] == 3

    def test_invalid_bytes_raises_value_error(self):
        from app.services.face_matcher import _bytes_to_bgr
        with pytest.raises(ValueError):
            _bytes_to_bgr(BAD_BYTES, "image/jpeg")


# ---------------------------------------------------------------------------
# _cosine_to_percent
# ---------------------------------------------------------------------------

class TestCosineToPercent:
    def test_identity_is_100(self):
        from app.services.face_matcher import _cosine_to_percent
        assert _cosine_to_percent(1.0) == 100.0

    def test_zero_is_50(self):
        from app.services.face_matcher import _cosine_to_percent
        assert _cosine_to_percent(0.0) == 50.0

    def test_negative_one_is_zero(self):
        from app.services.face_matcher import _cosine_to_percent
        assert _cosine_to_percent(-1.0) == 0.0

    def test_clamp_above_100(self):
        from app.services.face_matcher import _cosine_to_percent
        assert _cosine_to_percent(2.0) == 100.0

    def test_clamp_below_zero(self):
        from app.services.face_matcher import _cosine_to_percent
        assert _cosine_to_percent(-2.0) == 0.0


# ---------------------------------------------------------------------------
# _status_from_similarity
# ---------------------------------------------------------------------------

class TestStatusFromSimilarity:
    def test_pass_high(self):
        from app.services.face_matcher import _status_from_similarity
        assert _status_from_similarity(90.0) == "PASS"

    def test_warning_mid(self):
        from app.services.face_matcher import _status_from_similarity
        assert _status_from_similarity(60.0) == "WARNING"

    def test_fail_low(self):
        from app.services.face_matcher import _status_from_similarity
        assert _status_from_similarity(30.0) == "FAIL"


# ---------------------------------------------------------------------------
# compare_faces — 13 integration scenarios
# ---------------------------------------------------------------------------

class TestCompareFaces:

    # ── Scenario 1: high-similarity pair → PASS ──────────────────────────────
    def test_high_similarity_pass(self):
        from app.services.face_matcher import compare_faces
        # cosine 0.90 → percent = (0.90+1)/2*100 = 95.0
        e1, e2 = _emb_with_cosine(0.90)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "PASS"
        assert result["similarity"] >= 75.0
        assert result["similarity"] is not None
        assert "%" in result["reason"]

    # ── Scenario 2: borderline similarity → WARNING ───────────────────────────
    def test_borderline_similarity_warning(self):
        from app.services.face_matcher import compare_faces
        # cosine 0.10 → percent = (0.10+1)/2*100 = 55.0 → exactly WARNING
        e1, e2 = _emb_with_cosine(0.10)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "WARNING"
        assert 55.0 <= result["similarity"] < 75.0

    # ── Scenario 3: low-similarity pair → FAIL ───────────────────────────────
    def test_low_similarity_fail(self):
        from app.services.face_matcher import compare_faces
        # cosine -0.50 → percent = (-0.50+1)/2*100 = 25.0 → FAIL
        e1, e2 = _emb_with_cosine(-0.50)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "FAIL"
        assert result["similarity"] < 55.0

    # ── Scenario 4: bad document image → NOT_AVAILABLE ───────────────────────
    def test_bad_document_image_not_available(self):
        from app.services.face_matcher import compare_faces
        e1, e2 = _emb_with_cosine(0.90)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(BAD_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similarity"] is None
        assert "document" in result["reason"].lower()

    # ── Scenario 5: bad selfie image → NOT_AVAILABLE ─────────────────────────
    def test_bad_selfie_image_not_available(self):
        from app.services.face_matcher import compare_faces
        e1, e2 = _emb_with_cosine(0.90)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", BAD_BYTES, "image/jpeg")
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similarity"] is None
        assert "selfie" in result["reason"].lower()

    # ── Scenario 6: no face in document → NOT_AVAILABLE ──────────────────────
    def test_no_face_in_document(self):
        from app.services.face_matcher import compare_faces
        _, e2 = _emb_with_cosine(0.90)
        app = _make_app_mock([], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similarity"] is None
        assert "document" in result["reason"].lower()

    # ── Scenario 7: no face in selfie → NOT_AVAILABLE ────────────────────────
    def test_no_face_in_selfie(self):
        from app.services.face_matcher import compare_faces
        e1, _ = _emb_with_cosine(0.90)
        app = _make_app_mock([_make_face(e1)], [])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similarity"] is None
        assert "selfie" in result["reason"].lower()

    # ── Scenario 8: app.get() raises Exception → NOT_AVAILABLE ───────────────
    def test_app_get_raises_exception(self):
        from app.services.face_matcher import compare_faces
        app = MagicMock()
        app.get.side_effect = RuntimeError("ONNX model error")
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similarity"] is None

    # ── Scenario 9: similarity exactly at PASS_THRESHOLD → PASS ─────────────
    def test_similarity_exactly_at_pass_threshold(self):
        from app.services.face_matcher import compare_faces, PASS_THRESHOLD
        # PASS_THRESHOLD = 75.0 → cosine = 2*(75/100) - 1 = 0.50
        target_cosine = 2.0 * (PASS_THRESHOLD / 100.0) - 1.0
        e1, e2 = _emb_with_cosine(target_cosine)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "PASS"

    # ── Scenario 10: similarity exactly at WARNING_THRESHOLD → WARNING ────────
    def test_similarity_exactly_at_warning_threshold(self):
        from app.services.face_matcher import compare_faces, WARNING_THRESHOLD
        # WARNING_THRESHOLD = 55.0 → cosine = 2*(55/100) - 1 = 0.10
        target_cosine = 2.0 * (WARNING_THRESHOLD / 100.0) - 1.0
        e1, e2 = _emb_with_cosine(target_cosine)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "WARNING"

    # ── Scenario 11: similarity just below WARNING_THRESHOLD → FAIL ───────────
    def test_similarity_just_below_warning_threshold(self):
        from app.services.face_matcher import compare_faces, WARNING_THRESHOLD
        # 54.9 → cosine = 2*(54.9/100) - 1 = 0.098
        target_cosine = 2.0 * ((WARNING_THRESHOLD - 0.1) / 100.0) - 1.0
        e1, e2 = _emb_with_cosine(target_cosine)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "FAIL"

    # ── Scenario 12: similarity == 100.0 → PASS, reason has % ────────────────
    def test_perfect_match_reason(self):
        from app.services.face_matcher import compare_faces
        # cosine = 1.0 → identical
        e1, e2 = _emb_with_cosine(1.0)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "PASS"
        assert result["similarity"] == 100.0
        assert "%" in result["reason"]
        assert "matches" in result["reason"].lower()

    # ── Scenario 13: similarity == 0.0 → FAIL, reason has % ─────────────────
    def test_zero_match_reason(self):
        from app.services.face_matcher import compare_faces
        # cosine = -1.0 → anti-parallel → similarity = 0.0
        e1, e2 = _emb_with_cosine(-1.0)
        app = _make_app_mock([_make_face(e1)], [_make_face(e2)])
        with patch(GET_APP, return_value=app):
            result = compare_faces(GOOD_DOC_BYTES, "image/jpeg", GOOD_SELFIE_BYTES, "image/jpeg")
        assert result["status"] == "FAIL"
        assert result["similarity"] == 0.0
        assert "%" in result["reason"]
        assert "not match" in result["reason"].lower()
