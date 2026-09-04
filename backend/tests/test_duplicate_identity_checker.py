"""Tests for duplicate_identity_checker.py — SIH26188.

All tests use an isolated in-memory SQLite database (":memory:") so they are
completely independent from the production screening.db.  No InsightFace models,
no network calls, no filesystem writes.

16 test scenarios:
 1.  Empty database → PASS
 2.  Same face + same document → PASS  (same-document rule)
 3.  Same face + different document → FAIL
 4.  Moderate similarity + different document → WARNING
 5.  Low similarity → PASS
 6.  No embedding (None) → NOT_AVAILABLE
 7.  No document number (None) → NOT_AVAILABLE
 8.  Embedding stored correctly (verify DB row)
 9.  Same document upserts (no duplicate rows)
10.  Repeated upserts produce exactly one row per document
11.  Inactive identity (is_active=0) is ignored
12.  Database failure (bad path) → NOT_AVAILABLE
13.  Raw embedding NOT returned to frontend (absent from DuplicateIdentityCheckResult)
14.  Duplicate FAIL feeds risk engine
15.  Duplicate FAIL produces risk >= 75 (override applied)
16.  Similarity clamped safely to 0–100
"""

import json
import math
import sqlite3
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from app.database.session import init_db


# ---------------------------------------------------------------------------
# Helpers — in-memory database fixtures
# ---------------------------------------------------------------------------

def _make_in_memory_db() -> sqlite3.Connection:
    """Create a fresh in-memory SQLite database with the full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
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
        CREATE INDEX IF NOT EXISTS idx_emb_doc_num
            ON identity_embeddings(document_number);
        """
    )
    return conn


def _unit_emb(dim: int = 512, value: float = 1.0) -> List[float]:
    """Return a normalised embedding with the first element set to `value`."""
    emb = [0.0] * dim
    emb[0] = value
    norm = math.sqrt(sum(x * x for x in emb))
    return [x / norm for x in emb]


def _emb_with_cosine(target_cosine: float, dim: int = 512) -> List[float]:
    """Return a unit embedding whose cosine similarity to _unit_emb() == target_cosine."""
    emb = [0.0] * dim
    emb[0] = float(target_cosine)
    remainder = 1.0 - target_cosine ** 2
    if remainder > 0:
        emb[1] = float(remainder ** 0.5)
    norm = math.sqrt(sum(x * x for x in emb))
    if norm == 0:
        return emb
    return [x / norm for x in emb]


def _cosine_to_percent(cosine: float) -> float:
    return round(min(100.0, max(0.0, (cosine + 1.0) / 2.0 * 100.0)), 1)


# Path to patch so tests use an injected in-memory connection
GET_CONN = "app.services.duplicate_identity_checker._get_connection"


class _NoCloseConn:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def close(self):
        pass

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        return self._conn.commit()

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _make_conn_factory(conn: sqlite3.Connection):
    """Return a factory that always yields the given connection (no close side-effects)."""
    proxy = _NoCloseConn(conn)
    return lambda db_path=None: proxy


# ---------------------------------------------------------------------------
# Scenario 1: Empty database → PASS
# ---------------------------------------------------------------------------

