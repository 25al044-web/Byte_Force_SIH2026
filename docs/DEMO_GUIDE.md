# SIH26188: Hackathon Demonstration & Evaluation Guide

## AI-Based Fake Identity & Document Screening System

This guide outlines the setup, architecture, and step-by-step presentation scenarios for the jury evaluation.

---

## 1. Quick Startup (One-Click)

The repository provides a single-command launcher for Windows environments:

```bat
START_APP.bat
```

### What it does:
1. Verifies the Python backend virtual environment (`backend\.venv`).
2. Verifies frontend dependencies (`frontend\node_modules`).
3. Verifies local InsightFace model cache (`buffalo_sc`).
4. Launches the FastAPI screening server on `http://127.0.0.1:8000`.
5. Launches the React + Vite frontend on `http://localhost:5173`.
6. Automatically launches the default web browser to the screening dashboard.

### Graceful Shutdown:
To terminate all backend and frontend services cleanly:
```bat
STOP_APP.bat
```

---

## 2. Model Readiness & Local Cache

Biometric face verification and selfie embedding extraction use the lightweight **InsightFace `buffalo_sc`** model running on ONNX Runtime CPU.

* **Local Cache Path:** `C:\Users\<user>\.insightface\models\buffalo_sc`
* **Local Model Files:**
  * `det_500m.onnx` (~2.5 MB) — SCRFD Face Detector
  * `w600k_mbf.onnx` (~13.6 MB) — MobileFaceNet ArcFace Biometric Feature Extractor
* **Pre-cached Status:** Verified present locally. **No network download will occur during the jury presentation.**

---

## 3. Development / Demo Mode & State Reset

* The platform operates with `DEMO_MODE=true` by default, enabling testing helpers while maintaining real screening modules.
* **Resetting Demo State:** To demonstrate duplicate identity detection multiple times, click the **Reset Demo Data** button in the top navigation bar or run:
  ```powershell
  python backend\scripts\reset_demo_data.py
  ```
  *(This clears stored applicant face embeddings from `identity_embeddings` without altering seed blacklist watchlist records).*

---

## 4. Live Hackathon Demonstration Scenarios

### Scenario 1: Clean Authentic Document + Matching Selfie
* **Objective:** Demonstrate normal, seamless border clearance for a legitimate traveler.
* **Input:**
  * Document: Authentic passport/ID image.
  * Selfie: Matching live applicant photograph.
* **Expected Results:**
  * **Risk Score:** `0 - 15` (`LOW RISK`)
  * **MRZ Verification:** `PASS` (Check digit parity verified)
  * **Expiry Verification:** `PASS` (Valid future expiration)
  * **Face Match:** `PASS` (Similarity $> 90\%$)
  * **Duplicate Identity:** `PASS` (No recurring face found under another document)
  * **Blacklist Screening:** `PASS` (No match in enforcement watchlist)
  * **Tamper Screening:** `PASS` (Uniform compression & sensor noise)
* **What to explain to the Jury:**
  > "The multimodal pipeline extracts identity fields, mathematically validates ICAO check digits, confirms the live selfie matches the document portrait with high confidence, and yields an explainable clearance score."

---

### Scenario 2: Document with Mismatched Selfie (Impostor Attempt)
* **Objective:** Detect when an unauthorized individual attempts to cross a border using someone else's valid passport.
* **Input:**
  * Document: Valid passport.
  * Selfie: Live photograph of a completely different person.
* **Expected Results:**
  * **Face Match:** `FAIL` or `WARNING` (Similarity $< 80\%$)
  * **Risk Assessment:** Elevated to `REVIEW` or `HIGH`
  * **Explanations:** Clear warning: *"Face comparison failed: low similarity between selfie and document portrait."*
* **What to explain to the Jury:**
  > "Even if the travel document is 100% authentic, the biometric ArcFace verification isolates and flags the impostor attempt immediately."

---

### Scenario 3: Watchlist / Blacklisted Synthetic Document
* **Objective:** Demonstrate instant interception of flagged individuals and forged numbers on enforcement lists.
* **Input:**
  * Document Number: `TEST0001` or `DEMO9999` (or specify query parameter `?doc_number_override=TEST0001`).
* **Expected Results:**
  * **Blacklist Screening:** `FAIL` (Red alert)
  * **Match Details:** Matches active high-priority watchlist record (Terrorism / Document Fraud).
  * **Risk Score:** `85 - 100` (`HIGH RISK`)
  * **Critical Override:** Immediately enforces maximum risk level regardless of other pass checks.
