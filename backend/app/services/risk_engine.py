"""Explainable rule-based risk-scoring engine for SIH26188.

This service evaluates screening check results (MRZ, expiry, tamper, face match,
duplicate identity, blacklist) and computes a deterministic, explainable risk score
(0-100), triaging risk level (LOW, REVIEW, HIGH), granular contributions,
and auditable human-readable explanations.
"""

from typing import Any, Dict, List, Optional, Union

# Base status risk contribution mappings
STATUS_RISK_MAP = {
    "mrz": {
        "PASS": 0,
        "WARNING": 10,
        "FAIL": 25,
        "NOT_AVAILABLE": 5,
    },
    "expiry": {
        "PASS": 0,
        "WARNING": 10,
        "FAIL": 25,
        "NOT_AVAILABLE": 5,
    },
    "face_match": {
        "PASS": 0,
        "WARNING": 20,
        "FAIL": 40,
        "NOT_AVAILABLE": 10,
    },
    "duplicate_identity": {
        "PASS": 0,
        "WARNING": 25,
        "FAIL": 45,
        "NOT_AVAILABLE": 5,
    },
    "blacklist": {
        "PASS": 0,
        "WARNING": 40,
        "FAIL": 70,
        "NOT_AVAILABLE": 10,
    },
}


def _extract_check(checks: Any, key: str) -> Dict[str, Any]:
    """Safely extracts a check result dictionary from ChecksContainer or dict."""
    if checks is None:
        return {}

    val = None
    if isinstance(checks, dict):
        val = checks.get(key)
    else:
        val = getattr(checks, key, None)

    if val is None:
        return {}

    if hasattr(val, "model_dump"):
        return val.model_dump()
    if isinstance(val, dict):
        return val

    return {
        "status": getattr(val, "status", None),
        "score": getattr(val, "score", None),
        "reason": getattr(val, "reason", None),
        "risk": getattr(val, "risk", None),
        "similarity": getattr(val, "similarity", None),
        "similar_identity": getattr(val, "similar_identity", None),
    }


def _normalize_status(check_dict: Dict[str, Any]) -> str:
    """Normalizes check status to uppercase string."""
    st = check_dict.get("status")
    if hasattr(st, "value"):
        st = st.value
    if isinstance(st, str):
        norm = st.strip().upper()
        if norm in ("PASS", "WARNING", "FAIL", "NOT_AVAILABLE"):
            return norm
    return "NOT_AVAILABLE"


