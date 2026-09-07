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

    # 4. Biometric Face Verification is a local ONNX model, not a network service.
    from app.services.face_matcher import is_face_engine_ready
    face = is_face_engine_ready()
    face_status = "AVAILABLE" if face["ready"] else "UNAVAILABLE"

    # 5. Blockchain Audit Layer (Local Ethereum/Hardhat)
    try:
        from app.services.blockchain.blockchain_client import BlockchainClient
        blockchain = BlockchainClient().health()
        blockchain_status = "CONNECTED" if blockchain["ready"] else "UNAVAILABLE"
    except Exception as exc:
        blockchain, blockchain_status = {"ready": False, "error": "Blockchain unavailable"}, "UNAVAILABLE"

    return {
        "status": "ok",
        "backend": backend_status,
        "database": database_status,
        "ai_extraction": ai_status,
        "face_verification": face_status,
        "blockchain": blockchain_status,
        "face_verification_details": face,
        "blockchain_details": blockchain,
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
