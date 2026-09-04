"""Duplicate identity detection service for SIH26188.

Detects when a highly similar face (ArcFace embedding) appears under a
DIFFERENT document number in the SQLite identity_embeddings table.

Design principles:
- Uses cosine similarity of L2-normalised ArcFace embeddings.
- Embeddings stored as JSON float arrays — no pickle, no binary blobs.
- No images, no selfies, no portraits stored or logged.
- Embeddings are never returned to the frontend or serialised into API responses.
- Same document number is always treated as a PASS (re-scan of same identity).

Thresholds (conservative MVP values — screening aid, not definitive proof):
    similarity >= 90  →  FAIL    (highly similar face under different document)
    similarity >= 80  →  WARNING (moderately similar face under different document)
    similarity <  80  →  PASS    (no duplicate signal)

Return format:
    {
        "status":           "PASS" | "WARNING" | "FAIL" | "NOT_AVAILABLE",
        "similar_identity": None | {"document_number": str, "full_name": str|None, "similarity": float},
        "reason":           str
    }
"""

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
FAIL_THRESHOLD = 90.0       # similarity >= 90  → FAIL
WARNING_THRESHOLD = 80.0    # similarity >= 80  → WARNING; below → PASS

# ---------------------------------------------------------------------------
# Internal cosine similarity (no numpy dependency — operates on plain lists)
# ---------------------------------------------------------------------------

def _dot(a: List[float], b: List[float]) -> float:
    """Compute dot product of two equal-length Python float lists."""
    return sum(x * y for x, y in zip(a, b))


def _norm(a: List[float]) -> float:
    """Compute L2 norm of a Python float list."""
    return math.sqrt(sum(x * x for x in a))


def _cosine_similarity_lists(a: List[float], b: List[float]) -> float:
    """Cosine similarity in [-1, 1] for two plain Python float lists."""
    if len(a) != len(b):
        return 0.0
    n1 = _norm(a)
    n2 = _norm(b)
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return _dot(a, b) / (n1 * n2)


def _cosine_to_percent(cosine: float) -> float:
    """Map cosine similarity [-1, 1] to 0–100 percentage (mirrors face_matcher.py)."""
    return round(min(100.0, max(0.0, (cosine + 1.0) / 2.0 * 100.0)), 1)


