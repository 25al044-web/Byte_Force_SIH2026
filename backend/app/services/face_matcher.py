"""Face comparison service for SIH26188.

Compares a selfie against the portrait extracted from an identity document using
pretrained face-embedding models via the InsightFace library (ONNX Runtime backend).
InsightFace is TensorFlow-free and runs on CPU.

Privacy guarantees:
- Images are never persisted to disk.
- Embeddings are never logged or stored.
- No personal data is written anywhere.

Return format:
    {
        "status": "PASS" | "WARNING" | "FAIL" | "NOT_AVAILABLE",
        "similarity": float | None,   # 0-100 normalised; None if unavailable
        "reason": str
    }
"""

import logging
from io import BytesIO
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds (tuneable)
# ---------------------------------------------------------------------------
PASS_THRESHOLD = 75.0       # similarity >= 75  → PASS
WARNING_THRESHOLD = 55.0    # similarity >= 55  → WARNING; below → FAIL

# InsightFace cosine similarity: 1.0 = identical, 0.0 = orthogonal, -1.0 = opposite
# We map [-1.0, 1.0] to [0, 100]:  percent = (raw + 1) / 2 * 100
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Lazy import helpers
# ---------------------------------------------------------------------------

def _import_insightface():
    """Import insightface lazily to avoid slow startup costs."""
    try:
        import insightface  # type: ignore
        from insightface.app import FaceAnalysis  # type: ignore
        return FaceAnalysis
    except ImportError as exc:
        raise ImportError(
            "insightface is not installed. "
            "Run: pip install insightface onnxruntime"
        ) from exc


def _import_pil_image():
    """Import PIL Image lazily."""
    try:
        from PIL import Image  # type: ignore
        return Image
    except ImportError as exc:
        raise ImportError(
            "Pillow is not installed. Run: pip install pillow"
        ) from exc


def _import_numpy():
    """Import numpy lazily."""
    try:
        import numpy as np  # type: ignore
        return np
    except ImportError as exc:
        raise ImportError("numpy is not installed.") from exc


# ---------------------------------------------------------------------------
# Module-level app cache
# ---------------------------------------------------------------------------
_face_app = None


def _get_face_app():
    """Return a cached, initialised InsightFace FaceAnalysis app.

    Uses the buffalo_sc (small, CPU-friendly) model pack.
    Downloads automatically on first call (~100 MB) and caches to disk.
    """
    global _face_app
    if _face_app is None:
        FaceAnalysis = _import_insightface()
        app = FaceAnalysis(
            name="buffalo_sc",   # small model: RetinaFace (det) + ArcFace (rec)
            providers=["CPUExecutionProvider"],
        )
        app.prepare(ctx_id=0, det_size=(640, 640))
        _face_app = app
    return _face_app


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bytes_to_bgr(image_bytes: bytes, mime_type: str):
    """Convert raw image bytes to a BGR numpy array (OpenCV convention).

    InsightFace expects BGR (H, W, 3) uint8 arrays.

    Parameters
    ----------
    image_bytes : bytes
        Raw binary image data.
    mime_type : str
        MIME type string (e.g. ``"image/jpeg"``).

    Returns
    -------
    numpy.ndarray
        An (H, W, 3) uint8 BGR array suitable for InsightFace.

    Raises
    ------
    ValueError
        If the image cannot be decoded.
    """
    Image = _import_pil_image()
    np = _import_numpy()

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        # RGB → BGR
        bgr = arr[:, :, ::-1].copy()
        return bgr
    except Exception as exc:
        raise ValueError(f"Cannot decode image (mime={mime_type}): {exc}") from exc


def _cosine_similarity(emb1, emb2) -> float:
    """Compute normalised cosine similarity between two 1-D embedding vectors.

    Returns a value in [-1.0, 1.0]; 1.0 = identical.
    """
    np = _import_numpy()
    n1 = np.linalg.norm(emb1)
    n2 = np.linalg.norm(emb2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / (n1 * n2))


