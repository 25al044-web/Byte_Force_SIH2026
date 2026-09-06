"""Pipeline profiler and benchmark comparison tool for SIH26188.

Measures and compares execution time:
BASELINE (unoptimized) vs OPTIMIZED (decode-once, embedding reuse, shared feature maps).
"""

import io
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.blacklist_checker import check_blacklist
from app.services.duplicate_identity_checker import check_duplicate_identity
from app.services.expiry_validator import validate_expiry
from app.services.face_matcher import compare_faces, extract_selfie_embedding
from app.services.mrz_validator import validate_td3_mrz
from app.services.risk_engine import calculate_risk
from app.services.tamper_detector import (
    detect_tampering,
    _decode_and_sanitize_image,
)
from app.models.screening import (
    BlacklistCheckResult,
    ChecksContainer,
    CheckStatus,
    ExpiryCheckResult,
    FaceMatchCheckResult,
    MRZCheckResult,
    TamperCheckResult,
    DuplicateIdentityCheckResult,
)


def build_test_passport(ai_overlay: bool = False, quality: int = 95, blur: float = 0.0) -> Tuple[bytes, Dict[str, Any], Tuple[str, str]]:
    w, h = 800, 600
    img = Image.new("RGB", (w, h), (246, 243, 238))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, w - 20, h - 20], outline=(120, 120, 120), width=2)
    draw.text((320, 40), "REPUBLIC OF DEMO - PASSPORT", fill=(45, 45, 50))
    draw.rectangle([50, 80, 230, 310], fill=(180, 190, 210), outline=(80, 80, 90), width=2)
    draw.ellipse([110, 130, 170, 200], fill=(140, 150, 170))
    draw.ellipse([85, 210, 195, 300], fill=(130, 140, 160))

    name = "RAHUL SHARMA" if ai_overlay else "ARUN KUMAR"
    draw.text((320, 85), "Document No.", fill=(110, 110, 115))
    draw.text((320, 105), "P1234567", fill=(35, 35, 40))
    draw.text((320, 145), "Surname & Given Names", fill=(110, 110, 115))
    if ai_overlay:
        draw.rectangle([315, 160, 580, 195], fill=(246, 243, 238))
        draw.text((320, 165), name, fill=(5, 5, 5))
    else:
        draw.text((320, 165), name, fill=(35, 35, 40))

    draw.text((320, 205), "Date of Birth", fill=(110, 110, 115))
    draw.text((320, 225), "1995-05-15", fill=(35, 35, 40))
    draw.text((320, 265), "Date of Expiry", fill=(110, 110, 115))
    draw.text((320, 285), "2030-05-15", fill=(35, 35, 40))

    draw.rectangle([35, 490, w - 35, 580], fill=(252, 252, 250), outline=(200, 200, 200))
    mrz_1 = "P<INDARUN<<KUMAR<<<<<<<<<<<<<<<<<<<<<<<<<<<<".ljust(44, '<')
    mrz_2 = "P1234567<1IND9505151M3005156<<<<<<<<<<<<<<<4".ljust(44, '<')
    draw.text((45, 505), mrz_1, fill=(20, 20, 20))
    draw.text((45, 540), mrz_2, fill=(20, 20, 20))

    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    doc_bytes = buf.getvalue()

    doc_data = {
        "full_name": name,
        "document_number": "P1234567",
        "date_of_birth": "1995-05-15",
        "expiry_date": "2030-05-15",
    }
    return doc_bytes, doc_data, (mrz_1, mrz_2)


