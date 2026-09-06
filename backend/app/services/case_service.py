"""Case management and review service for SIH26188.

Maintains suspicious, manual review, and high-risk case records
for border security officer inspection and triage.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.session import get_db_connection


def save_case(
    screening_id: str,
    risk_score: int,
    risk_level: str,
    recommendation: str,
    main_reason: str,
    status: str,
    extracted_identity: Optional[Dict[str, Any]] = None,
    detected_issues: Optional[List[str]] = None,
    document_integrity_status: Optional[str] = None,
    face_match_status: Optional[str] = None,
    review_status: str = "PENDING",
) -> None:
    """Save or update a screening case in the database."""
    conn = get_db_connection()
    try:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        identity_json = json.dumps(extracted_identity or {}, ensure_ascii=False)
        issues_json = json.dumps(detected_issues or [], ensure_ascii=False)

        conn.execute(
            """
            INSERT OR REPLACE INTO screening_cases (
                screening_id, risk_score, risk_level, recommendation,
                main_reason, status, review_status, extracted_identity,
                detected_issues, document_integrity_status, face_match_status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                screening_id,
                risk_score,
                risk_level,
                recommendation,
                main_reason,
                status,
                review_status,
                identity_json,
                issues_json,
                document_integrity_status or "PASS",
                face_match_status or "PASS",
                now_str,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _backfill_from_audits_if_empty(conn) -> None:
    """If screening_cases is empty, backfill any historical screening_audits records."""
    count = conn.execute("SELECT COUNT(*) as c FROM screening_cases").fetchone()["c"]
    if count > 0:
        return

    audit_rows = conn.execute(
        "SELECT screening_id, report_json, created_at FROM screening_audits ORDER BY created_at DESC"
    ).fetchall()

    for r in audit_rows:
        try:
            report = json.loads(r["report_json"]) if r["report_json"] else {}
            screening_id = r["screening_id"]
            risk_score = report.get("risk_score", 0)
            risk_level = report.get("risk_level", "LOW")
            recommendation = report.get("recommendation", "CLEAR")
            doc_status = report.get("document_integrity_status", "PASS")
            face_status = report.get("face_match_status", "PASS")

            main_reason = "Automated forensic inspection anomaly" if risk_level in ("HIGH", "REVIEW") else "Normal verification"
            issues = ["Forensic integrity anomaly identified" if doc_status in ("WARNING", "FAIL") else "Routine screening"]

            conn.execute(
                """
                INSERT OR IGNORE INTO screening_cases (
                    screening_id, risk_score, risk_level, recommendation,
                    main_reason, status, review_status, extracted_identity,
                    detected_issues, document_integrity_status, face_match_status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
                """,
                (
                    screening_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    main_reason,
                    doc_status,
                    json.dumps({}),
                    json.dumps(issues),
                    doc_status,
                    face_status,
                    r["created_at"],
                ),
            )
        except Exception:
            continue
    conn.commit()


def list_cases(only_requiring_review: bool = True) -> List[Dict[str, Any]]:
    """Retrieve cases for review, filtered by high risk or secondary inspection."""
    conn = get_db_connection()
    try:
        _backfill_from_audits_if_empty(conn)

        if only_requiring_review:
            query = """
                SELECT * FROM screening_cases
                WHERE (risk_level IN ('HIGH', 'REVIEW'))
                   OR (risk_score >= 20)
                   OR (status IN ('FAIL', 'WARNING'))
                   OR (document_integrity_status IN ('FAIL', 'WARNING', 'SUSPICIOUS'))
                   OR (recommendation = 'SECONDARY_INSPECTION_RECOMMENDED')
                   OR (recommendation = 'MANUAL_REVIEW_RECOMMENDED' AND risk_score > 0)
                ORDER BY created_at DESC
                LIMIT 100
            """
            rows = conn.execute(query).fetchall()
        else:
            query = """
                SELECT * FROM screening_cases
                ORDER BY created_at DESC
                LIMIT 100
            """
            rows = conn.execute(query).fetchall()

        results = []
        for r in rows:
            extracted_id = {}
            if r["extracted_identity"]:
                try:
                    extracted_id = json.loads(r["extracted_identity"])
                except Exception:
                    extracted_id = {}

            detected_issues = []
            if r["detected_issues"]:
                try:
                    detected_issues = json.loads(r["detected_issues"])
                except Exception:
                    detected_issues = []

            results.append({
                "screening_id": r["screening_id"],
                "risk_score": r["risk_score"],
                "risk_level": r["risk_level"],
                "recommendation": r["recommendation"],
                "main_reason": r["main_reason"],
                "status": r["status"],
                "review_status": r["review_status"],
                "extracted_identity": extracted_id,
                "detected_issues": detected_issues,
                "document_integrity_status": r["document_integrity_status"],
                "face_match_status": r["face_match_status"],
                "timestamp": r["created_at"],
            })
        return results
    finally:
        conn.close()


def get_case(screening_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single screening case by screening_id."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM screening_cases WHERE screening_id = ?",
            (screening_id,),
        ).fetchone()
        if not row:
            return None

        extracted_id = {}
        if row["extracted_identity"]:
            try:
                extracted_id = json.loads(row["extracted_identity"])
            except Exception:
                extracted_id = {}

        detected_issues = []
        if row["detected_issues"]:
            try:
                detected_issues = json.loads(row["detected_issues"])
            except Exception:
                detected_issues = []

        return {
            "screening_id": row["screening_id"],
            "risk_score": row["risk_score"],
            "risk_level": row["risk_level"],
            "recommendation": row["recommendation"],
            "main_reason": row["main_reason"],
            "status": row["status"],
            "review_status": row["review_status"],
            "extracted_identity": extracted_id,
            "detected_issues": detected_issues,
            "document_integrity_status": row["document_integrity_status"],
            "face_match_status": row["face_match_status"],
            "timestamp": row["created_at"],
        }
    finally:
        conn.close()
