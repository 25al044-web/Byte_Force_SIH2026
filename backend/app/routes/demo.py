"""Development and Demo helper endpoints for SIH26188.

Allows controlling demonstration features and resetting duplicate identity
scan history without touching seed blacklist records.
"""

import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.database import get_db_connection

router = APIRouter(prefix="/demo", tags=["demo"])


def is_demo_mode() -> bool:
    """Return True if DEMO_MODE is enabled in environment (default: True for dev)."""
    val = os.getenv("DEMO_MODE", "true").strip().lower()
    return val in ("true", "1", "yes", "on")


class DemoStatusResponse(BaseModel):
    demo_mode: bool
    status: str
    message: str


class DemoResetResponse(BaseModel):
    success: bool
    message: str
    cleared_table: str


@router.get(
    "/status",
    response_model=DemoStatusResponse,
    summary="Get Demo Mode Status",
    description="Returns whether the platform is currently operating in development/demo mode.",
)
def get_demo_status() -> DemoStatusResponse:
    active = is_demo_mode()
    return DemoStatusResponse(
        demo_mode=active,
        status="ok",
        message="Demo mode active with synthetic testing helpers enabled" if active else "Production mode active",
    )


@router.post(
    "/reset",
    response_model=DemoResetResponse,
    summary="Reset Demo Scan History",
    description="Development/Demo endpoint to clear stored identity embeddings for repeated duplicate testing. Blacklist seed records are preserved.",
)
def reset_demo_scan_history() -> DemoResetResponse:
    if not is_demo_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset endpoint is disabled in production mode (DEMO_MODE=false).",
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM identity_embeddings;")
        conn.commit()
        conn.close()
        return DemoResetResponse(
            success=True,
            message="Demo identity embeddings scan history successfully cleared. Blacklist seed data preserved.",
            cleared_table="identity_embeddings",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo scan history: {str(exc)}",
        )
