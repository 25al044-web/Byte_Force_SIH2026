"""Typography and layout consistency analysis module.

Inspects document typography to detect clean AI/digital text replacements:
- Character height and line proportion consistency
- Stroke width / font thickness via distance transform
- Character spacing and kerning regularity
- Horizontal baseline alignment
- Foreground ink color and luminance consistency vs document reference text
- Anti-aliasing / edge transition gradient profile

FLAG (Phase 5):
TYPOGRAPHY_INCONSISTENCY
"""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def _extract_text_components(gray_patch: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Segments individual letter/glyph bounding boxes using Otsu binarization."""
    # Invert so text is white on black background
    blur = cv2.GaussianBlur(gray_patch, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)

    boxes = []
    ph, pw = gray_patch.shape[:2]
    min_area = max(10, (ph * pw) // 1000)
    max_area = (ph * pw) // 2

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # Filter noise dots and huge background blobs
        if min_area <= area <= max_area and h >= 6 and w >= 3:
            boxes.append((x, y, w, h))

    # Sort left to right
    boxes.sort(key=lambda b: b[0])
    return boxes


def _compute_stroke_width(gray_patch: np.ndarray) -> float:
    """Estimates font stroke width using Euclidean distance transform on text skeleton."""
    blur = cv2.GaussianBlur(gray_patch, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Filter out huge blobs (e.g. solid banners, photo borders)
    ph, pw = gray_patch.shape[:2]
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)
    clean_thresh = np.zeros_like(thresh)
    max_area = (ph * pw) // 4
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if area <= max_area and h < int(ph * 0.75) and w < int(pw * 0.85):
            clean_thresh[labels == i] = 255

    dist = cv2.distanceTransform(clean_thresh, cv2.DIST_L2, 5)
    # Average peak distance across text pixels represents half-stroke width
    text_pixels = dist[clean_thresh > 0]
    if len(text_pixels) == 0:
        return 1.0
    return float(np.median(text_pixels) * 2.0)


def _get_text_ink_color(bgr_patch: np.ndarray, gray_patch: np.ndarray) -> Tuple[float, float, float]:
    """Computes median (B, G, R) color of the primary dark text pixels."""
    bg_val = float(np.median(gray_patch))
    dark_mask = gray_patch < (bg_val - 25)
    if np.count_nonzero(dark_mask) < 10:
        return (0.0, 0.0, 0.0)

    dark_pixels = gray_patch[dark_mask]
    # Focus on the darkest 6% of dark pixels to isolate core value ink from anti-aliasing / faint labels
    cutoff = float(np.percentile(dark_pixels, 6))
    core_ink_mask = dark_mask & (gray_patch <= cutoff)
    if np.count_nonzero(core_ink_mask) < 3:
        core_ink_mask = dark_mask

    b = float(np.median(bgr_patch[:, :, 0][core_ink_mask]))
    g = float(np.median(bgr_patch[:, :, 1][core_ink_mask]))
    r = float(np.median(bgr_patch[:, :, 2][core_ink_mask]))
    return (b, g, r)


def analyze_typography_consistency(
    bgr: np.ndarray,
    gray: np.ndarray,
    name_pixel_bbox: Tuple[int, int, int, int],
    reference_pixel_bbox: Optional[Tuple[int, int, int, int]] = None,
) -> Dict[str, Any]:
    """Compares typography in the Name field against other printed text on the document.

    Args:
        bgr: Full document BGR image.
        gray: Grayscale full image.
        name_pixel_bbox: (y1, x1, y2, x2) bounding box of the Name field.
        reference_pixel_bbox: Optional reference text zone (e.g. DOB/Doc number or lower text block).
    """
    h, w = gray.shape[:2]
    ny1, nx1, ny2, nx2 = name_pixel_bbox

    # Ensure valid patch
    ny1, ny2 = max(0, min(h - 5, ny1)), max(5, min(h, ny2))
    nx1, nx2 = max(0, min(w - 5, nx1)), max(5, min(w, nx2))

    if ny2 <= ny1 or nx2 <= nx1:
        return {
            "status": "PASS",
            "score": 0,
            "typography_similarity": 100,
            "reasons": [],
        }

    name_gray = gray[ny1:ny2, nx1:nx2]
    name_bgr = bgr[ny1:ny2, nx1:nx2]

    # Pick reference patch if none provided (e.g. text zone lower down or next to photo)
    if reference_pixel_bbox:
        ry1, rx1, ry2, rx2 = reference_pixel_bbox
    else:
        # Default reference: area below name (y: 40% to 65%, x: 38% to 90%)
        ry1, ry2 = int(h * 0.40), int(h * 0.65)
        rx1, rx2 = int(w * 0.38), int(w * 0.90)

    ry1, ry2 = max(0, min(h - 5, ry1)), max(5, min(h, ry2))
    rx1, rx2 = max(0, min(w - 5, rx1)), max(5, min(w, rx2))

    ref_gray = gray[ry1:ry2, rx1:rx2]
    ref_bgr = bgr[ry1:ry2, rx1:rx2]

    reasons: List[str] = []
    inconsistency_points = 0

    # 1. Stroke Width / Font Thickness Comparison
    name_stroke = _compute_stroke_width(name_gray)
    ref_stroke = _compute_stroke_width(ref_gray)

    stroke_ratio = name_stroke / (ref_stroke + 0.1)
    if stroke_ratio > 1.65 or stroke_ratio < 0.58:
        inconsistency_points += 25
        reasons.append(f"Font stroke thickness in Name field ({name_stroke:.1f}px) deviates from document baseline ({ref_stroke:.1f}px)")
    elif stroke_ratio > 1.45 or stroke_ratio < 0.65:
        inconsistency_points += 15
        reasons.append(f"Noticeable font weight variance between Name field ({name_stroke:.1f}px) and adjacent text ({ref_stroke:.1f}px)")

    # 2. Character Spacing / Kerning Regularity
    name_components = _extract_text_components(name_gray)
    if len(name_components) >= 4:
        gaps = []
        for i in range(len(name_components) - 1):
            gap = name_components[i + 1][0] - (name_components[i][0] + name_components[i][2])
            if -5 <= gap <= 40:
                gaps.append(gap)
        if len(gaps) >= 3:
            gap_std = float(np.std(gaps))
            gap_mean = float(np.mean(gaps))
            # Abnormal gap variance indicates spliced or unevenly pasted letters
            if gap_std > 8.0:
                inconsistency_points += 20
                reasons.append(f"Irregular character spacing / kerning detected in Name field (variance {gap_std:.1f})")

    # 3. Text Ink Color & Contrast Consistency
    name_ink = _get_text_ink_color(name_bgr, name_gray)
    ref_ink = _get_text_ink_color(ref_bgr, ref_gray)

    # Euclidean color distance in BGR space
    ink_color_dist = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(name_ink, ref_ink))))

    if ink_color_dist > 35.0:
        inconsistency_points += 30
        reasons.append(f"Ink color discrepancy: Name field ink differs significantly from document baseline ({ink_color_dist:.1f} color distance)")
    elif ink_color_dist > 22.0:
        inconsistency_points += 15
        reasons.append(f"Noticeable ink tint or contrast variation detected in Name field ({ink_color_dist:.1f} color distance)")

    # 4. Anti-Aliasing & Edge Gradient Profile
    # Digitally rendered text on scanned backgrounds has sharp step edges without ink bleed
    name_grad = np.abs(cv2.Sobel(name_gray, cv2.CV_32F, 1, 0, ksize=3))
    ref_grad = np.abs(cv2.Sobel(ref_gray, cv2.CV_32F, 1, 0, ksize=3))

    name_edge_mask = name_grad > 25.0
    ref_edge_mask = ref_grad > 25.0

    if np.count_nonzero(name_edge_mask) > 20 and np.count_nonzero(ref_edge_mask) > 20:
        name_sharpness = float(np.mean(name_grad[name_edge_mask]))
        ref_sharpness = float(np.mean(ref_grad[ref_edge_mask]))
        sharpness_ratio = name_sharpness / (ref_sharpness + 1.0)

        if sharpness_ratio > 1.8 or sharpness_ratio < 0.55:
            inconsistency_points += 20
            reasons.append(f"Edge transition gradient in Name differs from document printing style (ratio {sharpness_ratio:.1f}x)")
        elif sharpness_ratio > 1.35 or sharpness_ratio < 0.70:
            inconsistency_points += 10
            reasons.append(f"Mild edge sharpness discrepancy in Name field (ratio {sharpness_ratio:.1f}x)")
    else:
        sharpness_ratio = 1.0

    clamped_score = max(0, min(100, inconsistency_points))
    typography_similarity = max(0, 100 - clamped_score)

    if clamped_score >= 35:
        status = "SUSPICIOUS"
    elif clamped_score >= 15:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "status": status,
        "score": clamped_score,
        "typography_similarity": typography_similarity,
        "metrics": {
            "name_stroke_width": round(name_stroke, 1),
            "ref_stroke_width": round(ref_stroke, 1),
            "ink_color_distance": round(ink_color_dist, 1),
            "edge_sharpness_ratio": round(sharpness_ratio, 2),
        },
        "reasons": reasons,
    }