* **What to explain to the Jury:**
  > "The system features a real SQLite watchlist engine with exact and normalized fuzzy matching. Any hit enforces a hard critical risk override, demanding immediate officer intervention."

---

### Scenario 4: Duplicate Identity Detection (Same Face, Different Documents)
* **Objective:** Expose identity fraud syndicates where one individual creates multiple identities under different registration numbers.
* **Execution:**
  1. **First Scan:** Ingest document with Number `DEMO-A` and Applicant Face X.
     * *Result:* `Duplicate Identity: PASS` (Stored in secure SQLite vector store).
  2. **Second Scan:** Ingest document with Number `DEMO-B` and the **same Applicant Face X**.
     * *Result:* `Duplicate Identity: FAIL`
     * *Match:* Detected recurring face under document `DEMO-A` with $\ge 90\%$ similarity.
     * *Risk Impact:* Risk score immediately jumps to $\ge 75$ (`HIGH RISK`).
  3. **Same-Document Idempotency:** Re-scanning `DEMO-A` with Face X returns `PASS` (bypasses duplicate warning because it is the legitimate document holder re-scanning).
* **What to explain to the Jury:**
  > "Traditional systems only check whether a document looks authentic. Our system extracts a 512-dimensional ArcFace embedding and checks for prior occurrences under different document IDs. Privacy is built-in: no selfies or face photos are stored, only privacy-preserving JSON float vectors."

---

### Scenario 5: Tampered / Spliced Document (Digital Forgery)
* **Objective:** Detect digital manipulation, cut-and-paste alterations, and cloned security stamps.
* **Input:**
  * Document: Image containing spliced text, altered photo box, or duplicate cloned stamps.
* **Expected Results:**
  * **Tamper Screening:** `WARNING` or `FAIL`
  * **Forensic Reason:** Explains specific visual anomalies (e.g. localized ELA compression variance, sensor noise disparity, or SIFT copy-move clusters).
  * **Risk Engine Impact:** Adds $+10$ to $+40$ risk contribution.
* **What to explain to the Jury:**
  > "Rather than relying on opaque deep-learning models that hallucinate, we execute explainable forensic algorithms: Error Level Analysis (ELA) for recompression artifacts, edge-masked high-frequency noise variance, and SIFT copy-move feature clustering. It runs on CPU in under 0.2 seconds."

---

## 5. Offline & API Resilience Handling

* **Gemini Extraction Resilience:** If the network is offline or the Gemini API key is missing:
  * The server will **not** crash.
  * Document fields will be marked `Not available` (no fabricated mock data).
  * The frontend displays a prominent amber notice: *"Document extraction service unavailable or unreadable."*
  * Biometric face matching, duplicate identity detection, and OpenCV tamper screening **continue to run locally on CPU**.

---

## 6. Architecture Summary

```
                       [ Uploaded Document & Selfie ]
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      ▼                              ▼                              ▼
[ Gemini 2.5 Flash ]       [ InsightFace ArcFace ]        [ OpenCV Forensics ]
Document Extraction            Face Comparison &              ELA & Noise
& TD3 MRZ Parsing             Selfie Embedding               Tamper Screening
      │                              │                              │
      ▼                              ▼                              ▼
[ ICAO MRZ Check ]        [ Duplicate Identity Store ]    [ Visual Indicators ]
Parity Calculations        SQLite Cosine Vector Lookup     Compression & Noise
      │                              │                              │
      └──────────────────────────────┼──────────────────────────────┘
                                     ▼
                        [ SQLite Blacklist Check ]
                         Normalized Exact & Fuzzy
                                     │
                                     ▼
                    [ Explainable Risk Engine (0-100) ]
                     Weighted Scoring & Hard Overrides
                                     │
                                     ▼
                     [ React Border Security Dashboard ]
                       Triage Decision: LOW / REVIEW / HIGH
```

---

## 7. Verification Checklist Before Presentation

- [x] Backend running on `http://127.0.0.1:8000` (`GET /api/health` returns `200 OK`)
- [x] Frontend running on `http://localhost:5173`
- [x] `buffalo_sc` models pre-cached locally
- [x] 125 backend tests passing with zero failures
- [x] Production build clean (`npm run build` succeeds)
- [x] No API keys or raw images committed to Git
