"""Deterministic SHA-256 helpers for the screening audit boundary."""

import hashlib
import json
from typing import Any, Dict


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_report(report: Dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(report).encode("utf-8"))