def build_test_selfie() -> bytes:
    img = Image.new("RGB", (400, 400), (220, 220, 220))
    draw = ImageDraw.Draw(img)
    draw.ellipse([150, 100, 250, 220], fill=(180, 150, 130))
    draw.ellipse([100, 220, 300, 380], fill=(60, 80, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def measure_unoptimized(doc_bytes, doc_data, mrz_lines, selfie_bytes, mime_type="image/jpeg"):
    """Simulates the unoptimized pipeline (duplicate decodes, duplicate selfie inference)."""
    t_start = time.perf_counter()

    # 1. MRZ
    t0 = time.perf_counter()
    _ = validate_td3_mrz(mrz_lines[0], mrz_lines[1])
    t_mrz = (time.perf_counter() - t0) * 1000

    # 2. Expiry
    t0 = time.perf_counter()
    _ = validate_expiry(doc_data.get("expiry_date"))
    t_expiry = (time.perf_counter() - t0) * 1000

    # 3. Blacklist
    t0 = time.perf_counter()
    _ = check_blacklist(doc_data.get("document_number"))
    t_blacklist = (time.perf_counter() - t0) * 1000

    # 4. Face comparison (decodes doc and selfie from raw bytes)
    t0 = time.perf_counter()
    face_res = compare_faces(doc_bytes, mime_type, selfie_bytes, mime_type)
    t_face = (time.perf_counter() - t0) * 1000

    # 5. Selfie embedding (re-decodes selfie and re-runs insightface)
    t0 = time.perf_counter()
    selfie_emb = extract_selfie_embedding(selfie_bytes, mime_type)
    t_emb = (time.perf_counter() - t0) * 1000

    # 6. Duplicate lookup
    t0 = time.perf_counter()
    _ = check_duplicate_identity(doc_data.get("document_number"), doc_data.get("full_name"), selfie_emb)
    t_dup = (time.perf_counter() - t0) * 1000

    # 7. Tamper screening (unoptimized call: re-decodes document bytes from scratch)
    t0 = time.perf_counter()
    tamper_res = detect_tampering(doc_bytes, mime_type, extracted_data=doc_data, mrz_lines=mrz_lines)
    t_tamper = (time.perf_counter() - t0) * 1000

    # 8. Risk engine
    t0 = time.perf_counter()
    checks = ChecksContainer(
        mrz=MRZCheckResult(status=CheckStatus.PASS, score=100, reason="ok"),
        expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=100, reason="ok"),
        tamper=TamperCheckResult(status=CheckStatus.PASS, risk=tamper_res["risk"], reason="ok"),
        face_match=FaceMatchCheckResult(status=CheckStatus.NOT_AVAILABLE, reason="ok"),
        duplicate_identity=DuplicateIdentityCheckResult(status=CheckStatus.PASS, reason="ok"),
        blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
    )
    _ = calculate_risk(checks)
    t_risk = (time.perf_counter() - t0) * 1000

    t_total = (time.perf_counter() - t_start) * 1000
    return {
        "mrz": t_mrz,
        "expiry": t_expiry,
        "blacklist": t_blacklist,
        "face_match": t_face,
        "selfie_embedding": t_emb,
        "duplicate_check": t_dup,
        "tamper_detection": t_tamper,
        "risk_engine": t_risk,
        "total": t_total,
    }


def measure_optimized(doc_bytes, doc_data, mrz_lines, selfie_bytes, mime_type="image/jpeg"):
    """Simulates the optimized pipeline (single decode, embedding reuse, shared feature maps)."""
    t_start = time.perf_counter()

    # 1. Decode once at ingestion
    t0_dec = time.perf_counter()
    doc_bgr, doc_metadata, _ = _decode_and_sanitize_image(doc_bytes, mime_type)
    doc_gray = cv2.cvtColor(doc_bgr, cv2.COLOR_BGR2GRAY) if doc_bgr is not None else None
    t_dec = (time.perf_counter() - t0_dec) * 1000

    # 1. MRZ
    t0 = time.perf_counter()
    _ = validate_td3_mrz(mrz_lines[0], mrz_lines[1])
    t_mrz = (time.perf_counter() - t0) * 1000

    # 2. Expiry
    t0 = time.perf_counter()
    _ = validate_expiry(doc_data.get("expiry_date"))
    t_expiry = (time.perf_counter() - t0) * 1000

    # 3. Blacklist
    t0 = time.perf_counter()
    _ = check_blacklist(doc_data.get("document_number"))
    t_blacklist = (time.perf_counter() - t0) * 1000

    # 4. Face comparison (reuses pre-decoded document BGR)
    t0 = time.perf_counter()
    face_res = compare_faces(
        doc_bytes,
        mime_type,
        selfie_bytes,
        mime_type,
        precomputed_doc_bgr=doc_bgr,
    )
    t_face = (time.perf_counter() - t0) * 1000

    # 5. Selfie embedding (reuses already extracted embedding from face_res)
    t0 = time.perf_counter()
    if face_res.get("_selfie_checked"):
        selfie_emb = face_res.get("_selfie_embedding")
    else:
        selfie_emb = extract_selfie_embedding(selfie_bytes, mime_type)
    t_emb = (time.perf_counter() - t0) * 1000

    # 6. Duplicate lookup
    t0 = time.perf_counter()
    _ = check_duplicate_identity(doc_data.get("document_number"), doc_data.get("full_name"), selfie_emb)
    t_dup = (time.perf_counter() - t0) * 1000

    # 7. Tamper screening (reuses pre-decoded BGR, grayscale, and metadata)
    t0 = time.perf_counter()
    tamper_res = detect_tampering(
        doc_bytes,
        mime_type,
        extracted_data=doc_data,
        mrz_lines=mrz_lines,
        precomputed_bgr=doc_bgr,
        precomputed_metadata=doc_metadata,
        precomputed_gray=doc_gray,
    )
    t_tamper = (time.perf_counter() - t0) * 1000

    # 8. Risk engine
    t0 = time.perf_counter()
    checks = ChecksContainer(
        mrz=MRZCheckResult(status=CheckStatus.PASS, score=100, reason="ok"),
        expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=100, reason="ok"),
        tamper=TamperCheckResult(status=CheckStatus.PASS, risk=tamper_res["risk"], reason="ok"),
        face_match=FaceMatchCheckResult(status=CheckStatus.NOT_AVAILABLE, reason="ok"),
        duplicate_identity=DuplicateIdentityCheckResult(status=CheckStatus.PASS, reason="ok"),
        blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
    )
    _ = calculate_risk(checks)
    t_risk = (time.perf_counter() - t0) * 1000

    t_total = (time.perf_counter() - t_start) * 1000
    return {
        "decode_once": t_dec,
        "mrz": t_mrz,
        "expiry": t_expiry,
        "blacklist": t_blacklist,
        "face_match": t_face,
        "selfie_embedding": t_emb,
        "duplicate_check": t_dup,
        "tamper_detection": t_tamper,
        "risk_engine": t_risk,
        "total": t_total,
    }


