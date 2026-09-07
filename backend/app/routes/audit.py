"""Read-only listing and verification of the blockchain audit layer."""

import json
from typing import Any, Dict, List
from fastapi import APIRouter
from app.database.session import get_db_connection
from app.services.blockchain.audit_service import verify_audit
from app.services.blockchain.blockchain_client import BlockchainClient

router = APIRouter()

@router.get("/blockchain/status")
def blockchain_status() -> Dict[str, Any]:
    """Truthful local Hardhat and deployed-contract readiness probe."""
    return BlockchainClient().health()


@router.get("/audit")
def list_audits() -> Dict[str, Any]:
    """Retrieve audit records for the immutable audit trail dashboard."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT screening_id, report_json, report_hash, document_hash,
                   transaction_hash, block_number, audit_status, created_at
            FROM screening_audits
            ORDER BY created_at DESC
            LIMIT 100
            """
        ).fetchall()

        audits: List[Dict[str, Any]] = []
        for r in rows:
            report: Dict[str, Any] = {}
            if r["report_json"]:
                try:
                    report = json.loads(r["report_json"])
                except Exception:
                    report = {}

            report_h = r["report_hash"]
            if report_h and not str(report_h).startswith("0x"):
                report_h = f"0x{report_h}"

            doc_h = r["document_hash"]
            if doc_h and not str(doc_h).startswith("0x"):
                doc_h = f"0x{doc_h}"

            audits.append({
                "screening_id": r["screening_id"],
                "timestamp": report.get("timestamp") or r["created_at"],
                "blockchain_status": r["audit_status"],
                "report_hash": report_h,
                "document_hash": doc_h,
                "transaction_hash": r["transaction_hash"],
                "block_number": r["block_number"],
                "created_at": r["created_at"],
                "risk_score": report.get("risk_score"),
                "risk_level": report.get("risk_level"),
                "recommendation": report.get("recommendation"),
            })

        # Check if local Ethereum/Hardhat testnet is configured & available
        blockchain_configured = False
        try:
            from app.services.blockchain.blockchain_client import BlockchainClient
            BlockchainClient()._contract()
            blockchain_configured = True
        except Exception:
            blockchain_configured = False

        return {
            "audits": audits,
            "total": len(audits),
            "blockchain_configured": blockchain_configured,
        }
    finally:
        conn.close()


@router.get("/audit/{screening_id}")
def get_audit(screening_id: str):
    """Verify cryptographic hash and blockchain consensus for a given screening record."""
    return verify_audit(screening_id)

@router.post("/audit/{screening_id}/verify")
def verify_audit_post(screening_id: str):
    result = verify_audit(screening_id)
    return {"verified": result.get("integrity_status") == "VERIFIED", "database_hash": result.get("current_hash"), "blockchain_hash": result.get("stored_hash"), "transaction_hash": result.get("transaction_hash"), "block_number": result.get("block_number"), **result}
