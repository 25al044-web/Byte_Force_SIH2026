"""Read-only verification of the blockchain audit layer."""

from fastapi import APIRouter
from app.services.blockchain.audit_service import verify_audit

router = APIRouter()


@router.get("/audit/{screening_id}")
def get_audit(screening_id: str):
    return verify_audit(screening_id)
