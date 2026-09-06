"""Document tamper screening service for SIH26188.

Executes explainable OpenCV-based forensic visual analysis on identity documents:
1. Sharpness / blur analysis (Laplacian variance)
2. Compression inconsistency / Error Level Analysis (ELA)
3. Local background noise consistency across spatial regions
4. Edge density & sharpness discontinuity analysis
5. Copy-move / duplicate region detection (SIFT feature clustering)
6. Document boundary / tight crop detection
7. Digital editing software metadata inspection

Performance & Reliability:
- Vectorized NumPy & OpenCV operations (no nested Python pixel loops)
- Target execution time < 1.0s on standard CPU
- Large images auto-downscaled preserving aspect ratio
- Resilient error handling (graceful NOT_AVAILABLE on corrupted/tiny images)
- Screening aid only — flags suspicious anomalies without claiming absolute proof
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from app.services.document_analysis.integrity_engine import run_document_integrity_pipeline

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
MIN_IMAGE_DIMENSION = 50
MAX_ANALYSIS_DIMENSION = 1200
FEATURE_ANALYSIS_DIMENSION = 600

# Scoring threshold interpretation:
# 0 - 19: PASS (low risk / consistent visual characteristics)
# 20 - 49: WARNING (moderate anomalies / localized variations)
# 50 - 100: FAIL (multiple significant forensic inconsistencies)
PASS_MAX_RISK = 19
WARNING_MAX_RISK = 49


# ---------------------------------------------------------------------------
# Internal Helpers: Decoding & Preprocessing
# ---------------------------------------------------------------------------

def _decode_and_sanitize_image(
    image_bytes: bytes,
    mime_type: str,
) -> Tuple[Optional[np.ndarray], Optional[Dict[str, Any]], Optional[str]]:
    """Decode raw image bytes into BGR array with metadata.

    Returns:
        (bgr_image, metadata_dict, error_message)
    """
    if not image_bytes:
        return None, None, "Empty image payload"

    clean_mime = (mime_type or "").strip().lower()
    if clean_mime and clean_mime not in SUPPORTED_MIME_TYPES:
        return None, None, f"Unsupported MIME type: {mime_type}"

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        metadata: Dict[str, Any] = {
            "format": pil_img.format,
            "mode": pil_img.mode,
            "info": dict(pil_img.info) if hasattr(pil_img, "info") else {},
        }
        # Safely extract quantization tables if JPEG
        if hasattr(pil_img, "quantization") and pil_img.quantization:
            try:
                metadata["quantization"] = pil_img.quantization
            except Exception:
                pass

        # Safely extract basic EXIF if available
        if hasattr(pil_img, "getexif"):
            try:
                exif = pil_img.getexif()
                if exif:
                    metadata["exif"] = {str(k): str(v) for k, v in exif.items()}
            except Exception:
                pass

        # Convert to RGB (handles RGBA, Palette, Grayscale, CMYK, etc.)
        rgb_img = pil_img.convert("RGB")
        arr = np.array(rgb_img, dtype=np.uint8)
        # Convert RGB to BGR for OpenCV
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    except Exception as exc:
        logger.warning("Tamper detector: failed to decode image: %s", exc)
        return None, None, "Corrupted or unreadable image data"

    h, w = bgr.shape[:2]
    if h < MIN_IMAGE_DIMENSION or w < MIN_IMAGE_DIMENSION:
        return None, None, f"Image resolution too small ({w}x{h}) for forensic analysis"

    # Resize if image exceeds maximum analysis dimension (preserves aspect ratio)
    max_dim = max(h, w)
    if max_dim > MAX_ANALYSIS_DIMENSION:
        scale = MAX_ANALYSIS_DIMENSION / float(max_dim)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        bgr = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return bgr, metadata, None


# ---------------------------------------------------------------------------
# Indicator A: Image Quality & Sharpness (Laplacian Variance)
# ---------------------------------------------------------------------------

def _check_sharpness(gray: np.ndarray) -> Dict[str, Any]:
    """Inspect image blur, focus quality, and localized sharpness disparity."""
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    h, w = gray.shape[:2]

    # Block-level sharpness variance
    grid_rows, grid_cols = 8, 8
    bh, bw = max(4, h // grid_rows), max(4, w // grid_cols)
    local_vars = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            patch = gray[r * bh:min(h, (r + 1) * bh), c * bw:min(w, (c + 1) * bw)]
            if patch.shape[0] > 5 and patch.shape[1] > 5:
                local_vars.append(float(cv2.Laplacian(patch, cv2.CV_64F).var()))

    max_local = float(max(local_vars)) if local_vars else 0.0
    med_local = float(np.median(local_vars)) if local_vars else 1.0
    sharp_ratio = max_local / (med_local + 5.0)

    # Check for extreme localized sharpness disparity (pasted sharp elements on soft doc)
    if max_local >= 400.0 and sharp_ratio >= 20.0 and med_local < 30.0:
        score = 20
        status = "WARNING"
        reason = f"Extreme local sharpness disparity detected across document regions (peak {max_local:.0f} vs median {med_local:.1f})"
    elif laplacian_var < 25.0:
        score = 15
        status = "WARNING"
        reason = f"Image is significantly blurred (sharpness {laplacian_var:.1f}), forensic confidence reduced"
    elif laplacian_var < 55.0:
        score = 5
        status = "PASS"
        reason = f"Image has mild softness (sharpness {laplacian_var:.1f}), within acceptable limits"
    else:
        score = 0
        status = "PASS"
        reason = f"Image sharpness is good (sharpness {laplacian_var:.1f})"

    return {
        "name": "blur_quality",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": round(laplacian_var, 1),
    }


# ---------------------------------------------------------------------------
# Indicator B: Compression Inconsistency / Error Level Analysis (ELA)
# ---------------------------------------------------------------------------

def _check_compression_inconsistency(bgr: np.ndarray) -> Dict[str, Any]:
    """Perform Error Level Analysis (ELA) across spatial patches."""
    h, w = bgr.shape[:2]
    # Recompress to JPEG at quality 90 in memory
    success, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not success or encoded is None:
        return {
            "name": "compression_inconsistency",
            "status": "PASS",
            "score": 0,
            "reason": "Compression analysis unavailable",
        }

    recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if recompressed is None:
        return {
            "name": "compression_inconsistency",
            "status": "PASS",
            "score": 0,
            "reason": "Recompression decode failed",
        }

    # Absolute difference between original and re-saved image, magnified 10x
    diff = cv2.absdiff(bgr, recompressed).astype(np.float32) * 10.0
    ela_map = np.mean(diff, axis=2)

    # Compute block-level statistics across an 8x8 grid
    grid_rows, grid_cols = 8, 8
    block_h = max(4, h // grid_rows)
    block_w = max(4, w // grid_cols)

    block_means = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            y1, y2 = r * block_h, min(h, (r + 1) * block_h)
            x1, x2 = c * block_w, min(w, (c + 1) * block_w)
            if y2 > y1 and x2 > x1:
                block_means.append(float(np.mean(ela_map[y1:y2, x1:x2])))

    if not block_means:
        return {
            "name": "compression_inconsistency",
            "status": "PASS",
            "score": 0,
            "reason": "Insufficient spatial area for compression analysis",
        }

    max_ela = float(max(block_means))
    median_ela = float(np.median(block_means))
    ratio = max_ela / (median_ela + 0.5)

    # Clean single-pass documents have magnified ELA error < 25.0 (raw pixel diff < 2.5)
    if max_ela < 25.0:
        score = 0
        status = "PASS"
        reason = "Uniform single-pass compression levels consistent with authentic document"
    elif max_ela >= 50.0 and ratio >= 4.0:
        score = 25
        status = "WARNING"
        reason = f"High localized compression variance detected via ELA (peak={max_ela/10.0:.1f}, ratio={ratio:.1f})"
    elif max_ela >= 32.0 and ratio >= 2.5:
        score = 12
        status = "WARNING"
        reason = f"Moderate compression error variation detected across document regions (ratio={ratio:.1f})"
    else:
        score = 0
        status = "PASS"
        reason = "Normal compression consistency without isolated artifact spikes"

    return {
        "name": "compression_inconsistency",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": round(ratio, 2),
    }


# ---------------------------------------------------------------------------
# Indicator C: Local Noise Inconsistency
# ---------------------------------------------------------------------------

def _check_noise_inconsistency(gray: np.ndarray) -> Dict[str, Any]:
    """Examine localized background sensor noise residuals using edge masking."""
    h, w = gray.shape[:2]
    # Mask out high-contrast edges so we inspect true background / surface noise
    edges = cv2.Canny(gray, 50, 150)
    dilated_edges = cv2.dilate(edges, np.ones((5, 5), np.uint8))
    smooth_mask = (dilated_edges == 0)

    denoised = cv2.medianBlur(gray, 3)
    noise = cv2.absdiff(gray, denoised).astype(np.float32)

    grid_rows, grid_cols = 8, 8
    block_h = max(4, h // grid_rows)
    block_w = max(4, w // grid_cols)

    smooth_stds = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            y1, y2 = r * block_h, min(h, (r + 1) * block_h)
            x1, x2 = c * block_w, min(w, (c + 1) * block_w)
            patch_noise = noise[y1:y2, x1:x2]
            patch_smooth = smooth_mask[y1:y2, x1:x2]
            if np.sum(patch_smooth) > 100:
                smooth_stds.append(float(np.std(patch_noise[patch_smooth])))

    if not smooth_stds:
        return {
            "name": "noise_inconsistency",
            "status": "PASS",
            "score": 0,
            "reason": "Noise analysis skipped",
        }

    max_std = float(max(smooth_stds))
    median_std = float(np.median(smooth_stds))
    ratio = max_std / (median_std + 0.2)

    # Clean flat/scanned images have max smooth noise std < 1.5
    if max_std < 1.5:
        score = 0
        status = "PASS"
        reason = "Clean and uniform surface texture across document background"
    elif max_std >= 3.0 and ratio >= 4.0:
        score = 20
        status = "WARNING"
        reason = f"Abnormal localized sensor noise disparity detected across background regions (peak={max_std:.1f})"
    elif max_std >= 2.0 and ratio >= 2.5:
        score = 10
        status = "WARNING"
        reason = f"Mild localized noise variance detected across document patches (ratio={ratio:.1f})"
    else:
        score = 0
        status = "PASS"
        reason = "Natural sensor noise distribution is consistent across document surface"

    return {
        "name": "noise_inconsistency",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": round(ratio, 2),
    }


# ---------------------------------------------------------------------------
# Indicator D: Edge & Sharpness Inconsistency
# ---------------------------------------------------------------------------

def _check_edge_inconsistency(gray: np.ndarray) -> Dict[str, Any]:
    """Detect anomalous sharp rectangular boundaries or gradient spikes."""
    h, w = gray.shape[:2]
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(sobelx, sobely)

    grid_rows, grid_cols = 8, 8
    block_h = max(4, h // grid_rows)
    block_w = max(4, w // grid_cols)

    densities = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            y1, y2 = r * block_h, min(h, (r + 1) * block_h)
            x1, x2 = c * block_w, min(w, (c + 1) * block_w)
            if y2 > y1 and x2 > x1:
                patch = magnitude[y1:y2, x1:x2]
                densities.append(float(np.mean(patch > 60.0)))

    if not densities:
        return {
            "name": "edge_inconsistency",
            "status": "PASS",
            "score": 0,
            "reason": "Edge analysis skipped",
        }

    max_edge = float(max(densities))
    median_edge = float(np.median(densities))
    ratio = max_edge / (median_edge + 0.05)

    if max_edge >= 0.35 and ratio >= 5.0:
        score = 15
        status = "WARNING"
        reason = f"Isolated high-gradient border density detected (peak={max_edge:.2f}, ratio={ratio:.1f})"
    elif max_edge >= 0.25 and ratio >= 3.5:
        score = 8
        status = "PASS"
        reason = "Normal document edge transitions observed (text and photo boundaries)"
    else:
        score = 0
        status = "PASS"
        reason = "Continuous edge gradient distribution without anomalous sharp boundaries"

    return {
        "name": "edge_inconsistency",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": round(ratio, 2),
    }


# ---------------------------------------------------------------------------
# Indicator E: Duplicate Region / Copy-Move Cloning (SIFT Matching)
# ---------------------------------------------------------------------------

def _check_duplicate_regions(gray: np.ndarray) -> Dict[str, Any]:
    """Detect potential copy-move cloning using fast SIFT feature displacement clustering."""
    h, w = gray.shape[:2]
    # Bound image size for fast execution (< 60ms)
    scale = 1.0
    if max(h, w) > FEATURE_ANALYSIS_DIMENSION:
        scale = FEATURE_ANALYSIS_DIMENSION / float(max(h, w))
        small = cv2.resize(gray, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    else:
        small = gray

    try:
        sift = cv2.SIFT_create(nfeatures=250)
        keypoints, descriptors = sift.detectAndCompute(small, None)
    except Exception as exc:
        logger.debug("Tamper detector: SIFT feature computation skipped: %s", exc)
        return {
            "name": "duplicate_regions",
            "status": "PASS",
            "score": 0,
            "reason": "Duplicate region analysis unavailable",
        }

    if descriptors is None or len(descriptors) < 20:
        return {
            "name": "duplicate_regions",
            "status": "PASS",
            "score": 0,
            "reason": "Insufficient distinct texture features for copy-move analysis",
        }

    # Pairwise feature matching using L2 distance
    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(descriptors, descriptors, k=2)

    pts = np.array([k.pt for k in keypoints])
    diffs = []

    for m in matches:
        if len(m) < 2:
            continue
        m2 = m[1]
        # Match distance threshold for near-identical feature descriptors
        if m2.distance < 120.0:
            p1 = pts[m2.queryIdx]
            p2 = pts[m2.trainIdx]
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            dist = np.hypot(dx, dy)
            # Require significant spatial separation and exclude pure vertical line repetition
            if dist > 40.0 and dx > 15.0:
                diffs.append(p2 - p1)

    max_cluster = 0
    if diffs:
        bins = np.round(np.array(diffs) / 25.0).astype(int)
        _, counts = np.unique(bins, axis=0, return_counts=True)
        max_cluster = int(np.max(counts))

    if max_cluster >= 6:
        score = 35
        status = "FAIL"
        reason = f"Potential copy-move duplicated region detected ({max_cluster} aligned feature pairs)"
    elif max_cluster >= 5:
        score = 15
        status = "WARNING"
        reason = f"Minor duplicate texture pattern detected ({max_cluster} matching feature pairs)"
    else:
        score = 0
        status = "PASS"
        reason = "No recurring cloned or duplicated regions identified"

    return {
        "name": "duplicate_regions",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": max_cluster,
    }


# ---------------------------------------------------------------------------
# Indicator F: Suspicious Crop & Boundary Margins
# ---------------------------------------------------------------------------

def _check_boundary_crop(gray: np.ndarray) -> Dict[str, Any]:
    """Inspect outer image borders for abnormal clipping or cropped security features."""
    h, w = gray.shape[:2]
    margin_y = max(2, int(h * 0.03))
    margin_x = max(2, int(w * 0.03))

    top = gray[:margin_y, :]
    bottom = gray[h - margin_y:, :]
    left = gray[:, :margin_x]
    right = gray[:, w - margin_x:]

    border_stds = [float(np.std(top)), float(np.std(bottom)), float(np.std(left)), float(np.std(right))]
    high_border_activity = sum(1 for s in border_stds if s > 55.0)

    if high_border_activity >= 3:
        score = 8
        status = "WARNING"
        reason = "Document appears tightly cropped with content flush against image boundaries"
    else:
        score = 0
        status = "PASS"
        reason = "Document framing and margins appear natural"

    return {
        "name": "boundary_crop",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": high_border_activity,
    }


# ---------------------------------------------------------------------------
# Indicator G: Editing Software Metadata Inspection
# ---------------------------------------------------------------------------

def _check_metadata_signatures(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Check for digital image editing suite signatures in metadata headers."""
    if not metadata:
        return {
            "name": "metadata_integrity",
            "status": "PASS",
            "score": 0,
            "reason": "Metadata stripped or absent (standard for mobile capture)",
        }

    editing_tools = [
        "photoshop", "gimp", "canva", "paint.net", "adobe",
        "illustrator", "pixlr", "snapseed", "lightroom",
    ]

    found_tools = []
    text_blob = str(metadata).lower()
    for tool in editing_tools:
        if tool in text_blob:
            found_tools.append(tool.title())

    if found_tools:
        score = 20
        status = "WARNING"
        tools_str = ", ".join(sorted(set(found_tools)))
        reason = f"Image metadata references photo manipulation software: {tools_str}"
    else:
        score = 0
        status = "PASS"
        reason = "No digital manipulation software signatures found in metadata"

    return {
        "name": "metadata_integrity",
        "status": status,
        "score": score,
        "reason": reason,
        "metric": len(found_tools),
    }


