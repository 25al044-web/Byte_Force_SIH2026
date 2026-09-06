"""AI-edit and generative manipulation indicator module.

Inspects document text and background regions for generative inpainting signatures:
- Background texture suppression / unnatural over-smoothing behind modified text
- Bounding envelope blend seam transitions
- Frequency spectrum anomalies characteristic of neural diffusion/inpainting
- Generative tool metadata signatures (Photoshop Generative Fill, Canva, Firefly, etc.)

RULE (Phase 9):
Treat as an explainable supplementary signal (LOW / MEDIUM / HIGH).
A high AI-edit score alone does not automatically mean fraud; it combines with other evidence.
"""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def detect_ai_manipulation(
    bgr: np.ndarray,
    gray: np.ndarray,
    metadata: Optional[Dict[str, Any]] = None,
    field_bboxes: Optional[List[Tuple[int, int, int, int]]] = None,
) -> Dict[str, Any]:
    """Evaluates indicators of generative AI editing or inpainting."""
    h, w = gray.shape[:2]
    reasons: List[str] = []
    points = 0

    # 1. Metadata Inspection for AI tools
    if metadata:
        meta_str = str(metadata).lower()
        ai_signatures = [
            ("generative fill", "Adobe Generative Fill"),
            ("firefly", "Adobe Firefly"),
            ("stable diffusion", "Stable Diffusion Inpainting"),
            ("midjourney", "Midjourney"),
            ("dall-e", "DALL-E"),
            ("inpainting", "Digital Inpainting Suite"),
            ("photoshop", "Adobe Photoshop"),
            ("canva", "Canva Magic Edit"),
            ("gimp", "GIMP"),
            ("pixlr", "Pixlr AI"),
        ]
        for keyword, label in ai_signatures:
            if keyword in meta_str:
                points += 30
                reasons.append(f"Image metadata indicates manipulation with {label}")
                break

    # 2. Local Texture Variance Suppression (Inpainting Dead-Zone)
    # If field_bboxes provided (e.g. Name, DOB), inspect their background pixels
    if field_bboxes:
        doc_edges = cv2.Canny(gray, 40, 120)
        doc_smooth_mask = (doc_edges == 0)

        # Baseline noise variance in whole document smooth areas
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        doc_smooth_variance = float(np.var(laplacian[doc_smooth_mask])) if np.count_nonzero(doc_smooth_mask) > 500 else 10.0

        for idx, (y1, x1, y2, x2) in enumerate(field_bboxes):
            y1, y2 = max(0, min(h - 5, y1)), max(5, min(h, y2))
            x1, x2 = max(0, min(w - 5, x1)), max(5, min(w, x2))
            if (y2 - y1) < 15 or (x2 - x1) < 30:
                continue

            patch_gray = gray[y1:y2, x1:x2]
            patch_edges = cv2.Canny(patch_gray, 40, 120)
            patch_smooth_mask = (patch_edges == 0)

            if np.count_nonzero(patch_smooth_mask) > 100:
                patch_lap = cv2.Laplacian(patch_gray, cv2.CV_64F)
                patch_smooth_var = float(np.var(patch_lap[patch_smooth_mask]))

                # If document background has natural texture (var > 2.0),
                # but field background has near-zero texture (var < 0.25):
                if doc_smooth_variance > 3.0 and patch_smooth_var < 0.3:
                    points += 25
                    reasons.append(f"Artificial texture suppression / inpainting signature detected in field #{idx+1}")
                    break

    # 3. Patch Seam Gradient Inspection
    # Inpainted regions often have subtle boundary step changes
    denoised = cv2.fastNlMeansDenoising(gray, None, h=7, templateWindowSize=5, searchWindowSize=15)
    noise_residual = cv2.absdiff(gray, denoised)
    local_std = cv2.blur(noise_residual.astype(np.float32), (15, 15))

    # Variance of local standard deviation across the document
    std_spread = float(np.std(local_std))
    if std_spread > 4.5:
        points += 15
        reasons.append("Irregular localized noise variance distribution consistent with composite editing")

    clamped_score = max(0, min(100, points))

    if clamped_score >= 50:
        indicator = "HIGH"
    elif clamped_score >= 20:
        indicator = "MEDIUM"
    else:
        indicator = "LOW"

    return {
        "indicator": indicator,
        "score": clamped_score,
        "reasons": reasons,
        "metrics": {
            "ai_evidence_score": clamped_score,
            "metadata_flag": len(reasons) > 0 and "metadata" in reasons[0].lower(),
        },
    }
