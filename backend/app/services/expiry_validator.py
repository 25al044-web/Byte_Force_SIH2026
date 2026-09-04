"""Document expiration validation service.

Evaluates document expiration dates against validity thresholds:
- PASS: More than 180 days remaining
- WARNING: Within 180 days remaining
- FAIL: Already expired
- NOT_AVAILABLE: Expiry date is missing, empty, or unparseable
"""

from datetime import date, datetime
from typing import Any, Dict, Optional


def validate_expiry(
    expiry_date: Optional[str],
    reference_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Validates an identity document expiration date string.

    Args:
        expiry_date: Date string, expected in YYYY-MM-DD format.
        reference_date: Optional reference date for calculation (defaults to current date).

    Returns:
        Dict with keys:
          - status: "PASS" | "WARNING" | "FAIL" | "NOT_AVAILABLE"
          - score: int
          - reason: str
    """
    if not expiry_date or not isinstance(expiry_date, str) or not expiry_date.strip():
        return {
            "status": "NOT_AVAILABLE",
            "score": 0,
            "reason": "Document expiry date is not present or unavailable",
        }

    clean_str = expiry_date.strip()
    if clean_str.lower() in ("null", "none", "not available", "n/a"):
        return {
            "status": "NOT_AVAILABLE",
            "score": 0,
            "reason": "Document expiry date is not present or unavailable",
        }

    # Attempt parsing YYYY-MM-DD
    parsed_date = None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            parsed_date = datetime.strptime(clean_str, fmt).date()
            break
        except ValueError:
            continue

    if parsed_date is None:
        return {
            "status": "NOT_AVAILABLE",
            "score": 0,
            "reason": f"Document expiry date '{expiry_date}' format is invalid or unparseable",
        }

    today = reference_date or date.today()
    delta_days = (parsed_date - today).days

    if delta_days < 0:
        return {
            "status": "FAIL",
            "score": 25,
            "reason": f"Document expired on {parsed_date.isoformat()} ({abs(delta_days)} days ago)",
        }
    elif delta_days <= 180:
        return {
            "status": "WARNING",
            "score": 10,
            "reason": f"Document is nearing expiration on {parsed_date.isoformat()} ({delta_days} days remaining)",
        }
    else:
        return {
            "status": "PASS",
            "score": 0,
            "reason": f"Document is valid until {parsed_date.isoformat()} ({delta_days} days remaining)",
        }
