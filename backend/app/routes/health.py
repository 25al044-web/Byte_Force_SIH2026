"""Health check and system status endpoints for Sentinel ID."""

import os
from typing import Any, Dict
from fastapi import APIRouter
from app.database.session import get_db_connection

router = APIRouter()


def get_system_status() -> Dict[str, Any]:
    """Inspect all system subsystems and dependencies."""
    # 1. Backend Core API
    backend_status = "ONLINE"

    # 2. SQLite Database
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        database_status = "CONNECTED"
    except Exception:
        database_status = "ERROR"

    # 3. AI Document Extraction (Gemini Multimodal)
    ai_status = "AVAILABLE" if bool(os.getenv("GEMINI_API_KEY")) else "UNAVAILABLE"

    # 4. Biometric Face Verification (InsightFace ONNX)
    try:
        from app.services.face_matcher import _get_face_analysis_app
        app_instance = _get_face_analysis_app()
        face_status = "AVAILABLE" if app_instance is not None else "UNAVAILABLE"
    except Exception:
        face_status = "UNAVAILABLE"

    # 5. Blockchain Audit Layer (Local Ethereum/Hardhat)
    try:
        from app.services.blockchain.blockchain_client import BlockchainClient
        BlockchainClient()._contract()
        blockchain_status = "CONNECTED"
    except Exception:
        blockchain_status = "UNAVAILABLE"

    return {
        "status": "ok",
        "backend": backend_status,
        "database": database_status,
        "ai_extraction": ai_status,
        "face_verification": face_status,
        "blockchain": blockchain_status,
        "frontend": "RUNNING",
    }


@router.get("/health")
def get_health(detailed: bool = False):
    """Health check endpoint. Returns {'status': 'ok'} by default for contract compliance."""
    if not detailed:
        return {"status": "ok"}
    return get_system_status()


@router.get("/system/status")
def get_detailed_status():
    """System status dashboard endpoint for border security infrastructure."""
    return get_system_status()
