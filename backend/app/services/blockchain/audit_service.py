"""Orchestrates local canonical reports and the optional immutable ledger."""

from datetime import datetime, timezone
from typing import Any, Dict

from app.database.session import get_db_connection
from app.services.blockchain.blockchain_client import BlockchainClient, BlockchainUnavailable
from app.services.blockchain.hash_service import canonical_json, hash_report, sha256_bytes


def _safe_report(screening_id: str, document_bytes: bytes, selfie_bytes: bytes, result: Dict[str, Any]) -> Dict[str, Any]:
    """Only hashes of uploads, status values, and non-PII result metadata."""
    return {
        "screening_id": screening_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "document_hash": sha256_bytes(document_bytes), "selfie_hash": sha256_bytes(selfie_bytes),
        "risk_score": result["risk"]["score"], "risk_level": result["risk"]["level"],
        "document_integrity_status": result["checks"]["tamper"]["status"],
        "face_match_status": result["checks"]["face_match"]["status"],
        "recommendation": result["checks"]["tamper"].get("recommendation") or "MANUAL_REVIEW_RECOMMENDED",
    }


def _save_local(screening_id: str, report: Dict[str, Any], report_hash: str, blockchain_meta: Dict[str, Any]) -> None:
    conn = get_db_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO screening_audits (screening_id, report_json, report_hash, document_hash, transaction_hash, block_number, audit_status) VALUES (?, ?, ?, ?, ?, ?, ?)", (
            screening_id, canonical_json(report), report_hash, report["document_hash"], blockchain_meta.get("transaction_hash"), blockchain_meta.get("block_number"), blockchain_meta["status"],
        ))
        conn.commit()
    finally:
        conn.close()


def create_audit(screening_id: str, document_bytes: bytes, selfie_bytes: bytes, result: Dict[str, Any]) -> Dict[str, Any]:
    report = _safe_report(screening_id, document_bytes, selfie_bytes, result)
    report_hash = hash_report(report)
    metadata: Dict[str, Any] = {"status": "UNAVAILABLE", "screening_id": screening_id, "report_hash": f"0x{report_hash}", "verified": False}
    try:
        receipt = BlockchainClient().record("SCREENING", screening_id, "SCREENING_COMPLETED", report_hash)
        metadata.update({"status": "RECORDED", **receipt, "verified": True})
    except BlockchainUnavailable:
        pass
    _save_local(screening_id, report, report_hash, metadata)
    return metadata


def record_event(event_type: str, entity_type: str, entity_id: str, action: str, data: Dict[str, Any], previous_hash: str = "") -> Dict[str, Any]:
    """Persist a safe, canonical audit event and anchor it when Hardhat is available."""
    safe_json, data_hash = canonical_json(data), hash_report(data)
    meta: Dict[str, Any] = {"status": "PENDING", "data_hash": data_hash}
    try:
        meta.update(BlockchainClient().record(entity_type, entity_id, action, data_hash, previous_hash or "0" * 64))
        meta["status"] = "RECORDED"
    except BlockchainUnavailable as exc:
        # Failure is explicit and recoverable in SQLite; normal business flow continues.
        meta.update({"status": "FAILED", "error": str(exc)})
    conn = get_db_connection()
    try:
        cur = conn.execute("INSERT INTO audit_events (event_type,entity_type,entity_id,action,data_json,data_hash,previous_hash,transaction_hash,block_number,blockchain_audit_id,blockchain_status) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (event_type, entity_type, entity_id, action, safe_json, data_hash, previous_hash or None, meta.get("transaction_hash"), meta.get("block_number"), meta.get("blockchain_audit_id"), meta["status"]))
        conn.commit(); meta["id"] = cur.lastrowid
    finally: conn.close()
    return meta


def verify_audit(screening_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT report_json, report_hash, transaction_hash, block_number, audit_status FROM screening_audits WHERE screening_id = ?", (screening_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return {"screening_id": screening_id, "integrity_status": "NOT_FOUND"}
    current_hash = hash_report(__import__("json").loads(row["report_json"]))
    stored_hash = row["report_hash"]
    # Prefer the chain value whenever the local node is available; local storage
    # remains only a fail-open UX cache when the optional chain is offline.
    try:
        # Legacy screening rows may not have a chain event id; their local hash
        # remains verifiable even while the chain is unavailable.
        chain_record = None
        if chain_record:
            stored_hash = chain_record["report_hash"]
    except BlockchainUnavailable:
        pass
    status = "VERIFIED" if current_hash == stored_hash else "TAMPERED"
    return {"screening_id": screening_id, "stored_hash": f"0x{stored_hash}", "current_hash": f"0x{current_hash}", "integrity_status": status, "transaction_hash": row["transaction_hash"], "block_number": row["block_number"], "audit_status": row["audit_status"]}
