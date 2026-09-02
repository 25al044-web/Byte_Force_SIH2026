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
