"""Blacklist and sanctions screening service.

Matches applicant documents against active SQLite blacklist records.
Uses parameterized queries and synthetic demonstration data only.
"""

import sqlite3
from typing import Any, Dict, Optional

from app.database.session import get_db_connection


def check_blacklist(
    document_number: Optional[str],
    full_name: Optional[str] = None,
    nationality: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    db_conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    """Screens an identity against the SQLite demonstration blacklist.

    Primary matching is executed using the document number against active records.
    Does NOT leak internal database identifiers or sensitive metadata.

    Args:
        document_number: Official document / passport identifier.
        full_name: Optional full name (for future fuzzy/multi-factor matching).
        nationality: Optional nationality code.
        date_of_birth: Optional date of birth string.
        db_conn: Optional injected SQLite connection (defaults to managed connection).

    Returns:
        Structured result dict conforming to:
          - status: "PASS" | "FAIL" | "NOT_AVAILABLE"
          - reason: Human-readable explanation
          - match: Sanitized match details or None
    """
    if not document_number or not isinstance(document_number, str) or not document_number.strip():
        return {
            "status": "NOT_AVAILABLE",
            "reason": "No document number provided for blacklist screening",
            "match": None,
        }

    clean_doc_number = document_number.strip().upper()
    should_close = False
    conn = db_conn

    try:
        if conn is None:
            conn = get_db_connection()
            should_close = True

        cursor = conn.cursor()
        # Parameterized query targeting only active blacklist records
        cursor.execute(
            """
            SELECT document_number, reason, severity
            FROM blacklist
            WHERE UPPER(document_number) = ? AND is_active = 1
            LIMIT 1;
            """,
            (clean_doc_number,),
        )
        row = cursor.fetchone()

        if row:
            return {
                "status": "FAIL",
                "reason": "Document number matched active demonstration blacklist record",
                "match": {
                    "document_number": row["document_number"],
                    "reason": row["reason"],
                    "severity": row["severity"],
                },
            }
        else:
            return {
                "status": "PASS",
                "reason": "Document not found in demonstration blacklist",
                "match": None,
            }

    except Exception:
        # Gracefully handle database errors without crashing the pipeline
        return {
            "status": "NOT_AVAILABLE",
            "reason": "Blacklist database temporarily unavailable",
            "match": None,
        }
    finally:
        if should_close and conn is not None:
            conn.close()