def calculate_risk(checks: Any) -> Dict[str, Any]:
    """Calculates overall fraud risk score, level, contributions, and explanations.

    Args:
        checks: ChecksContainer instance or dictionary containing individual checks.

    Returns:
        Dict with keys:
          - score: int (clamped 0..100)
          - level: "LOW" | "REVIEW" | "HIGH"
          - explanations: List[str]
          - contributions: Dict[str, int]
    """
    contributions: Dict[str, int] = {
        "mrz": 0,
        "expiry": 0,
        "tamper": 0,
        "face_match": 0,
        "duplicate_identity": 0,
        "blacklist": 0,
    }
    explanations: List[str] = []
    override_notes: List[str] = []

    # 1. MRZ Check
    mrz_data = _extract_check(checks, "mrz")
    mrz_status = _normalize_status(mrz_data)
    mrz_contrib = STATUS_RISK_MAP["mrz"].get(mrz_status, 5)
    contributions["mrz"] = mrz_contrib

    if mrz_status == "PASS":
        explanations.append("MRZ validation passed: no additional risk.")
    elif mrz_status == "WARNING":
        explanations.append("MRZ validation warning: +10 risk.")
    elif mrz_status == "FAIL":
        explanations.append("MRZ validation failed: +25 risk.")
    else:
        explanations.append("MRZ validation not available: +5 default risk.")

    # 2. Expiry Check
    expiry_data = _extract_check(checks, "expiry")
    expiry_status = _normalize_status(expiry_data)
    expiry_contrib = STATUS_RISK_MAP["expiry"].get(expiry_status, 5)
    contributions["expiry"] = expiry_contrib

    if expiry_status == "PASS":
        explanations.append("Document has not expired: no additional risk.")
    elif expiry_status == "WARNING":
        explanations.append("Document is nearing expiration: +10 risk.")
    elif expiry_status == "FAIL":
        explanations.append("Document is expired: +25 risk.")
    else:
        explanations.append("Document expiry check not available: +5 default risk.")

    # 3. Tamper Screening
    tamper_data = _extract_check(checks, "tamper")
    tamper_status = _normalize_status(tamper_data)
    raw_tamper_risk = tamper_data.get("risk")

    if raw_tamper_risk is not None and isinstance(raw_tamper_risk, (int, float)):
        t_val = int(raw_tamper_risk)
        if t_val < 20:
            tamper_contrib = 0
            tamper_msg = f"Tamper screening detected low risk ({t_val}/100): no additional risk."
        elif t_val < 40:
            tamper_contrib = 10
            tamper_msg = f"Tamper screening detected minor anomaly ({t_val}/100): +10 risk."
        elif t_val < 60:
            tamper_contrib = 20
            tamper_msg = f"Tamper screening detected moderate risk ({t_val}/100): +20 risk."
        elif t_val < 80:
            tamper_contrib = 30
            tamper_msg = f"Tamper screening detected elevated risk ({t_val}/100): +30 risk."
        else:
            tamper_contrib = 40
            tamper_msg = f"Tamper screening detected critical risk ({t_val}/100): +40 risk."
    else:
        # Fallback when tamper risk score is missing
        if tamper_status == "FAIL":
            tamper_contrib = 30
            tamper_msg = "Tamper check failed: +30 risk."
        elif tamper_status == "WARNING":
            tamper_contrib = 15
            tamper_msg = "Tamper check warning: +15 risk."
        elif tamper_status == "PASS":
            tamper_contrib = 0
            tamper_msg = "No tampering detected: no additional risk."
        else:
            tamper_contrib = 5
            tamper_msg = "Tamper check not available: +5 default risk."

    contributions["tamper"] = tamper_contrib
    explanations.append(tamper_msg)

    # 4. Face Match & Biometric Similarity Adjustment
    face_data = _extract_check(checks, "face_match")
    face_status = _normalize_status(face_data)
    base_face_risk = STATUS_RISK_MAP["face_match"].get(face_status, 10)

    raw_similarity = face_data.get("similarity")
    sim_risk: Optional[int] = None
    if raw_similarity is not None and isinstance(raw_similarity, (int, float)):
        s_val = float(raw_similarity)
        if s_val >= 85.0:
            sim_risk = 0
        elif s_val >= 70.0:
            sim_risk = 10
        elif s_val >= 50.0:
            sim_risk = 25
        else:
            sim_risk = 40

    if face_status == "FAIL":
        if sim_risk is not None:
            # Do not excessively double count if status is already FAIL
            face_contrib = max(base_face_risk, sim_risk)
            face_msg = f"Face match failed with similarity {raw_similarity:.1f}%: +{face_contrib} risk."
        else:
            face_contrib = base_face_risk
            face_msg = f"Face match failed: +{face_contrib} risk."
    elif face_status == "WARNING":
        if sim_risk is not None and sim_risk > 0:
            face_contrib = base_face_risk + sim_risk
            face_msg = f"Face match warning (+{base_face_risk}) and similarity {raw_similarity:.1f}% (+{sim_risk}): +{face_contrib} risk."
        else:
            face_contrib = base_face_risk
            face_msg = f"Face match warning: +{face_contrib} risk."
    elif face_status == "PASS":
        if sim_risk is not None:
            face_contrib = sim_risk
            if sim_risk > 0:
                face_msg = f"Face similarity of {raw_similarity:.1f}% increased risk by {sim_risk}."
            else:
                face_msg = f"Face comparison passed with high similarity ({raw_similarity:.1f}%): no additional risk."
        else:
            face_contrib = 0
            face_msg = "Face comparison passed: no additional risk."
    else:  # NOT_AVAILABLE
        face_contrib = base_face_risk
        face_msg = "Face comparison not available: +10 default risk."

    contributions["face_match"] = face_contrib
    explanations.append(face_msg)

    # 5. Duplicate Identity Check
    dup_data = _extract_check(checks, "duplicate_identity")
    dup_status = _normalize_status(dup_data)
    dup_contrib = STATUS_RISK_MAP["duplicate_identity"].get(dup_status, 5)
    contributions["duplicate_identity"] = dup_contrib

    if dup_status == "PASS":
        explanations.append("No duplicate identity detected: no additional risk.")
    elif dup_status == "WARNING":
        explanations.append("Possible duplicate identity detected: +25 risk.")
    elif dup_status == "FAIL":
        explanations.append("Duplicate identity confirmed: +45 risk.")
    else:
        explanations.append("Duplicate identity check not available: +5 default risk.")

    # 6. Blacklist Check
    bl_data = _extract_check(checks, "blacklist")
    bl_status = _normalize_status(bl_data)
    bl_contrib = STATUS_RISK_MAP["blacklist"].get(bl_status, 10)
    contributions["blacklist"] = bl_contrib

    if bl_status == "PASS":
        explanations.append("Document not found on watchlist/blacklist: no additional risk.")
    elif bl_status == "WARNING":
        explanations.append("Partial watchlist match detected: +40 risk.")
    elif bl_status == "FAIL":
        explanations.append("Document/identity found on blacklist: +70 risk.")
    else:
        explanations.append("Blacklist screening not available: +10 default risk.")

    # 7. Trusted Identity Registry Cross-Verification (additive check)
    tr_data = _extract_check(checks, "trusted_registry")
    tr_status = None
    if tr_data:
        raw_tr_st = tr_data.get("status")
        if hasattr(raw_tr_st, "value"):
            raw_tr_st = raw_tr_st.value
        tr_status = str(raw_tr_st).strip().upper() if raw_tr_st else "NOT_FOUND"

        tr_mismatches = tr_data.get("mismatches") or []
        tr_reason = tr_data.get("reason") or "conflict detected"

        if tr_status == "MISMATCH":
            has_high_sev = any(m.get("severity") == "HIGH" for m in tr_mismatches)
            tr_contrib = 60 if has_high_sev else 40
            contributions["trusted_registry"] = tr_contrib
            explanations.append(f"Trusted identity registry conflict: {tr_reason} (+{tr_contrib} risk).")
        elif tr_status == "MATCH":
            contributions["trusted_registry"] = 0
            explanations.append("Presented document matches trusted identity registry: no additional risk.")
        else:
            contributions["trusted_registry"] = 0

    # Compute base cumulative score
    raw_score = sum(contributions.values())
    final_score = raw_score

    # 8. Critical Overrides
    # Override A: Blacklist FAIL -> minimum risk 85
    if bl_status == "FAIL":
        if final_score < 85:
            final_score = 85
            override_notes.append("Blacklist match triggered minimum high-risk threshold (85).")

    # Override B: Duplicate Identity FAIL -> minimum risk 75
    if dup_status == "FAIL":
        if final_score < 75:
            final_score = 75
            override_notes.append("Duplicate identity match triggered minimum risk threshold (75).")

    # Override C: Face Match FAIL AND MRZ FAIL -> minimum risk 80
    if face_status == "FAIL" and mrz_status == "FAIL":
        if final_score < 80:
            final_score = 80
            override_notes.append("Concurrent face match failure and MRZ invalidity triggered critical risk threshold (80).")

    # Override D: Machine-Readable Data Mismatch (MRZ/QR vs Visible) -> minimum risk 75
    cross_field = tamper_data.get("cross_field_consistency") or {}
    if cross_field.get("has_mismatch"):
        if final_score < 75:
            final_score = 75
            override_notes.append("Machine-readable data mismatch (MRZ/QR vs visible document fields) triggered high-risk threshold (75).")

    # Override E: Trusted Registry Mismatch -> minimum risk 75
    if tr_data and tr_status == "MISMATCH":
        if final_score < 75:
            final_score = 75
            override_notes.append("Trusted identity registry mismatch triggered high-risk threshold (75).")

    # Clamp score to 0..100
    final_score = max(0, min(100, final_score))

    # Append any override explanation notes
    explanations.extend(override_notes)

    # 8. Map Risk Level
    # 0-29: LOW, 30-59: REVIEW, 60-100: HIGH
    if final_score <= 29:
        level = "LOW"
    elif final_score <= 59:
        level = "REVIEW"
    else:
        level = "HIGH"

    return {
        "score": final_score,
        "level": level,
        "explanations": explanations,
        "contributions": contributions,
    }
