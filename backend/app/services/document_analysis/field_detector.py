"""Field-level document layout and region detection module.

Locates semantic document zones:
- Photograph region
- Machine Readable Zone (MRZ)
- Primary Identity Fields: Name, Document Number, Date of Birth, Expiry
- QR / Barcode zones

All bounding boxes are represented as normalized [ymin, xmin, ymax, xmax]
tuples in the 0..1000 coordinate space for resolution-independent rendering.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class DocumentFieldRegion:
    field_name: str
    label: str
    bbox: Tuple[int, int, int, int]  # [ymin, xmin, ymax, xmax] in 0..1000
    pixel_bbox: Tuple[int, int, int, int]  # [y1, x1, y2, x2] in image pixels
    confidence: float
    value: Optional[str] = None


def _to_norm_bbox(y1: int, x1: int, y2: int, x2: int, h: int, w: int) -> Tuple[int, int, int, int]:
    """Converts pixel coordinates to normalized 0-1000 range."""
    ymin = max(0, min(1000, int(round((y1 / max(1, h)) * 1000))))
    xmin = max(0, min(1000, int(round((x1 / max(1, w)) * 1000))))
    ymax = max(0, min(1000, int(round((y2 / max(1, h)) * 1000))))
    xmax = max(0, min(1000, int(round((x2 / max(1, w)) * 1000))))
    return (ymin, xmin, ymax, xmax)


def detect_document_regions(
    gray: np.ndarray,
    extracted_data: Optional[Dict[str, Any]] = None,
    has_mrz: bool = False,
    qr_bbox: Optional[List[int]] = None,
) -> List[DocumentFieldRegion]:
    """Segments document into semantic field regions."""
    h, w = gray.shape[:2]
    regions: List[DocumentFieldRegion] = []
    doc = extracted_data or {}

    # 1. Photograph Detection
    # Attempt Haar cascade face detection if available, else standard passport portrait layout
    photo_found = False
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
        if len(faces) > 0:
            fx, fy, fw, fh = faces[0]
            # Expand slightly around face to capture portrait card box
            py1 = max(0, fy - int(fh * 0.3))
            px1 = max(0, fx - int(fw * 0.25))
            py2 = min(h, fy + int(fh * 1.35))
            px2 = min(w, fx + int(fw * 1.25))
            regions.append(DocumentFieldRegion(
                field_name="photograph",
                label="Applicant Photograph",
                bbox=_to_norm_bbox(py1, px1, py2, px2, h, w),
                pixel_bbox=(py1, px1, py2, px2),
                confidence=0.92,
            ))
            photo_found = True
    except Exception:
        pass

    if not photo_found:
        # Standard ID/Passport layout: left 30%, 15% to 65% vertical
        py1, px1, py2, px2 = int(h * 0.15), int(w * 0.05), int(h * 0.65), int(w * 0.35)
        regions.append(DocumentFieldRegion(
            field_name="photograph",
            label="Applicant Photograph",
            bbox=_to_norm_bbox(py1, px1, py2, px2, h, w),
            pixel_bbox=(py1, px1, py2, px2),
            confidence=0.70,
        ))

    # 2. MRZ Detection
    if has_mrz:
        # Standard TD3 MRZ is bottom 18% of document across full width
        my1 = int(h * 0.80)
        my2 = int(h * 0.98)
        mx1 = int(w * 0.03)
        mx2 = int(w * 0.97)
        regions.append(DocumentFieldRegion(
            field_name="mrz",
            label="Machine Readable Zone",
            bbox=_to_norm_bbox(my1, mx1, my2, mx2, h, w),
            pixel_bbox=(my1, mx1, my2, mx2),
            confidence=0.95,
        ))

    # 3. QR Code Region (if detected by qr_validator)
    if qr_bbox and len(qr_bbox) == 4:
        # qr_bbox is normalized [ymin, xmin, ymax, xmax]
        qy1 = int((qr_bbox[0] / 1000.0) * h)
        qx1 = int((qr_bbox[1] / 1000.0) * w)
        qy2 = int((qr_bbox[2] / 1000.0) * h)
        qx2 = int((qr_bbox[3] / 1000.0) * w)
        regions.append(DocumentFieldRegion(
            field_name="qr_code",
            label="Machine-Readable QR Code",
            bbox=tuple(qr_bbox),
            pixel_bbox=(qy1, qx1, qy2, qx2),
            confidence=0.98,
        ))

    # 4. Text Field Regions
    # Estimate layout based on standard identity document typography zones:
    # Most documents have text in the right 60% of the document between y=15% and y=75%
    text_left = int(w * 0.38)
    text_right = int(w * 0.95)

    # Name Field (Typically upper text quadrant)
    name_val = doc.get("full_name")
    ny1, ny2 = int(h * 0.18), int(h * 0.34)
    regions.append(DocumentFieldRegion(
        field_name="name",
        label="Full Name",
        bbox=_to_norm_bbox(ny1, text_left, ny2, text_right, h, w),
        pixel_bbox=(ny1, text_left, ny2, text_right),
        confidence=0.90 if name_val else 0.75,
        value=name_val,
    ))

    # Document / ID Number (Header or top-right)
    doc_val = doc.get("document_number")
    dy1, dy2 = int(h * 0.06), int(h * 0.17)
    regions.append(DocumentFieldRegion(
        field_name="document_number",
        label="Document Number",
        bbox=_to_norm_bbox(dy1, int(w * 0.55), dy2, text_right, h, w),
        pixel_bbox=(dy1, int(w * 0.55), dy2, text_right),
        confidence=0.88 if doc_val else 0.70,
        value=doc_val,
    ))

    # Date of Birth & Nationality (Middle text quadrant)
    dob_val = doc.get("date_of_birth")
    by1, by2 = int(h * 0.36), int(h * 0.52)
    regions.append(DocumentFieldRegion(
        field_name="date_of_birth",
        label="Date of Birth",
        bbox=_to_norm_bbox(by1, text_left, by2, text_right, h, w),
        pixel_bbox=(by1, text_left, by2, text_right),
        confidence=0.88 if dob_val else 0.70,
        value=dob_val,
    ))

    # Expiry Date (Lower text quadrant above MRZ)
    exp_val = doc.get("expiry_date")
    ey1, ey2 = int(h * 0.54), int(h * 0.74)
    regions.append(DocumentFieldRegion(
        field_name="expiry_date",
        label="Expiry Date",
        bbox=_to_norm_bbox(ey1, text_left, ey2, text_right, h, w),
        pixel_bbox=(ey1, text_left, ey2, text_right),
        confidence=0.85 if exp_val else 0.70,
        value=exp_val,
    ))

    return regions