def _status_from_similarity(similarity: float) -> str:
    """Map 0–100 similarity to PASS/WARNING/FAIL."""
    if similarity >= FAIL_THRESHOLD:
        return "FAIL"
    if similarity >= WARNING_THRESHOLD:
        return "WARNING"
    return "PASS"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_connection(db_path: Optional[str] = None):
    """Return a live SQLite connection, re-using database/session logic."""
    from app.database.session import get_db_connection
    return get_db_connection(db_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_duplicate_identity(
    document_number: Optional[str],
    full_name: Optional[str],
    embedding: Optional[List[float]],
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare the current selfie embedding against all stored active identities.

    Rows whose ``document_number`` matches the current ``document_number`` are
    explicitly excluded — re-scanning the same document is always a PASS.

    Parameters
    ----------
    document_number : str or None
        The extracted document number for the current subject.
    full_name : str or None
        Display name of the current subject (for logging context only).
    embedding : list[float] or None
        L2-normalised 512-d ArcFace embedding from ``extract_selfie_embedding()``.
    db_path : str or None
        Optional override for the SQLite database path (used in tests).

    Returns
    -------
    dict
        ``{"status", "similar_identity", "reason"}``

    Notes
    -----
    This function is a **screening aid** only.  Cosine similarity of face
    embeddings is probabilistic and not definitive biometric proof of identity.
    All FAIL/WARNING results must be reviewed by a trained human officer.
    """
    # Guard: missing inputs → NOT_AVAILABLE
    if document_number is None:
        return {
            "status": "NOT_AVAILABLE",
            "similar_identity": None,
            "reason": "Document number unavailable; duplicate identity check skipped",
        }
    if embedding is None:
        return {
            "status": "NOT_AVAILABLE",
            "similar_identity": None,
            "reason": "Face embedding unavailable; duplicate identity check skipped",
        }

    # Normalise document number for consistent comparison
    current_doc = document_number.strip().upper()

    try:
        conn = _get_connection(db_path)
    except Exception as exc:
        logger.warning("duplicate_identity_checker: DB connection failed — %s", exc)
        return {
            "status": "NOT_AVAILABLE",
            "similar_identity": None,
            "reason": "Database unavailable; duplicate identity check skipped",
        }

    try:
        cursor = conn.cursor()
        # Fetch all active embeddings that belong to OTHER document numbers
        cursor.execute(
            """
            SELECT document_number, full_name, embedding
            FROM identity_embeddings
            WHERE is_active = 1
              AND UPPER(TRIM(document_number)) != ?
            """,
            (current_doc,),
        )
        rows = cursor.fetchall()
    except Exception as exc:
        logger.warning("duplicate_identity_checker: query failed — %s", exc)
        conn.close()
        return {
            "status": "NOT_AVAILABLE",
            "similar_identity": None,
            "reason": "Database query failed; duplicate identity check skipped",
        }
    finally:
        conn.close()

    if not rows:
        # No other identities stored yet → clean pass
        return {
            "status": "PASS",
            "similar_identity": None,
            "reason": "No previously stored identities to compare against",
        }

    # Find the most similar stored embedding
    best_similarity: float = -1.0
    best_row = None

    for row in rows:
        stored_doc = row["document_number"]
        stored_name = row["full_name"]
        emb_json = row["embedding"]

        try:
            stored_emb: List[float] = json.loads(emb_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "duplicate_identity_checker: malformed embedding for doc=%s — skipped",
                stored_doc,
            )
            continue

        cosine = _cosine_similarity_lists(embedding, stored_emb)
        similarity = _cosine_to_percent(cosine)

        if similarity > best_similarity:
            best_similarity = similarity
            best_row = {"document_number": stored_doc, "full_name": stored_name}

    if best_row is None:
        # All stored embeddings were malformed
        return {
            "status": "PASS",
            "similar_identity": None,
            "reason": "No valid stored embeddings found for comparison",
        }

    status = _status_from_similarity(best_similarity)
    similar_identity = {
        "document_number": best_row["document_number"],
        "full_name": best_row["full_name"],
        "similarity": best_similarity,
    }

    if status == "FAIL":
        reason = (
            f"Highly similar face detected under a different identity document "
            f"({best_row['document_number']}, {best_similarity:.1f}% similarity)"
        )
    elif status == "WARNING":
        reason = (
            f"Moderately similar face found under another document "
            f"({best_row['document_number']}, {best_similarity:.1f}% similarity)"
        )
    else:
        reason = "No highly similar face found under another identity document"
        similar_identity = None  # type: ignore[assignment]

    return {
        "status": status,
        "similar_identity": similar_identity,
        "reason": reason,
    }


def store_embedding(
    document_number: Optional[str],
    full_name: Optional[str],
    embedding: Optional[List[float]],
    db_path: Optional[str] = None,
) -> bool:
    """Upsert the face embedding for a given document number.

    Uses ``INSERT OR REPLACE`` to avoid duplicate rows for repeated scans of
    the same document.  Sets ``updated_at`` on every write.

    Parameters
    ----------
    document_number : str or None
        The document number to associate with this embedding.
    full_name : str or None
        Display name (stored for audit reference only).
    embedding : list[float] or None
        L2-normalised ArcFace embedding to store as JSON text.
    db_path : str or None
        Optional database path override (used in tests).

    Returns
    -------
    bool
        ``True`` if the upsert succeeded, ``False`` on any failure.

    Notes
    -----
    - Embeddings are stored as JSON float arrays only (no images, no pickles).
    - Embedding values are never logged.
    """
    if document_number is None or embedding is None:
        return False

    current_doc = document_number.strip().upper()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        emb_json = json.dumps(embedding)
    except (TypeError, ValueError) as exc:
        logger.warning("store_embedding: cannot serialise embedding — %s", exc)
        return False

    try:
        conn = _get_connection(db_path)
    except Exception as exc:
        logger.warning("store_embedding: DB connection failed — %s", exc)
        return False

    try:
        conn.execute(
            """
            INSERT INTO identity_embeddings
                (document_number, full_name, embedding, is_active, updated_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(document_number) DO UPDATE SET
                full_name  = excluded.full_name,
                embedding  = excluded.embedding,
                is_active  = 1,
                updated_at = excluded.updated_at
            """,
            (current_doc, full_name, emb_json, now_iso),
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.warning("store_embedding: upsert failed — %s", exc)
        return False
    finally:
        conn.close()
