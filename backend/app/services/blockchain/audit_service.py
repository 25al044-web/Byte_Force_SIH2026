"""Orchestrates local canonical reports and the optional immutable ledger."""

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict

from app.database.session import get_db_connection
from app.services.blockchain.blockchain_client import BlockchainClient, BlockchainUnavailable
from app.services.blockchain.hash_service import canonical_json, hash_report, sha256_bytes

logger = logging.getLogger(__name__)


def _safe_report(screening_id: str, document_bytes: bytes, selfie_bytes: bytes, result: Dict[str, Any]) -> Dict[str, Any]:
    """Only hashes of uploads, status values, and non-PII result metadata."""
    return {
        "screening_id": screening_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "document_hash": sha256_bytes(document_bytes),
        "selfie_hash": sha256_bytes(selfie_bytes),
        "risk_score": result["risk"]["score"],
        "risk_level": result["risk"]["level"],
        "document_integrity_status": result["checks"]["tamper"]["status"],
        "face_match_status": result["checks"]["face_match"]["status"],
        "recommendation": result["checks"]["tamper"].get("recommendation") or "MANUAL_REVIEW_RECOMMENDED",
    }


def _save_local(screening_id: str, report: Dict[str, Any], report_hash: str, blockchain_meta: Dict[str, Any]) -> None:
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO screening_audits (screening_id, report_json, report_hash, document_hash, transaction_hash, block_number, audit_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                screening_id,
                canonical_json(report),
                report_hash,
                report["document_hash"],
                blockchain_meta.get("transaction_hash"),
                blockchain_meta.get("block_number"),
                blockchain_meta["status"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _async_anchor_audit(screening_id: str, report_hash: str) -> None:
    """Background worker to anchor screening report hash on-chain without blocking."""
    try:
        receipt = BlockchainClient().record("SCREENING", screening_id, "SCREENING_COMPLETED", report_hash)
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE screening_audits SET transaction_hash = ?, block_number = ?, audit_status = 'RECORDED' WHERE screening_id = ?",
                (receipt.get("transaction_hash"), receipt.get("block_number"), screening_id),
            )
            conn.commit()
        finally:
            conn.close()
    except BlockchainUnavailable:
        pass
    except Exception as exc:
        logger.debug("Background screening audit anchoring for %s failed: %s", screening_id, exc)


def create_audit(
    screening_id: str,
    document_bytes: bytes,
    selfie_bytes: bytes,
    result: Dict[str, Any],
    async_anchor: bool = True,
) -> Dict[str, Any]:
    report = _safe_report(screening_id, document_bytes, selfie_bytes, result)
    report_hash = hash_report(report)
    metadata: Dict[str, Any] = {
        "status": "RECORDED",
        "screening_id": screening_id,
        "report_hash": f"0x{report_hash}",
        "transaction_hash": None,
        "block_number": None,
        "verified": False,
    }

    if not async_anchor:
        try:
            receipt = BlockchainClient().record("SCREENING", screening_id, "SCREENING_COMPLETED", report_hash)
            metadata.update({**receipt, "verified": True})
        except BlockchainUnavailable:
            metadata["status"] = "UNAVAILABLE"

    # Immediately write local canonical audit to SQLite (<1ms)
    _save_local(screening_id, report, report_hash, metadata)

    # Submit the blockchain transaction asynchronously in a background worker thread
    if async_anchor:
        t = threading.Thread(target=_async_anchor_audit, args=(screening_id, report_hash), daemon=True)
        t.start()

    return metadata


def _async_anchor_event(event_id: int, entity_type: str, entity_id: str, action: str, data_hash: str, previous_hash: str) -> None:
    """Background worker to anchor audit event on-chain without blocking."""
    try:
        receipt = BlockchainClient().record(entity_type, entity_id, action, data_hash, previous_hash or "0" * 64)
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE audit_events SET transaction_hash = ?, block_number = ?, blockchain_audit_id = ?, blockchain_status = 'RECORDED' WHERE id = ?",
                (receipt.get("transaction_hash"), receipt.get("block_number"), receipt.get("blockchain_audit_id"), event_id),
            )
            conn.commit()
        finally:
            conn.close()
    except BlockchainUnavailable:
        conn = get_db_connection()
        try:
            conn.execute("UPDATE audit_events SET blockchain_status = 'FAILED' WHERE id = ?", (event_id,))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:
        logger.debug("Background event anchoring failed: %s", exc)


def record_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    action: str,
    data: Dict[str, Any],
    previous_hash: str = "",
    async_anchor: bool = True,
) -> Dict[str, Any]:
    """Persist a safe, canonical audit event and anchor it asynchronously."""
    safe_json, data_hash = canonical_json(data), hash_report(data)
    meta: Dict[str, Any] = {"status": "RECORDED", "data_hash": data_hash}

    if not async_anchor:
        try:
            meta.update(BlockchainClient().record(entity_type, entity_id, action, data_hash, previous_hash or "0" * 64))
            meta["status"] = "RECORDED"
        except BlockchainUnavailable as exc:
            meta.update({"status": "FAILED", "error": str(exc)})

    conn = get_db_connection()
    try:
        cur = conn.execute(
            "INSERT INTO audit_events (event_type,entity_type,entity_id,action,data_json,data_hash,previous_hash,transaction_hash,block_number,blockchain_audit_id,blockchain_status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                event_type,
                entity_type,
                entity_id,
                action,
                safe_json,
                data_hash,
                previous_hash or None,
                meta.get("transaction_hash"),
                meta.get("block_number"),
                meta.get("blockchain_audit_id"),
                meta["status"],
            ),
        )
        conn.commit()
        meta["id"] = cur.lastrowid
    finally:
        conn.close()

    if async_anchor and meta.get("id"):
        t = threading.Thread(
            target=_async_anchor_event,
            args=(meta["id"], entity_type, entity_id, action, data_hash, previous_hash),
            daemon=True,
        )
        t.start()

    return meta


def verify_audit(screening_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT report_json, report_hash, transaction_hash, block_number, audit_status FROM screening_audits WHERE screening_id = ?",
            (screening_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"screening_id": screening_id, "integrity_status": "NOT_FOUND"}
    current_hash = hash_report(__import__("json").loads(row["report_json"]))
    stored_hash = row["report_hash"]
    status = "VERIFIED" if current_hash == stored_hash else "TAMPERED"
    return {
        "screening_id": screening_id,
        "stored_hash": f"0x{stored_hash}",
        "current_hash": f"0x{current_hash}",
        "integrity_status": status,
        "transaction_hash": row["transaction_hash"],
        "block_number": row["block_number"],
        "audit_status": row["audit_status"],
    }
