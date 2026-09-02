# API Contract Specification

**Project:** SIH26188 — AI-Based Fake Identity & Document Screening System  
**Version:** 1.0.0 (MVP Architecture Contract)  
**Protocol:** HTTP/1.1 or HTTP/2  
**Base URL:** `/api`

---

## 1. Overview

The Screening Pipeline API provides a unified gateway for automated identity document verification, biometric facial matching, tamper detection, duplicate screening, and explainable risk evaluation.

---

## 2. Endpoints

### 2.1 Screening Endpoint

- **Method:** `POST`
- **Path:** `/api/screen`
- **Content-Type:** `multipart/form-data`
- **Accept:** `application/json`

#### 2.1.1 Request Payload (Multipart Form Data)

| Field Name | Type | Required | Allowed MIME Types | Description |
| :--- | :--- | :--- | :--- | :--- |
| `document_image` | File (`binary`) | **Yes** | `image/jpeg`, `image/png`, `image/webp`, `application/pdf` | Scanned or photographed travel/identity document (e.g., passport, national ID card, driver's license). |
| `selfie_image` | File (`binary`) | **Yes** | `image/jpeg`, `image/png`, `image/webp` | Live captured portrait or selfie of the applicant for biometric matching. |

#### 2.1.2 Response Headers

```http
Content-Type: application/json
```

#### 2.1.3 Response Schema (`200 OK`)

```json
{
  "screening_id": "SCR-2026-0001",
  "document": {
    "document_type": "passport",
    "full_name": "ARUN KUMAR",
    "document_number": "P1234567",
    "nationality": "IND",
    "date_of_birth": "2004-08-20",
    "expiry_date": "2032-08-14",
    "sex": "M"
  },
  "checks": {
    "mrz": {
      "status": "PASS",
      "score": 0,
      "reason": "MRZ checksums valid"
    },
    "expiry": {
      "status": "PASS",
      "score": 0,
      "reason": "Document is valid"
    },
    "tamper": {
      "status": "WARNING",
      "risk": 32,
      "reason": "Possible image compression inconsistency"
    },
    "face_match": {
      "status": "PASS",
      "similarity": 91.7,
      "reason": "Selfie is visually consistent with document portrait"
    },
    "duplicate_identity": {
      "status": "PASS",
      "similar_identity": null,
      "reason": "No matching face associated with another identity"
    },
    "blacklist": {
      "status": "PASS",
      "reason": "Document not found in demonstration blacklist"
    }
  },
  "risk": {
    "score": 27,
    "level": "REVIEW"
  },
  "explanations": [
    "MRZ validation passed",
    "Document has not expired",
    "Possible compression inconsistency detected",
    "Face comparison passed"
  ]
}
```

---

## 3. Data Dictionary & Rules

### 3.1 Screening Identifier

- **Field:** `screening_id` (`string`)
- **Format:** `SCR-YYYY-XXXX` or standard UUID (e.g. `SCR-2026-0001`)
- Unique identifier assigned to each screening transaction for audit logging and retrieval.

### 3.2 Document Metadata (`document`)

Extracted OCR/MRZ data from the submitted identity document.  
> [!IMPORTANT]
> **Field Nullability & Integrity**: If extraction fails for any field, the field value MUST be `null`. Missing or unreadable information must NEVER be fabricated or hallucinated.

| Field | Type | Nullable | Format / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `document_type` | string | Yes | `passport`, `national_id`, `driving_license`, or other standard ID types | Classified type of identity document. |
| `full_name` | string | Yes | Uppercase string (e.g., `"ARUN KUMAR"`) | Extracted full legal name of the bearer. |
| `document_number`| string | Yes | Alphanumeric (e.g., `"P1234567"`) | Official identification or passport number. |
| `nationality` | string | Yes | ISO 3166-1 alpha-3 code (e.g., `"IND"`) | Nationality or issuing jurisdiction. |
| `date_of_birth` | string | Yes | `YYYY-MM-DD` | Date of birth of the document holder. |
| `expiry_date` | string | Yes | `YYYY-MM-DD` | Expiration date of the document. |
| `sex` | string | Yes | `"M"`, `"F"`, `"X"` | Sex/gender as recorded on the document. |

---

### 3.3 Pipeline Checks (`checks`)

Each check evaluation produces a standardized status, associated confidence/risk score, and an explanatory human-readable reason.

#### Allowed Check Status Values

All checks MUST output one of the following four status values:

- `PASS`: The check completed successfully with no anomalies or policy violations detected.
- `WARNING`: An anomaly or minor discrepancy was detected that warrants manual verification, but does not definitively indicate fraud.
- `FAIL`: A definitive policy violation, invalid checksum, expiration, tampering indicator, biometric mismatch, or blacklist hit was identified.
- `NOT_AVAILABLE`: The check could not be performed (e.g., non-MRZ document submitted, face could not be detected, or external service unavailable).

#### Check Definitions

1. **`mrz` (Machine Readable Zone Check)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `score`: `number | null` (e.g., `0` indicating 0 check digit errors, or compliance score)
   - `reason`: `string` (Descriptive diagnostic message)

2. **`expiry` (Validity / Expiration Check)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `score`: `number | null`
   - `reason`: `string` (e.g., `"Document is valid"`, `"Document has expired"`)

3. **`tamper` (Document Forgery & Tamper Screening)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `risk`: `number | null` (Quantified tampering risk score: 0 to 100)
   - `reason`: `string` (e.g., `"Possible image compression inconsistency"`, `"No digital alterations detected"`)

4. **`face_match` (Biometric Comparison)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `similarity`: `number | null` (Biometric similarity percentage: 0.0 to 100.0)
   - `reason`: `string` (e.g., `"Selfie is visually consistent with document portrait"`)

5. **`duplicate_identity` (Duplicate Identity Detection)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `similar_identity`: `string | object | null` (Reference ID of conflicting identity, or null if none)
   - `reason`: `string` (e.g., `"No matching face associated with another identity"`)

6. **`blacklist` (Sanctions & Watchlist Screening)**
   - `status`: `CheckStatus` (`PASS`, `WARNING`, `FAIL`, `NOT_AVAILABLE`)
   - `reason`: `string` (e.g., `"Document not found in demonstration blacklist"`)

---

### 3.4 Risk Assessment (`risk`)

Consolidated risk rating calculated from individual check outcomes.

| Field | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `score` | integer | `0` to `100` (inclusive) | Overall calculated fraud risk index (0 = lowest risk, 100 = critical risk). |
| `level` | string | `LOW`, `REVIEW`, `HIGH` | Operational triaging classification for border/inspection officials. |

#### Risk Level Classifications

- `LOW`: Document passes all primary security and identity checks. Automated clearance recommended.
- `REVIEW`: Ambiguities, minor compression anomalies, or borderline biometric thresholds detected. Secondary human officer inspection recommended.
- `HIGH`: Confirmed tampering, invalid/forged MRZ, expired credentials, face mismatch, or watchlist hit detected. Immediate rejection or intervention required.

---

### 3.5 Explanations (`explanations`)

- **Field:** `explanations` (`Array<string>`)
- A deterministic or model-generated list of bulleted, auditable findings summarizing why the document was given its respective risk score and level.

---

## 4. Error Codes & Handling

| HTTP Status | Error Code | Description | Response Body Example |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | `INVALID_FILE_TYPE` | Uploaded file was not an allowed image or document format. | `{"detail": "File 'document_image' must be an image (JPEG, PNG, WEBP) or PDF."}` |
| `422 Unprocessable Entity` | `MISSING_FIELD` | Required multipart form fields (`document_image`, `selfie_image`) were omitted. | `{"detail": [{"loc": ["body", "document_image"], "msg": "Field required", "type": "missing"}]}` |
| `500 Internal Server Error` | `PROCESSING_ERROR` | Uncaught exception during pipeline execution. | `{"detail": "Internal processing error occurred while screening document."}` |

---

## 5. Health Check Endpoint

### 5.1 Health Check

- **Method:** `GET`
- **Path:** `/api/health`
- **Accept:** `application/json`

#### Response (`200 OK`)

```json
{
  "status": "ok"
}
```
