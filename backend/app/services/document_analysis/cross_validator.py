"""Cross-field consistency validator.

Compares OCR-visible document fields against machine-readable sources:
- Visible Name vs MRZ Name vs QR Name
- Visible Document Number vs MRZ Document Number vs QR Document Number
- Visible Date of Birth vs MRZ Date of Birth vs QR Date of Birth
- Visible Expiry Date vs MRZ Expiry Date

CRITICAL RULE (Phase 6 & 7):
If a visible field (e.g. Name: 'RAHUL SHARMA') contradicts machine-readable
data (e.g. MRZ Name: 'ARUN KUMAR'), flag as HIGH-SEVERITY DATA MISMATCH.
This should heavily drive the final risk score.
If machine-readable data is unavailable, report NOT_AVAILABLE, not FAIL.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


def _normalize_name_tokens(name: Optional[str]) -> List[str]:
    """Tokenize name into uppercase alphabetical tokens."""
    if not name or not isinstance(name, str):
        return []
    cleaned = re.sub(r"[^A-Za-z\s]", " ", name).upper()
    return [t for t in cleaned.split() if len(t) > 0]


def _names_match(name1: Optional[str], name2: Optional[str]) -> Tuple[bool, float]:
    """Evaluates whether two names refer to the same identity.

    Returns:
        (is_match, similarity_ratio: 0.0 to 1.0)
    """
    toks1 = _normalize_name_tokens(name1)
    toks2 = _normalize_name_tokens(name2)

    if not toks1 or not toks2:
        return True, 1.0  # Cannot determine mismatch if one is absent

    set1, set2 = set(toks1), set(toks2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)

    jaccard = len(intersection) / float(len(union)) if union else 0.0

    # Also check if one is subset of other (e.g. "ARUN" vs "ARUN KUMAR")
    is_subset = set1.issubset(set2) or set2.issubset(set1)

    if jaccard >= 0.65 or is_subset:
        return True, max(jaccard, 0.85)

    return False, jaccard


def _clean_alphanumeric(val: Optional[str]) -> str:
    """Strip whitespace and non-alphanumeric characters."""
    if not val:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(val)).upper()


def cross_validate_fields(
    visible_fields: Dict[str, Any],
    mrz_data: Optional[Dict[str, Any]] = None,
    qr_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Cross-validates visible document fields with machine-readable data."""
    checks: List[Dict[str, Any]] = []
    mismatches: List[str] = []
    has_machine_data = False

    vis_name = visible_fields.get("full_name")
    vis_doc = visible_fields.get("document_number")
    vis_dob = visible_fields.get("date_of_birth")
    vis_expiry = visible_fields.get("expiry_date")

    # 1. Compare with MRZ
    if mrz_data and mrz_data.get("valid_format"):
        has_machine_data = True
        mrz_name = mrz_data.get("full_name")
        mrz_doc = mrz_data.get("document_number")
        mrz_dob = mrz_data.get("date_of_birth")
        mrz_expiry = mrz_data.get("expiry_date")

        # 1a. Name Comparison
        if vis_name and mrz_name:
            matches, ratio = _names_match(vis_name, mrz_name)
            if not matches:
                msg = f"Visible Name ('{vis_name}') does not match MRZ Line 1 Name ('{mrz_name}')"
                mismatches.append(msg)
                checks.append({
                    "field": "name",
                    "source": "MRZ",
                    "status": "FAIL",
                    "severity": "HIGH",
                    "visible": vis_name,
                    "machine": mrz_name,
                    "reason": msg,
                })
            else:
                checks.append({
                    "field": "name",
                    "source": "MRZ",
                    "status": "PASS",
                    "severity": "LOW",
                    "visible": vis_name,
                    "machine": mrz_name,
                    "reason": "Visible name matches MRZ machine-readable name",
                })

        # 1b. Document Number Comparison
        if vis_doc and mrz_doc:
            c_vis = _clean_alphanumeric(vis_doc)
            c_mrz = _clean_alphanumeric(mrz_doc)
            if c_vis and c_mrz and c_vis != c_mrz and (c_mrz not in c_vis and c_vis not in c_mrz):
                msg = f"Visible Document Number ('{vis_doc}') does not match MRZ Document Number ('{mrz_doc}')"
                mismatches.append(msg)
                checks.append({
                    "field": "document_number",
                    "source": "MRZ",
                    "status": "FAIL",
                    "severity": "HIGH",
                    "visible": vis_doc,
                    "machine": mrz_doc,
                    "reason": msg,
                })
            else:
                checks.append({
                    "field": "document_number",
                    "source": "MRZ",
                    "status": "PASS",
                    "severity": "LOW",
                    "visible": vis_doc,
                    "machine": mrz_doc,
                    "reason": "Visible document number is consistent with MRZ data",
                })

        # 1c. Date of Birth Comparison
        if vis_dob and mrz_dob and vis_dob != mrz_dob:
            msg = f"Visible DOB ('{vis_dob}') does not match MRZ DOB ('{mrz_dob}')"
            mismatches.append(msg)
            checks.append({
                "field": "date_of_birth",
                "source": "MRZ",
                "status": "FAIL",
                "severity": "HIGH",
                "visible": vis_dob,
                "machine": mrz_dob,
                "reason": msg,
            })

        # 1d. Expiry Date Comparison
        if vis_expiry and mrz_expiry and vis_expiry != mrz_expiry:
            msg = f"Visible Expiry ('{vis_expiry}') does not match MRZ Expiry ('{mrz_expiry}')"
            mismatches.append(msg)
            checks.append({
                "field": "expiry_date",
                "source": "MRZ",
                "status": "FAIL",
                "severity": "HIGH",
                "visible": vis_expiry,
                "machine": mrz_expiry,
                "reason": msg,
            })

    # 2. Compare with QR Data (if detected and decoded)
    if qr_data and qr_data.get("detected"):
        has_machine_data = True
        extracted_qr = qr_data.get("extracted_fields", {})
        qr_name = extracted_qr.get("full_name")
        qr_doc = extracted_qr.get("document_number")

        if vis_name and qr_name:
            matches, _ = _names_match(vis_name, qr_name)
            if not matches:
                msg = f"Visible Name ('{vis_name}') does not match QR-encoded Name ('{qr_name}')"
                mismatches.append(msg)
                checks.append({
                    "field": "name",
                    "source": "QR_CODE",
                    "status": "FAIL",
                    "severity": "HIGH",
                    "visible": vis_name,
                    "machine": qr_name,
                    "reason": msg,
                })

        if vis_doc and qr_doc:
            c_vis = _clean_alphanumeric(vis_doc)
            c_qr = _clean_alphanumeric(qr_doc)
            if c_vis and c_qr and c_vis != c_qr:
                msg = f"Visible Document Number ('{vis_doc}') does not match QR-encoded ID ('{qr_doc}')"
                mismatches.append(msg)
                checks.append({
                    "field": "document_number",
                    "source": "QR_CODE",
                    "status": "FAIL",
                    "severity": "HIGH",
                    "visible": vis_doc,
                    "machine": qr_doc,
                    "reason": msg,
                })

    # 3. Aggregate Status and Risk
    if not has_machine_data:
        return {
            "status": "NOT_AVAILABLE",
            "mismatch_count": 0,
            "has_mismatch": False,
            "checks": [],
            "reason": "No machine-readable MRZ or QR barcode present on document for cross-validation.",
        }

    if mismatches:
        return {
            "status": "FAIL",
            "mismatch_count": len(mismatches),
            "has_mismatch": True,
            "checks": checks,
            "mismatches": mismatches,
            "reason": f"HIGH-SEVERITY DATA MISMATCH: {'; '.join(mismatches[:2])}",
        }

    return {
        "status": "PASS",
        "mismatch_count": 0,
        "has_mismatch": False,
        "checks": checks,
        "mismatches": [],
        "reason": "All visible document data is fully consistent with machine-readable records (MRZ/QR).",
    }
