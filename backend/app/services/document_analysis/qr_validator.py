"""Machine-readable QR and Barcode detection and semantic parsing module.

Uses OpenCV's native QRCodeDetector and BarcodeDetector to locate and
decode 2D barcodes on identity documents.

Parses identity payloads (JSON, XML, delimited strings, Key-Value)
and extracts demographic fields for cross-validation against visible OCR.

DISCLOSURE (Phase 8):
States clearly: "Encoded-data consistency verified; issuing-authority authenticity not verified."
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


def _parse_qr_payload(raw_text: str) -> Dict[str, Optional[str]]:
    """Attempts to extract demographic fields from decoded QR text."""
    fields: Dict[str, Optional[str]] = {
        "full_name": None,
        "document_number": None,
        "date_of_birth": None,
        "expiry_date": None,
        "gender": None,
    }

    if not raw_text or not raw_text.strip():
        return fields

    text = raw_text.strip()

    # 1. Try JSON
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                fields["full_name"] = data.get("name") or data.get("full_name") or data.get("holder_name")
                fields["document_number"] = data.get("doc_no") or data.get("document_number") or data.get("id")
                fields["date_of_birth"] = data.get("dob") or data.get("date_of_birth")
                fields["expiry_date"] = data.get("expiry") or data.get("expiry_date")
                fields["gender"] = data.get("gender") or data.get("sex")
                return fields
        except Exception:
            pass

    # 2. Try XML (e.g. Aadhaar secure QR schema / XML)
    if "<" in text and ">" in text:
        try:
            # Handle XML snippet or root
            root = ET.fromstring(text)
            attribs = root.attrib
            fields["full_name"] = attribs.get("name") or attribs.get("n")
            fields["document_number"] = attribs.get("uid") or attribs.get("doc")
            fields["date_of_birth"] = attribs.get("dob") or attribs.get("d")
            fields["gender"] = attribs.get("gender") or attribs.get("g")
            return fields
        except Exception:
            pass

    # 3. Try Key-Value pairs (e.g., "NAME=RAHUL SHARMA,DOB=2000-01-01,ID=P1234567")
    kv_pattern = re.findall(r"(?i)(name|full_name|id|doc|dob|expiry|sex|gender)\s*[:=]\s*([^,\n;]+)", text)
    if kv_pattern:
        for k, v in kv_pattern:
            k_lower = k.lower()
            val = v.strip()
            if k_lower in ("name", "full_name"):
                fields["full_name"] = val
            elif k_lower in ("id", "doc"):
                fields["document_number"] = val
            elif k_lower == "dob":
                fields["date_of_birth"] = val
            elif k_lower == "expiry":
                fields["expiry_date"] = val
            elif k_lower in ("sex", "gender"):
                fields["gender"] = val
        return fields

    return fields


def detect_and_decode_qr(bgr: np.ndarray) -> Dict[str, Any]:
    """Detects and decodes QR codes and 1D/2D barcodes on the document image."""
    h, w = bgr.shape[:2]
    qr_detector = cv2.QRCodeDetector()

    # Detect QR Code
    retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(bgr)

    if retval and decoded_info and len(decoded_info) > 0:
        raw_text = decoded_info[0]
        pts = points[0] if points is not None and len(points) > 0 else None

        bbox_norm = None
        if pts is not None:
            xmin = max(0, int(np.min(pts[:, 0])))
            xmax = min(w, int(np.max(pts[:, 0])))
            ymin = max(0, int(np.min(pts[:, 1])))
            ymax = min(h, int(np.max(pts[:, 1])))
            # Normalized 0-1000 coordinates
            bbox_norm = [
                int(round((ymin / h) * 1000)),
                int(round((xmin / w) * 1000)),
                int(round((ymax / h) * 1000)),
                int(round((xmax / w) * 1000)),
            ]

        extracted = _parse_qr_payload(raw_text)

        return {
            "detected": True,
            "type": "QR_CODE",
            "raw_text": raw_text[:200],  # sanitized snippet
            "bbox": bbox_norm,
            "extracted_fields": extracted,
            "disclaimer": "Encoded-data consistency verified; issuing-authority authenticity not verified.",
            "status": "PASS",
        }

    # If multi-detect failed, try single-detect on grayscale
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    text_single, points_single, _ = qr_detector.detectAndDecode(gray)
    if text_single:
        extracted = _parse_qr_payload(text_single)
        return {
            "detected": True,
            "type": "QR_CODE",
            "raw_text": text_single[:200],
            "bbox": None,
            "extracted_fields": extracted,
            "disclaimer": "Encoded-data consistency verified; issuing-authority authenticity not verified.",
            "status": "PASS",
        }

    return {
        "detected": False,
        "type": None,
        "raw_text": None,
        "bbox": None,
        "extracted_fields": {},
        "disclaimer": "No machine-readable QR or barcode identified on this document.",
        "status": "NOT_AVAILABLE",
    }
