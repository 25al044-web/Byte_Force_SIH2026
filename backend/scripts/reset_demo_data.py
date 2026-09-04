"""Reset demo scan history and identity embeddings.

Clears the `identity_embeddings` table to allow repeated demo scans of
duplicate identity detection scenarios (e.g. DEMO-A then DEMO-B).
Preserves all seed blacklist records.
"""

import os
import sqlite3
import sys
from pathlib import Path

# Resolve base paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DB_PATH = os.getenv("DATABASE_URL", str(PROJECT_ROOT / "screening.db"))


def reset_demo_data():
    print(f"Connecting to SQLite database: {DB_PATH}")
    if not Path(DB_PATH).exists():
        print(f"Database does not exist at {DB_PATH}. Nothing to reset.")
        return 0

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # Count existing embeddings
        cursor.execute("SELECT COUNT(*) FROM identity_embeddings;")
        count = cursor.fetchone()[0]
        print(f"Current stored demo identity embeddings: {count}")

        cursor.execute("DELETE FROM identity_embeddings;")
        conn.commit()
        print(f"Successfully cleared {count} identity embedding record(s).")

        # Verify blacklist remains intact
        cursor.execute("SELECT COUNT(*) FROM blacklist;")
        bl_count = cursor.fetchone()[0]
        print(f"Blacklist seed records intact: {bl_count} record(s).")
        return 0
    except Exception as exc:
        print(f"Error resetting demo database: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(reset_demo_data())
