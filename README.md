# AI-Based Fake Identity & Document Screening System
**Problem Statement ID:** SIH26188 (SIH 2026)

## Overview
An intelligent screening system designed to detect counterfeit identity documents, forged credentials, facial mismatches, and duplicate identities using multi-modal AI screening and explainable risk scoring.

---

## Project Structure
```text
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point & CORS configuration
│   │   ├── routes/              # API route definitions
│   │   │   ├── __init__.py
│   │   │   └── health.py        # GET /api/health endpoint
│   │   ├── services/            # Business logic and future AI services
│   │   │   └── __init__.py
│   │   ├── database/            # SQLite connection and session management
│   │   │   ├── __init__.py
│   │   │   └── session.py
│   │   └── models/              # Pydantic schemas and database models
│   │       └── __init__.py
│   └── requirements.txt         # Minimal backend dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx              # React root component
│   │   ├── main.jsx             # React DOM entry point
│   │   └── index.css            # Modern styling
│   ├── index.html
│   ├── package.json             # Frontend dependencies (React + Vite)
│   └── vite.config.js           # Vite development server configuration
├── test_data/
│   ├── documents/               # Sample document images for testing
│   └── selfies/                 # Sample selfie images for biometric matching
├── docs/                        # Project documentation and architecture specs
├── .env.example                 # Sample environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # Project guide & instructions
```

---

## Prerequisites
- Python 3.10+ (Tested with Python 3.14)
- Node.js 18+ and npm (Tested with Node v22)

---

## Setup & Running Backend

## Local blockchain audit (optional but fully verifiable)

Use four terminals from the repository root:

```bash
# Terminal 1
cd blockchain
npm install
npm run blockchain:node

# Terminal 2 (after node is ready)
cd blockchain
npm run blockchain:deploy

# Terminal 3
cd backend
pip install -r requirements.txt
# Create .env from .env.example and set REGISTRY_OFFICER_PIN to a real six-digit value.
# Set BLOCKCHAIN_PRIVATE_KEY to one of the development keys printed by Hardhat.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 4
cd frontend
npm install
npm run dev
```

Deployment writes `blockchain/deployments/localhost.json`; the backend reads this
artifact automatically. `/api/blockchain/status` reports connected only after it
can reach RPC, find contract bytecode, and execute a contract read. If Hardhat is
offline, screening continues and the local audit row is marked `FAILED` rather
than claiming an on-chain transaction.

The Trusted Identity Registry requires `REGISTRY_OFFICER_PIN` (exactly six
digits). The PIN is validated only by the backend with bcrypt and unlocks a
15-minute, inactivity-refreshed session. Registry writes produce a canonical
SHA-256 metadata hash, which is stored locally and anchored in AuditTrail when
the chain is available. Verify screening records with `POST /api/audit/{id}/verify`.

### 1. Create and Activate Virtual Environment
From the project root:
```bash
# Windows PowerShell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Verify Backend Health
Open `http://127.0.0.1:8000/api/health` in your browser or run:
```bash
curl http://127.0.0.1:8000/api/health
```
Response:
```json
{
  "status": "ok"
}
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

---

## Setup & Running Frontend

### 1. Install Dependencies
From the project root:
```bash
cd frontend
npm install
```
*(On Windows PowerShell, if execution policy restricts npm, use `npm.cmd install`)*

### 2. Run Development Server
```bash
npm run dev
```
*(Or `npm.cmd run dev`)*

The frontend will be accessible at: `http://localhost:5173`

### 3. Build for Production
```bash
npm run build
```
*(Or `npm.cmd run build`)*

---

## Future Roadmap (AI Modules)
1. **Document Extraction**: Automated OCR field parsing for passports and identity cards.
2. **MRZ Validation**: ICAO Doc 9303 compliance and checksum validation.
3. **Document Tamper Screening**: Splicing, pixel inconsistency, and digital forgery detection.
4. **Face Matching**: High-precision 1:1 facial biometric verification between document and selfie.
5. **Duplicate Identity Screening**: Vector and hash matching across registered identity records.
6. **Blacklist Checking**: Automated lookup against watchlists and sanctioned entity registries.
7. **Explainable Risk Scoring**: Aggregated confidence scores and human-interpretable reasoning.