class TestEmptyDatabase:
    def test_empty_db_returns_pass(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity
        conn = _make_in_memory_db()
        with patch(GET_CONN, side_effect=_make_conn_factory(conn)):
            result = check_duplicate_identity("DOC-001", "TEST PERSON", _unit_emb())
        assert result["status"] == "PASS"
        assert result["similar_identity"] is None


# ---------------------------------------------------------------------------
# Scenario 2: Same face + same document → PASS (same-document rule)
# ---------------------------------------------------------------------------

class TestSameFaceSameDocument:
    def test_same_document_always_pass(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb = _unit_emb()
        # Store the embedding under DOC-001
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-001", "TEST PERSON", emb)

        # Re-scan the same document → should always be PASS
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-001", "TEST PERSON", emb)
        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Scenario 3: Same face + different document → FAIL
# ---------------------------------------------------------------------------

class TestSameFaceDifferentDocument:
    def test_identical_face_different_doc_is_fail(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb = _unit_emb()
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-A", "PERSON A", emb)

        # Same embedding, different document
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-B", "PERSON B", emb)

        assert result["status"] == "FAIL"
        assert result["similar_identity"] is not None
        assert result["similar_identity"]["document_number"] == "DOC-A"
        assert result["similar_identity"]["similarity"] >= 90.0


# ---------------------------------------------------------------------------
# Scenario 4: Moderate similarity + different document → WARNING
# ---------------------------------------------------------------------------

class TestModerateSimilarityWarning:
    def test_moderate_similarity_different_doc_is_warning(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        # Store embedding A
        emb_a = _unit_emb()
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-A", "PERSON A", emb_a)

        # Build embedding B that has cosine similarity ≈ 0.60 to emb_a
        # _cosine_to_percent(0.60) = (0.60+1)/2*100 = 80.0 → WARNING
        emb_b = _emb_with_cosine(0.60)
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-B", "PERSON B", emb_b)

        assert result["status"] == "WARNING"
        assert result["similar_identity"] is not None
        assert 80.0 <= result["similar_identity"]["similarity"] < 90.0


# ---------------------------------------------------------------------------
# Scenario 5: Low similarity → PASS
# ---------------------------------------------------------------------------

class TestLowSimilarityPass:
    def test_low_similarity_different_doc_is_pass(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb_a = _unit_emb()
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-A", "PERSON A", emb_a)

        # cosine = -0.60 → percent = (-0.60+1)/2*100 = 20.0 → PASS
        emb_b = _emb_with_cosine(-0.60)
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-B", "PERSON B", emb_b)

        assert result["status"] == "PASS"
        assert result["similar_identity"] is None


# ---------------------------------------------------------------------------
# Scenario 6: No embedding (None) → NOT_AVAILABLE
# ---------------------------------------------------------------------------

class TestNoEmbeddingNotAvailable:
    def test_none_embedding_returns_not_available(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity
        result = check_duplicate_identity("DOC-001", "PERSON", None)
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similar_identity"] is None


# ---------------------------------------------------------------------------
# Scenario 7: No document number (None) → NOT_AVAILABLE
# ---------------------------------------------------------------------------

class TestNoDocumentNumberNotAvailable:
    def test_none_doc_number_returns_not_available(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity
        result = check_duplicate_identity(None, "PERSON", _unit_emb())
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similar_identity"] is None


# ---------------------------------------------------------------------------
# Scenario 8: Embedding stored correctly
# ---------------------------------------------------------------------------

class TestEmbeddingStoredCorrectly:
    def test_stored_embedding_is_json_float_array(self):
        from app.services.duplicate_identity_checker import store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb = _unit_emb()
        with patch(GET_CONN, side_effect=factory):
            success = store_embedding("DOC-STORE", "STORE PERSON", emb)

        assert success is True
        row = conn.execute(
            "SELECT embedding FROM identity_embeddings WHERE document_number = 'DOC-STORE'"
        ).fetchone()
        assert row is not None
        loaded = json.loads(row["embedding"])
        assert isinstance(loaded, list)
        assert len(loaded) == 512
        assert all(isinstance(v, float) for v in loaded)


# ---------------------------------------------------------------------------
# Scenario 9: Same document upserts cleanly (no duplicates)
# ---------------------------------------------------------------------------

class TestSameDocumentUpsert:
    def test_repeated_upsert_no_duplicate_rows(self):
        from app.services.duplicate_identity_checker import store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb1 = _unit_emb()
        emb2 = _emb_with_cosine(0.50)

        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-UPSERT", "UPSERT PERSON", emb1)
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-UPSERT", "UPSERT PERSON UPDATED", emb2)

        count = conn.execute(
            "SELECT COUNT(*) FROM identity_embeddings WHERE document_number = 'DOC-UPSERT'"
        ).fetchone()[0]
        assert count == 1

        # Latest embedding should be stored
        stored_json = conn.execute(
            "SELECT embedding FROM identity_embeddings WHERE document_number = 'DOC-UPSERT'"
        ).fetchone()["embedding"]
        stored = json.loads(stored_json)
        assert abs(stored[0] - emb2[0]) < 1e-6


# ---------------------------------------------------------------------------
# Scenario 10: Repeated upserts produce exactly one row per document
# ---------------------------------------------------------------------------

class TestNoDuplicateRows:
    def test_multiple_documents_have_correct_row_count(self):
        from app.services.duplicate_identity_checker import store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        for i in range(5):
            with patch(GET_CONN, side_effect=factory):
                store_embedding(f"DOC-{i:03d}", f"PERSON {i}", _unit_emb())

        # Insert each again (upsert)
        for i in range(5):
            with patch(GET_CONN, side_effect=factory):
                store_embedding(f"DOC-{i:03d}", f"PERSON {i} V2", _unit_emb())

        total = conn.execute(
            "SELECT COUNT(*) FROM identity_embeddings"
        ).fetchone()[0]
        assert total == 5


# ---------------------------------------------------------------------------
# Scenario 11: Inactive identity (is_active=0) is ignored
# ---------------------------------------------------------------------------

class TestInactiveIdentityIgnored:
    def test_inactive_row_not_matched(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb = _unit_emb()
        # Insert an inactive record manually (bypassing store_embedding which sets is_active=1)
        conn.execute(
            "INSERT INTO identity_embeddings (document_number, full_name, embedding, is_active) "
            "VALUES ('DOC-INACTIVE', 'INACTIVE PERSON', ?, 0)",
            (json.dumps(emb),),
        )
        conn.commit()

        # Checking same face against DOC-NEW should return PASS (inactive excluded)
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-NEW", "NEW PERSON", emb)

        assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Scenario 12: Database failure → NOT_AVAILABLE
# ---------------------------------------------------------------------------

class TestDatabaseFailureNotAvailable:
    def test_bad_db_path_returns_not_available(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity
        # Patch _get_connection to raise
        with patch(GET_CONN, side_effect=Exception("DB error")):
            result = check_duplicate_identity("DOC-001", "PERSON", _unit_emb())
        assert result["status"] == "NOT_AVAILABLE"
        assert result["similar_identity"] is None

    def test_store_embedding_bad_db_returns_false(self):
        from app.services.duplicate_identity_checker import store_embedding
        with patch(GET_CONN, side_effect=Exception("DB error")):
            success = store_embedding("DOC-001", "PERSON", _unit_emb())
        assert success is False


# ---------------------------------------------------------------------------
# Scenario 13: Raw embedding NOT returned to frontend
# ---------------------------------------------------------------------------

class TestEmbeddingNotExposedInModel:
    def test_duplicate_identity_check_result_has_no_embedding_field(self):
        from app.models.screening import DuplicateIdentityCheckResult, CheckStatus
        result = DuplicateIdentityCheckResult(
            status=CheckStatus.PASS,
            similar_identity=None,
            reason="test",
        )
        data = result.model_dump()
        assert "embedding" not in data
        assert "face_embedding" not in data

    def test_similar_identity_dict_has_no_embedding(self):
        from app.models.screening import DuplicateIdentityCheckResult, CheckStatus
        result = DuplicateIdentityCheckResult(
            status=CheckStatus.FAIL,
            similar_identity={
                "document_number": "DOC-X",
                "full_name": "PERSON X",
                "similarity": 94.6,
            },
            reason="Highly similar face detected",
        )
        data = result.model_dump()
        si = data["similar_identity"]
        assert "embedding" not in si
        assert "face_embedding" not in si


# ---------------------------------------------------------------------------
# Scenario 14: Duplicate FAIL feeds risk engine correctly
# ---------------------------------------------------------------------------

class TestDuplicateFailFeedsRiskEngine:
    def test_duplicate_fail_increases_risk(self):
        from app.models.screening import (
            ChecksContainer, CheckStatus, MRZCheckResult, ExpiryCheckResult,
            TamperCheckResult, FaceMatchCheckResult, DuplicateIdentityCheckResult,
            BlacklistCheckResult,
        )
        from app.services.risk_engine import calculate_risk

        checks = ChecksContainer(
            mrz=MRZCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            tamper=TamperCheckResult(status=CheckStatus.PASS, risk=0, reason="ok"),
            face_match=FaceMatchCheckResult(status=CheckStatus.PASS, similarity=95.0, reason="ok"),
            duplicate_identity=DuplicateIdentityCheckResult(
                status=CheckStatus.FAIL,
                similar_identity={"document_number": "DOC-X", "full_name": "X", "similarity": 94.0},
                reason="Highly similar face detected",
            ),
            blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
        )
        result = calculate_risk(checks)
        # duplicate FAIL = +45; override raises to ≥75
        assert result["score"] >= 45
        assert "Duplicate identity confirmed" in " ".join(result["explanations"])


# ---------------------------------------------------------------------------
# Scenario 15: Duplicate FAIL produces risk >= 75 (override applied)
# ---------------------------------------------------------------------------

class TestDuplicateFailRiskOverride:
    def test_duplicate_fail_minimum_risk_is_75(self):
        from app.models.screening import (
            ChecksContainer, CheckStatus, MRZCheckResult, ExpiryCheckResult,
            TamperCheckResult, FaceMatchCheckResult, DuplicateIdentityCheckResult,
            BlacklistCheckResult,
        )
        from app.services.risk_engine import calculate_risk

        checks = ChecksContainer(
            mrz=MRZCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            expiry=ExpiryCheckResult(status=CheckStatus.PASS, score=0, reason="ok"),
            tamper=TamperCheckResult(status=CheckStatus.PASS, risk=0, reason="ok"),
            face_match=FaceMatchCheckResult(status=CheckStatus.PASS, similarity=99.0, reason="ok"),
            duplicate_identity=DuplicateIdentityCheckResult(
                status=CheckStatus.FAIL,
                similar_identity={"document_number": "DOC-X", "full_name": "X", "similarity": 91.0},
                reason="Highly similar face detected",
            ),
            blacklist=BlacklistCheckResult(status=CheckStatus.PASS, reason="ok"),
        )
        result = calculate_risk(checks)
        assert result["score"] >= 75
        assert result["level"] == "HIGH"


# ---------------------------------------------------------------------------
# Scenario 16: Similarity clamped safely to 0–100
# ---------------------------------------------------------------------------

class TestSimilarityClampedSafely:
    def test_cosine_to_percent_clamps_extremes(self):
        from app.services.duplicate_identity_checker import _cosine_to_percent
        assert _cosine_to_percent(1.0) == 100.0
        assert _cosine_to_percent(-1.0) == 0.0
        assert _cosine_to_percent(2.0) == 100.0      # beyond max → clamped
        assert _cosine_to_percent(-2.0) == 0.0       # below min → clamped

    def test_stored_similarity_never_exceeds_100(self):
        from app.services.duplicate_identity_checker import check_duplicate_identity, store_embedding
        conn = _make_in_memory_db()
        factory = _make_conn_factory(conn)

        emb = _unit_emb()
        with patch(GET_CONN, side_effect=factory):
            store_embedding("DOC-A", "PERSON A", emb)

        # Identical embedding → should give 100.0, not exceed it
        with patch(GET_CONN, side_effect=factory):
            result = check_duplicate_identity("DOC-B", "PERSON B", emb)

        assert result["status"] == "FAIL"
        assert result["similar_identity"]["similarity"] <= 100.0
        assert result["similar_identity"]["similarity"] >= 0.0