# ---------------------------------------------------------------------------
# Main Public Service
# ---------------------------------------------------------------------------

def detect_tampering(
    image_bytes: bytes,
    mime_type: str,
    extracted_data: Optional[Dict[str, Any]] = None,
    mrz_lines: Optional[Tuple[Optional[str], Optional[str]]] = None,
) -> Dict[str, Any]:
    """Screen identity document for visual tampering, forgery, and data integrity.

    Args:
        image_bytes: Raw binary bytes of uploaded identity document.
        mime_type: MIME type string (e.g. 'image/jpeg', 'image/png').
        extracted_data: Optional dictionary of OCR-extracted fields for cross-validation.
        mrz_lines: Optional (mrz_line_1, mrz_line_2) tuple if MRZ was extracted.

    Returns:
        Dict adhering to the pipeline check contract with layered forensic insights:
        {
            "status": "PASS" | "WARNING" | "FAIL" | "NOT_AVAILABLE",
            "risk": int (0 to 100),
            "reason": str,
            "recommendation": "CLEAR" | "MANUAL_REVIEW_RECOMMENDED" | "SECONDARY_INSPECTION_RECOMMENDED",
            "confidence": "HIGH" | "MEDIUM" | "LOW",
            "checks": List[Dict[str, Any]],
            "sub_checks": Dict[str, Any],
            "document_quality": Dict[str, Any],
            "field_analysis": List[Dict[str, Any]],
            "highlighted_regions": List[Dict[str, Any]],
            "cross_field_consistency": Dict[str, Any],
            "ai_manipulation": Dict[str, Any],
        }
    """
    bgr, metadata, err = _decode_and_sanitize_image(image_bytes, mime_type)
    if err is not None or bgr is None:
        return {
            "status": "NOT_AVAILABLE",
            "risk": None,
            "reason": f"Tamper screening unavailable: {err or 'unreadable image'}",
            "recommendation": "MANUAL_REVIEW_RECOMMENDED",
            "confidence": "LOW",
            "checks": [],
            "sub_checks": {},
            "document_quality": {"status": "UNAVAILABLE", "score": 0, "confidence": "LOW"},
            "field_analysis": [],
            "highlighted_regions": [],
            "cross_field_consistency": {"status": "NOT_AVAILABLE", "has_mismatch": False},
            "ai_manipulation": {"indicator": "LOW", "score": 0},
        }

    try:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    except Exception as exc:
        logger.warning("Tamper detector: grayscale conversion failed: %s", exc)
        return {
            "status": "NOT_AVAILABLE",
            "risk": None,
            "reason": "Image color conversion failed",
            "recommendation": "MANUAL_REVIEW_RECOMMENDED",
            "confidence": "LOW",
            "checks": [],
            "sub_checks": {},
            "document_quality": {"status": "UNAVAILABLE", "score": 0, "confidence": "LOW"},
            "field_analysis": [],
            "highlighted_regions": [],
            "cross_field_consistency": {"status": "NOT_AVAILABLE", "has_mismatch": False},
            "ai_manipulation": {"indicator": "LOW", "score": 0},
        }

    # 1. Execute legacy independent visual indicators (preserves compatibility)
    legacy_indicators: List[Dict[str, Any]] = [
        _check_sharpness(gray),
        _check_compression_inconsistency(bgr),
        _check_noise_inconsistency(gray),
        _check_edge_inconsistency(gray),
        _check_duplicate_regions(gray),
        _check_boundary_crop(gray),
        _check_metadata_signatures(metadata),
    ]

    legacy_score = sum(ind.get("score", 0) for ind in legacy_indicators)

    # 2. Execute deep layered Document Integrity & Risk Engine
    layered_res = run_document_integrity_pipeline(
        bgr=bgr,
        gray=gray,
        metadata=metadata,
        extracted_data=extracted_data,
        mrz_lines=mrz_lines,
    )

    # 3. Fuse scores (deterministic cross-field mismatch takes highest priority)
    fused_risk = max(legacy_score, layered_res["risk"])
    if layered_res["cross_field_consistency"].get("has_mismatch"):
        fused_risk = max(fused_risk, 78)

    clamped_risk = max(0, min(100, int(round(fused_risk))))

    # 4. Determine final classification
    if clamped_risk >= 50 or layered_res["cross_field_consistency"].get("has_mismatch"):
        status = "FAIL"
        recommendation = "SECONDARY_INSPECTION_RECOMMENDED"
    elif clamped_risk >= 20:
        status = "WARNING"
        recommendation = "MANUAL_REVIEW_RECOMMENDED"
    else:
        status = "PASS"
        recommendation = layered_res.get("recommendation", "CLEAR")

    # Formulate explainable summary reason
    reasons = layered_res.get("reasons", [])
    if not reasons:
        legacy_anomalies = [
            ind["reason"]
            for ind in legacy_indicators
            if ind["status"] in ("WARNING", "FAIL") and ind.get("score", 0) > 0
        ]
        reasons = legacy_anomalies

    if status == "FAIL":
        if reasons:
            reason = "Multiple significant tamper indicators detected: " + "; ".join(reasons[:2])
        else:
            reason = "Elevated composite forensic tamper risk detected across document visual features"
    elif status == "WARNING":
        if reasons:
            reason = "Document visual anomaly detected: " + "; ".join(reasons[:2])
        else:
            reason = "Moderate localized visual inconsistency detected, manual verification recommended"
    else:
        if layered_res["document_quality"]["status"] == "ACCEPTABLE":
            reason = "No significant visual tamper indicators detected. Compression, typography, and texture appear consistent."
        else:
            reason = f"No clear tamper indicators detected. {layered_res['document_quality']['summary']}"

    def _sanitize(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: _sanitize(v) for k, v in val.items()}
        elif isinstance(val, (list, tuple)):
            return [_sanitize(x) for x in val]
        elif isinstance(val, (np.bool_, bool)):
            return bool(val)
        elif isinstance(val, (np.integer, int)):
            return int(val)
        elif isinstance(val, (np.floating, float)):
            return float(val)
        return val

    return _sanitize({
        "status": status,
        "risk": clamped_risk,
        "reason": reason,
        "recommendation": recommendation,
        "confidence": layered_res["confidence"],
        "checks": legacy_indicators,
        "sub_checks": layered_res["sub_checks"],
        "document_quality": layered_res["document_quality"],
        "field_analysis": layered_res["field_analysis"],
        "highlighted_regions": layered_res["highlighted_regions"],
        "cross_field_consistency": layered_res["cross_field_consistency"],
        "ai_manipulation": layered_res["ai_manipulation"],
        "reasons": reasons,
    })