def _cosine_to_percent(cosine: float) -> float:
    """Map cosine similarity [-1, 1] to [0, 100] percentage.

    ArcFace embeddings from InsightFace are already L2-normalised, so
    cosine similarity is in practice ≥ −1. We use the linear mapping:
        percent = (cosine + 1) / 2 * 100
    """
    percent = (cosine + 1.0) / 2.0 * 100.0
    return round(min(100.0, max(0.0, percent)), 1)


def _status_from_similarity(similarity: float) -> str:
    """Map a 0-100 similarity score to a check status string."""
    if similarity >= PASS_THRESHOLD:
        return "PASS"
    if similarity >= WARNING_THRESHOLD:
        return "WARNING"
    return "FAIL"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_faces(
    document_image_bytes: bytes,
    document_mime_type: str,
    selfie_image_bytes: bytes,
    selfie_mime_type: str,
    precomputed_doc_bgr: Optional[Any] = None,
    precomputed_selfie_bgr: Optional[Any] = None,
) -> Dict[str, Any]:
    """Compare the primary face in a document image to a selfie.

    Parameters
    ----------
    document_image_bytes : bytes
        Raw bytes of the identity document image.
    document_mime_type : str
        MIME type of the document image (e.g. ``"image/jpeg"``).
    selfie_image_bytes : bytes
        Raw bytes of the selfie image.
    selfie_mime_type : str
        MIME type of the selfie image.
    precomputed_doc_bgr : Optional[np.ndarray]
        Pre-decoded BGR numpy array for document image (skips redundant decoding).
    precomputed_selfie_bgr : Optional[np.ndarray]
        Pre-decoded BGR numpy array for selfie image (skips redundant decoding).

    Returns
    -------
    dict
        ``{"status": str, "similarity": float | None, "reason": str}``
    """
    # ── 1. Decode images to BGR arrays (or reuse precomputed) ───────────────
    if precomputed_doc_bgr is not None:
        doc_bgr = precomputed_doc_bgr
    else:
        try:
            doc_bgr = _bytes_to_bgr(document_image_bytes, document_mime_type)
        except ValueError as exc:
            logger.warning("Face matcher: cannot decode document image — %s", exc)
            return {
                "status": "NOT_AVAILABLE",
                "similarity": None,
                "reason": "Document image could not be decoded",
            }

    if precomputed_selfie_bgr is not None:
        selfie_bgr = precomputed_selfie_bgr
    else:
        try:
            selfie_bgr = _bytes_to_bgr(selfie_image_bytes, selfie_mime_type)
        except ValueError as exc:
            logger.warning("Face matcher: cannot decode selfie image — %s", exc)
            return {
                "status": "NOT_AVAILABLE",
                "similarity": None,
                "reason": "Selfie image could not be decoded",
            }

    # ── 2. Detect and embed faces ────────────────────────────────────────────
    try:
        app = _get_face_app()
    except Exception as exc:
        logger.warning("Face matcher: cannot initialise InsightFace — %s", exc)
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "Face comparison service unavailable",
        }

    try:
        doc_faces = app.get(doc_bgr)
    except Exception as exc:
        logger.warning("Face matcher: detection failed on document image — %s", exc)
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "Face detection failed on document image",
        }

    try:
        selfie_faces = app.get(selfie_bgr)
    except Exception as exc:
        logger.warning("Face matcher: detection failed on selfie image — %s", exc)
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "Face detection failed on selfie image",
        }

    # ── 3. Validate face counts and extract selfie embedding ───────────────────
    np = _import_numpy()
    selfie_embedding_list = None

    if not selfie_faces:
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "No face detected in selfie image",
            "_selfie_embedding": None,
            "_selfie_checked": True,
        }

    # Extract primary selfie face embedding
    def _area(f):
        bbox = f.bbox  # [x1, y1, x2, y2]
        return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    selfie_face = max(selfie_faces, key=_area)
    selfie_emb = selfie_face.embedding
    if selfie_emb is not None:
        norm = float(np.linalg.norm(selfie_emb))
        if norm == 0:
            selfie_embedding_list = selfie_emb.tolist()
        else:
            selfie_embedding_list = (selfie_emb / norm).astype(float).tolist()

    if not doc_faces:
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "No face detected in document image",
            "_selfie_embedding": selfie_embedding_list,
            "_selfie_checked": True,
        }

    # ── 4. Select primary document face ──────────────────────────────────────
    doc_face = max(doc_faces, key=_area)
    doc_emb = doc_face.embedding

    if doc_emb is None or selfie_emb is None:
        return {
            "status": "NOT_AVAILABLE",
            "similarity": None,
            "reason": "Face embedding unavailable for one or both images",
            "_selfie_embedding": selfie_embedding_list,
            "_selfie_checked": True,
        }

    # ── 5. Compute similarity ────────────────────────────────────────────────
    cosine = _cosine_similarity(doc_emb, selfie_emb)
    similarity = _cosine_to_percent(cosine)
    check_status = _status_from_similarity(similarity)

    # ── 6. Build human-readable reason ──────────────────────────────────────
    if check_status == "PASS":
        reason = f"Selfie matches document portrait ({similarity:.1f}% similarity)"
    elif check_status == "WARNING":
        reason = (
            f"Borderline face similarity ({similarity:.1f}%); "
            "manual review recommended"
        )
    else:
        reason = (
            f"Selfie does not match document portrait ({similarity:.1f}% similarity)"
        )

    return {
        "status": check_status,
        "similarity": similarity,
        "reason": reason,
        "_selfie_embedding": selfie_embedding_list,
        "_selfie_checked": True,
    }


