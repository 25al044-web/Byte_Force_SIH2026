"""Database connection and session utilities for SQLite."""
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = os.getenv("DATABASE_URL", str(BASE_DIR / "screening.db"))


def get_db_connection() -> sqlite3.Connection:
    """Create and return a new SQLite database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the SQLite database schema if needed."""
    conn = get_db_connection()
    try:
        # Schema tables will be defined here as models are introduced
        pass
    finally:
        conn.close()