def run_comparison(iterations: int = 5):
    doc_bytes, doc_data, mrz_lines = build_test_passport(ai_overlay=False)
    selfie_bytes = build_test_selfie()

    print(f"Running BEFORE vs AFTER benchmark over {iterations} iterations...\n")

    # Warmup
    _ = measure_unoptimized(doc_bytes, doc_data, mrz_lines, selfie_bytes)
    _ = measure_optimized(doc_bytes, doc_data, mrz_lines, selfie_bytes)

    unopt_runs = []
    opt_runs = []

    for i in range(iterations):
        unopt_runs.append(measure_unoptimized(doc_bytes, doc_data, mrz_lines, selfie_bytes))
        opt_runs.append(measure_optimized(doc_bytes, doc_data, mrz_lines, selfie_bytes))

    # Compute averages
    keys = ["mrz", "expiry", "blacklist", "face_match", "selfie_embedding", "duplicate_check", "tamper_detection", "risk_engine", "total"]

    print("=" * 85)
    print(f"{'PIPELINE STAGE':<25} | {'BEFORE (ms)':<14} | {'AFTER (ms)':<14} | {'SAVED (ms)':<12} | {'IMPROVEMENT'}")
    print("=" * 85)

    for k in keys:
        b_val = float(np.mean([r[k] for r in unopt_runs]))
        a_val = float(np.mean([r[k] for r in opt_runs]))
        diff = b_val - a_val
        pct = (diff / b_val * 100.0) if b_val > 0 else 0.0

        label = k.replace("_", " ").title()
        print(f"{label:<25} | {b_val:>10.2f} ms | {a_val:>10.2f} ms | {diff:>8.2f} ms | {pct:>9.1f}%")

    print("=" * 85)
    total_before = float(np.mean([r["total"] for r in unopt_runs]))
    total_after = float(np.mean([r["total"] for r in opt_runs]))
    total_saved = total_before - total_after
    total_pct = (total_saved / total_before * 100.0)
    print(f"\nTOTAL PIPELINE LATENCY: {total_before:.1f} ms -> {total_after:.1f} ms ({total_saved:.1f} ms saved, {total_pct:.1f}% FASTER)\n")


if __name__ == "__main__":
    run_comparison(iterations=5)