def extract_selfie_embedding(
    selfie_image_bytes: bytes,
    selfie_mime_type: str,
    precomputed_embedding: Optional[List[float]] = None,
    precomputed_bgr: Optional[Any] = None,
) -> Optional[List[float]]:
    """Extract the primary face embedding from a selfie image.

    Reuses the cached InsightFace ``buffalo_sc`` model. The embedding is
    returned as a plain Python ``list[float]`` so it can be JSON-serialised
    for storage.  Embedding values are **never** logged.

    This function is **backend-only**.  It must never be exposed in API
    responses or serialised into response models.

    Parameters
    ----------
    selfie_image_bytes : bytes
        Raw bytes of the selfie image.
    selfie_mime_type : str
        MIME type of the selfie image (e.g. ``"image/jpeg"``).
    precomputed_embedding : Optional[list[float]]
        If already extracted (e.g. during compare_faces), returns immediately.
    precomputed_bgr : Optional[np.ndarray]
        Pre-decoded BGR numpy array to skip duplicate decoding.

    Returns
    -------
    list[float] or None
        L2-normalised 512-d ArcFace embedding as a plain Python list, or
        ``None`` if detection / embedding extraction fails for any reason.
    """
    if precomputed_embedding is not None:
        return precomputed_embedding

    np = _import_numpy()

    if precomputed_bgr is not None:
        selfie_bgr = precomputed_bgr
    else:
        try:
            selfie_bgr = _bytes_to_bgr(selfie_image_bytes, selfie_mime_type)
        except ValueError as exc:
            logger.warning("extract_selfie_embedding: cannot decode selfie — %s", exc)
            return None

    try:
        app = _get_face_app()
    except Exception as exc:
        logger.warning("extract_selfie_embedding: InsightFace unavailable — %s", exc)
        return None

    try:
        faces = app.get(selfie_bgr)
    except Exception as exc:
        logger.warning("extract_selfie_embedding: detection failed — %s", exc)
        return None

    if not faces:
        logger.info("extract_selfie_embedding: no face detected in selfie")
        return None

    # Select primary face (largest bounding box)
    def _area(f):
        bbox = f.bbox
        return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    primary = max(faces, key=_area)
    emb = primary.embedding

    if emb is None:
        logger.warning("extract_selfie_embedding: embedding is None")
        return None

    # L2-normalise and return as plain Python list (JSON-safe, no numpy dependency downstream)
    norm = np.linalg.norm(emb)
    if norm == 0:
        return emb.tolist()
    normalised = (emb / norm).astype(float)
    return normalised.tolist()
