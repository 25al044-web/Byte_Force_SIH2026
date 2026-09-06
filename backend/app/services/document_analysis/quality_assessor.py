"""Document quality assessment module.

Evaluates photographic and scanning quality metrics:
- Blur & focus sharpness (Laplacian variance + edge energy)
- Spatial resolution (megapixels, width x height)
- Compression degradation (compression artifacts / recompression level)
- Illumination & contrast clipping (overexposure, underexposure)

CRITICAL RULE (Phase 14 & 15):
Quality degradation (blur, screenshot, heavy JPEG compression) must be
classified as quality issues / uncertainty warnings, NOT fraudulent tampering.
"""

from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


def assess_image_quality(
    bgr: np.ndarray,
    gray: np.ndarray,
    original_format: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Inspects document image quality independent of document tampering.

    Args:
        bgr: Decoded image in BGR format.
        gray: Grayscale representation.
        original_format: Original format string if known ('JPEG', 'PNG', etc.).
        metadata: Optional image metadata dict containing EXIF and quantization tables.

    Returns:
        Structured dictionary with quality assessment metrics and flags.
    """
    h, w = gray.shape[:2]
    total_pixels = h * w

    # 1. Blur & Focus Sharpness (Laplacian variance)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = float(laplacian.var())

    # High frequency Sobel ratio (fraction of pixels with significant gradient)
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient_mag = cv2.magnitude(sobelx, sobely)
    edge_fraction = float(np.count_nonzero(gradient_mag > 40.0) / max(1, total_pixels))

    is_heavy_blur = laplacian_var < 25.0
    is_mild_blur = 25.0 <= laplacian_var < 55.0

    # 2. Spatial Resolution
    is_low_res = (w < 400 or h < 300 or total_pixels < 200_000)
    is_optimal_res = (w >= 800 and h >= 600)

    # 3. Compression Level Estimation
    is_heavy_compression = False

    # Check JPEG quantization table if present in metadata
    if metadata and "quantization" in metadata:
        q_dict = metadata["quantization"]
        if isinstance(q_dict, dict) and 0 in q_dict:
            table_0 = q_dict[0]
            if isinstance(table_0, (list, tuple)) and len(table_0) > 0:
                mean_q = float(np.mean(table_0))
                # Average quantization step >= 30 corresponds to JPEG quality <= 35
                if mean_q >= 28.0:
                    is_heavy_compression = True

    # Fallback re-encode test
    if not is_heavy_compression:
        success_90, enc_90 = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if success_90:
            dec_90 = cv2.imdecode(enc_90, cv2.IMREAD_COLOR)
            diff_90 = np.mean(cv2.absdiff(bgr, dec_90))
            if diff_90 > 14.0:
                is_heavy_compression = True

    # 4. Exposure & Lighting Assessment
    dark_pixels = np.count_nonzero(gray < 15) / max(1, total_pixels)
    blown_pixels = np.count_nonzero(gray > 245) / max(1, total_pixels)
    has_extreme_glare = blown_pixels > 0.18
    is_underexposed = dark_pixels > 0.35

    # 5. Composite Quality Score (0 to 100, 100 = pristine studio scan)
    quality_score = 100

    if is_heavy_blur:
        quality_score -= 40
    elif is_mild_blur:
        quality_score -= 15

    if is_low_res:
        quality_score -= 25

    if is_heavy_compression:
        quality_score -= 20

    if has_extreme_glare:
        quality_score -= 20
    elif is_underexposed:
        quality_score -= 15

    quality_score = max(5, min(100, quality_score))

    # 6. Quality Status & Confidence
    if quality_score >= 70:
        quality_status = "ACCEPTABLE"
        confidence = "HIGH"
        summary = "Document visual quality is clear and acceptable for automated screening."
    elif quality_score >= 45:
        quality_status = "DEGRADED"
        confidence = "MEDIUM"
        reasons = []
        if is_mild_blur or is_heavy_blur:
            reasons.append("mild blur")
        if is_heavy_compression:
            reasons.append("compression artifacts")
        if is_low_res:
            reasons.append("low resolution")
        summary = f"Document visual quality is degraded ({', '.join(reasons) or 'moderate noise'}); forensic confidence reduced."
    else:
        quality_status = "POOR"
        confidence = "LOW"
        summary = "Image quality is poor (heavy blur or extreme compression). Manual review or clearer re-upload recommended."

    return {
        "status": quality_status,
        "score": quality_score,
        "confidence": confidence,
        "summary": summary,
        "metrics": {
            "sharpness": round(laplacian_var, 1),
            "edge_fraction": round(edge_fraction, 3),
            "width": w,
            "height": h,
            "megapixels": round(total_pixels / 1_000_000.0, 2),
            "is_heavy_blur": is_heavy_blur,
            "is_mild_blur": is_mild_blur,
            "is_low_res": is_low_res,
            "is_heavy_compression": is_heavy_compression,
            "has_extreme_glare": has_extreme_glare,
            "is_underexposed": is_underexposed,
        },
        "recommendation": "OK" if quality_score >= 60 else "MANUAL_REVIEW_POOR_QUALITY",
    }
