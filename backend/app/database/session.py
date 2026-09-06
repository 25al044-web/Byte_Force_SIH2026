"""Database connection and session utilities for SQLite."""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = os.getenv("DATABASE_URL", str(BASE_DIR / "screening.db"))

# Clearly labeled synthetic demonstration records for development and testing
SYNTHETIC_BLACKLIST_SEEDS = [
    {
        "document_number": "TEST0001",
        "full_name": "DEMO PERSON",
        "nationality": "IND",
        "date_of_birth": "1985-05-15",
        "reason": "Synthetic stolen-document demonstration record",
        "severity": "HIGH",
        "is_active": 1,
    },
    {
        "document_number": "DEMO9999",
        "full_name": "SYNTHETIC FLAGGED ENTITY",
        "nationality": "GBR",
        "date_of_birth": "1990-11-20",
        "reason": "Synthetic financial sanctions watchlist demonstration record",
        "severity": "CRITICAL",
        "is_active": 1,
    },
    {
        "document_number": "BLACKLIST01",
        "full_name": "FICTIONAL SUBJECT ALPHA",
        "nationality": "USA",
        "date_of_birth": "1978-03-10",
        "reason": "Synthetic border alert demonstration record",
        "severity": "MEDIUM",
        "is_active": 1,
    },
    {
        "document_number": "INACTIVE01",
        "full_name": "INACTIVE RECORD DEMO",
        "nationality": "IND",
        "date_of_birth": "1995-01-01",
        "reason": "Synthetic historical record that has been deactivated",
        "severity": "LOW",
        "is_active": 0,
    },
]

SYNTHETIC_TRUSTED_SEEDS = [
    {
        "registry_id": "TIR-ID123456",
        "full_name": "ARUN KUMAR",
        "document_number": "ID123456",
        "document_type": "PASSPORT",
        "date_of_birth": "1995-05-15",
        "nationality": "IND",
        "photo_path_or_reference": None,
        "photo_embedding": None,
        "notes": "Verified synthetic passport identity for cross-verification testing",
        "is_active": 1,
    },
    {
        "registry_id": "TIR-DL987654",
        "full_name": "PRIYA SHARMA",
        "document_number": "DL987654",
        "document_type": "DRIVING_LICENSE",
        "date_of_birth": "1992-08-24",
        "nationality": "IND",
        "photo_path_or_reference": None,
        "photo_embedding": None,
        "notes": "Synthetic driving license registered record",
        "is_active": 1,
    },
    {
        "registry_id": "TIR-PASS456789",
        "full_name": "JOHN DOE",
        "document_number": "PASS456789",
        "document_type": "PASSPORT",
        "date_of_birth": "1988-12-05",
        "nationality": "USA",
        "photo_path_or_reference": None,
        "photo_embedding": None,
        "notes": "Synthetic international passport record",
        "is_active": 1,
    },
]


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a new SQLite database connection.

    Args:
        db_path: Optional database file path or URI (defaults to DB_FILE).
    """
    target = db_path or os.getenv("DATABASE_URL", str(BASE_DIR / "screening.db"))
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


def seed_blacklist_data(conn: sqlite3.Connection) -> int:
    """Idempotently seed synthetic demonstration blacklist records.

    Uses INSERT OR IGNORE against the unique document_number column
    to ensure no duplicates are created on repeated startup.

    Returns:
        Number of newly inserted records.
    """
    cursor = conn.cursor()
    inserted_count = 0
    query = """
        INSERT OR IGNORE INTO blacklist (
            document_number,
            full_name,
            nationality,
            date_of_birth,
            reason,
            severity,
            is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    for rec in SYNTHETIC_BLACKLIST_SEEDS:
        cursor.execute(
            query,
            (
                rec["document_number"],
                rec["full_name"],
                rec["nationality"],
                rec["date_of_birth"],
                rec["reason"],
                rec["severity"],
                rec["is_active"],
            ),
        )
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    return inserted_count


def seed_trusted_registry(conn: sqlite3.Connection) -> int:
    """Idempotently seed synthetic demonstration trusted registry records.

    Uses INSERT OR IGNORE against the unique registry_id column.

    Returns:
        Number of newly inserted records.
    """
    cursor = conn.cursor()
    inserted_count = 0
    query = """
        INSERT OR IGNORE INTO trusted_identities (
            registry_id,
            full_name,
            document_number,
            document_type,
            date_of_birth,
            nationality,
            photo_path_or_reference,
            photo_embedding,
            notes,
            is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for rec in SYNTHETIC_TRUSTED_SEEDS:
        cursor.execute(
            query,
            (
                rec["registry_id"],
                rec["full_name"],
                rec["document_number"],
                rec["document_type"],
                rec["date_of_birth"],
                rec.get("nationality"),
                rec.get("photo_path_or_reference"),
                rec.get("photo_embedding"),
                rec.get("notes"),
                rec.get("is_active", 1),
            ),
        )
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    return inserted_count


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database schema and seed synthetic data."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        # Create blacklist table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_number TEXT NOT NULL UNIQUE,
                full_name TEXT,
                nationality TEXT,
                date_of_birth TEXT,
                reason TEXT NOT NULL,
                severity TEXT NOT NULL CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # Create index on document_number for efficient searching
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_blacklist_doc_num
            ON blacklist(document_number);
            """
        )

        # Create identity_embeddings table for duplicate detection
        # Stores ArcFace embeddings as JSON float arrays — no images, no pickles.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS identity_embeddings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                document_number TEXT    NOT NULL UNIQUE,
                full_name       TEXT,
                embedding       TEXT    NOT NULL,
                is_active       INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_emb_doc_num
            ON identity_embeddings(document_number);
            """
        )
        # Stores only canonical report metadata and cryptographic hashes, never PII or images.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_audits (
                screening_id TEXT PRIMARY KEY, report_json TEXT NOT NULL,
                report_hash TEXT NOT NULL, document_hash TEXT NOT NULL,
                transaction_hash TEXT, block_number INTEGER, audit_status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

        # Stores screening case summaries for officer review
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screening_id TEXT NOT NULL UNIQUE,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                main_reason TEXT,
                status TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'PENDING',
                extracted_identity TEXT,
                detected_issues TEXT,
                document_integrity_status TEXT,
                face_match_status TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cases_screening_id
            ON screening_cases(screening_id);
            """
        )

        # Trusted Identity Registry store
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trusted_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registry_id TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                document_number TEXT NOT NULL,
                document_type TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                nationality TEXT,
                photo_path_or_reference TEXT,
                photo_embedding TEXT,
                notes TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trusted_doc_num
            ON trusted_identities(document_number);
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trusted_reg_id
            ON trusted_identities(registry_id);
            """
        )
        conn.commit()

        # Seed synthetic records idempotently
        seed_blacklist_data(conn)
        seed_trusted_registry(conn)
    finally:
        conn.close()
