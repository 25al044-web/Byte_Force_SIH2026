"""Local and global image forensics module for identity documents.

Analyzes localized physical and digital inconsistencies:
- Local Error Level Analysis (ELA) on sensitive text fields
- Local noise residual consistency (wavelet/median residual vs reference background)
- Boundary gradient discontinuity / bounding box seams
- 2D Fourier (FFT) high-frequency spectrum analysis
- SIFT duplicate / copy-move feature clustering
"""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

FEATURE_ANALYSIS_DIM = 600


def analyze_local_field_forensics(
    bgr: np.ndarray,
    gray: np.ndarray,
    pixel_bbox: Tuple[int, int, int, int],
    field_name: str,
    precomputed_ela_map: Optional[np.ndarray] = None,
    precomputed_noise_res: Optional[np.ndarray] = None,
    precomputed_grad_mag: Optional[np.ndarray] = None,
    precomputed_mean_grad: Optional[float] = None,
    precomputed_doc_bg_noise_std: Optional[float] = None,
) -> Dict[str, Any]:
    """Inspects an individual field bounding box against document background baseline.

    Args:
        bgr: Full document BGR image.
        gray: Grayscale full image.
        pixel_bbox: (y1, x1, y2, x2) in pixel space.
        field_name: Identifier of the field (e.g. 'name', 'date_of_birth').
        precomputed_ela_map: Optional precomputed whole-document ELA map.
        precomputed_noise_res: Optional precomputed whole-document noise residual.
        precomputed_grad_mag: Optional precomputed whole-document Sobel gradient magnitude.
        precomputed_mean_grad: Optional precomputed mean gradient across document.
        precomputed_doc_bg_noise_std: Optional precomputed background noise std.

    Returns:
        Forensic anomaly metrics and composite local risk score (0 to 100).
    """
    h, w = gray.shape[:2]
    y1, x1, y2, x2 = pixel_bbox

    # Ensure valid coordinates
    y1, y2 = max(0, min(h - 5, y1)), max(5, min(h, y2))
    x1, x2 = max(0, min(w - 5, x1)), max(5, min(w, x2))

    if y2 <= y1 or x2 <= x1:
        return {"anomaly_score": 0, "status": "PASS", "reasons": []}

    patch_gray = gray[y1:y2, x1:x2]
    patch_bgr = bgr[y1:y2, x1:x2]

    reasons: List[str] = []
    anomaly_points = 0

    # 1. Local Error Level Analysis (ELA)
    if precomputed_ela_map is not None:
        ela_map = precomputed_ela_map
        success = True
    else:
        success, encoded = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if success:
            recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            diff = cv2.absdiff(bgr, recompressed).astype(np.float32)
            ela_map = np.mean(diff, axis=2)
        else:
            ela_map = None

    if success and ela_map is not None:
        # Patch ELA vs whole document ELA
        patch_ela = float(np.mean(ela_map[y1:y2, x1:x2]))
        doc_ela = float(np.mean(ela_map))

        ela_ratio = patch_ela / (doc_ela + 0.5)
        if patch_ela > 8.0 and ela_ratio > 2.2:
            anomaly_points += 30
            reasons.append(f"Localized JPEG compression anomaly in {field_name} (ELA ratio {ela_ratio:.1f}x)")
        elif patch_ela > 5.0 and ela_ratio > 1.7:
            anomaly_points += 15
            reasons.append(f"Mild compression variance around {field_name}")

    # 2. Local Noise Consistency (Background residual)
    if precomputed_noise_res is not None:
        noise_res = precomputed_noise_res
    else:
        denoised = cv2.medianBlur(gray, 3)
        noise_res = cv2.absdiff(gray, denoised).astype(np.float32)

    # Calculate noise in field vs whole image
    patch_noise_std = float(np.std(noise_res[y1:y2, x1:x2]))
    doc_noise_std = float(np.std(noise_res))

    noise_ratio = patch_noise_std / (doc_noise_std + 0.1)

    # An unnaturally smoothed background (AI inpainting) has very low noise
    # A foreign noisy patch has very high noise
    if patch_noise_std > 2.5 and noise_ratio > 2.5:
        anomaly_points += 25
        reasons.append(f"Abnormal sensor noise spike in {field_name} region (ratio {noise_ratio:.1f}x)")
    elif doc_noise_std > 3.0 and patch_noise_std < 0.35 and (y2 - y1) > 20:
        if precomputed_doc_bg_noise_std is not None:
            doc_bg_noise_std = precomputed_doc_bg_noise_std
        else:
            # Only flag smoothing if the document background actually has texture/grain
            edges = cv2.Canny(gray, 30, 100)
            dilated = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
            pure_bg = (dilated == 0) & (gray > 200)
            doc_bg_noise_std = float(np.std(noise_res[pure_bg])) if np.count_nonzero(pure_bg) > 500 else 0.0
        if doc_bg_noise_std > 2.5:
            anomaly_points += 20
            reasons.append(f"Unnatural texture smoothing / inpainting signature around {field_name}")

    # 3. Boundary Edge Step Discontinuity
    # Check if a rectangular perimeter seam exists around the field (requires both H & V steps)
    bw = max(2, min(5, (x2 - x1) // 10))
    bh = max(2, min(5, (y2 - y1) // 10))

    if precomputed_grad_mag is not None and precomputed_mean_grad is not None:
        grad_mag = precomputed_grad_mag
        mean_grad = precomputed_mean_grad
    else:
        sobel_v = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_h = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = cv2.magnitude(sobel_v, sobel_h)
        mean_grad = float(np.mean(grad_mag)) + 1.0

    outer_edge_left = float(np.mean(grad_mag[y1:y2, max(0, x1 - bw):x1 + bw])) if x1 > bw else 0
    outer_edge_right = float(np.mean(grad_mag[y1:y2, x2 - bw:min(w, x2 + bw)])) if x2 < w - bw else 0
    outer_edge_top = float(np.mean(grad_mag[max(0, y1 - bh):y1 + bh, x1:x2])) if y1 > bh else 0
    outer_edge_bottom = float(np.mean(grad_mag[y2 - bh:min(h, y2 + bh), x1:x2])) if y2 < h - bh else 0

    h_step = max(outer_edge_left, outer_edge_right) / mean_grad
    v_step = max(outer_edge_top, outer_edge_bottom) / mean_grad

    # Spliced patches have sharp step edges on both horizontal and vertical perimeters
    if h_step > 3.5 and v_step > 3.5:
        anomaly_points += 30
        reasons.append(f"Sharp rectangular boundary seam detected around {field_name}")

    # 4. 2D FFT Frequency Analysis
    try:
        f = np.fft.fft2(patch_gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1.0)
        # High frequency energy fraction (corners of spectrum)
        ph, pw = magnitude_spectrum.shape
        cy, cx = ph // 2, pw // 2
        r = min(cy, cx) // 2
        mask_low = np.zeros((ph, pw), np.uint8)
        cv2.circle(mask_low, (cx, cy), r, 1, -1)
        high_freq_energy = float(np.mean(magnitude_spectrum[mask_low == 0]))
        low_freq_energy = float(np.mean(magnitude_spectrum[mask_low == 1]))
        freq_ratio = high_freq_energy / (low_freq_energy + 1.0)

        if freq_ratio > 1.8:
            anomaly_points += 15
            reasons.append(f"Synthetic high-frequency spectral pattern in {field_name}")
    except Exception:
        pass

    clamped_anomaly = max(0, min(100, anomaly_points))

    if clamped_anomaly >= 45:
        status = "SUSPICIOUS"
    elif clamped_anomaly >= 20:
        status = "WARNING"
    else:
        status = "PASS"

    return {
        "field": field_name,
        "anomaly_score": clamped_anomaly,
        "status": status,
        "reasons": reasons,
    }


def analyze_copy_move_cloning(gray: np.ndarray) -> Dict[str, Any]:
    """Fast SIFT feature clustering to detect cloned or copy-moved regions."""
    h, w = gray.shape[:2]
    scale = 1.0
    if max(h, w) > FEATURE_ANALYSIS_DIM:
        scale = FEATURE_ANALYSIS_DIM / float(max(h, w))
        small = cv2.resize(gray, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    else:
        small = gray

    try:
        sift = cv2.SIFT_create(nfeatures=250)
        keypoints, descriptors = sift.detectAndCompute(small, None)
    except Exception:
        return {"status": "PASS", "score": 0, "metric": 0, "reason": "Copy-move analysis unavailable"}

    if descriptors is None or len(descriptors) < 20:
        return {"status": "PASS", "score": 0, "metric": 0, "reason": "Insufficient distinct texture for copy-move analysis"}

    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(descriptors, descriptors, k=2)

    pts = np.array([k.pt for k in keypoints])
    diffs = []

    for m in matches:
        if len(m) < 2:
            continue
        m2 = m[1]
        if m2.distance < 120.0:
            p1 = pts[m2.queryIdx]
            p2 = pts[m2.trainIdx]
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            dist = np.hypot(dx, dy)
            if dist > 40.0 and dx > 15.0:
                diffs.append(p2 - p1)

    max_cluster = 0
    if diffs:
        bins = np.round(np.array(diffs) / 25.0).astype(int)
        _, counts = np.unique(bins, axis=0, return_counts=True)
        max_cluster = int(np.max(counts))

    if max_cluster >= 6:
        return {
            "status": "FAIL",
            "score": 35,
            "metric": max_cluster,
            "reason": f"Potential copy-move duplicated region detected ({max_cluster} aligned feature pairs)",
        }
    elif max_cluster >= 5:
        return {
            "status": "WARNING",
            "score": 15,
            "metric": max_cluster,
            "reason": f"Minor duplicate texture pattern detected ({max_cluster} matching feature pairs)",
        }
    return {
        "status": "PASS",
        "score": 0,
        "metric": max_cluster,
        "reason": "No recurring cloned or duplicated regions identified",
    }
