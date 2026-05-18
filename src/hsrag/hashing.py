"""
HSRAG hashing utilities.

QSVCS scope:
- I / Intent:
  Provide deterministic hashes for source text, evidence, config, rows,
  and audit-chain payloads.
- V / Validation:
  All public hashes use the `sha256:` prefix to match RQ1-RQ6 artifacts.
- O / Operation:
  Hash JSON using sorted keys for reproducibility.
- P / Postcondition:
  Same payload -> same hash. Different payload -> different hash.
- F / Feedback:
  Do not change hash format without updating all benchmark manifests.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_text(text: str) -> str:
    """Hash plain text with the HSRAG `sha256:` prefix."""

    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Hash bytes with the HSRAG `sha256:` prefix."""

    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_json(payload: Any) -> str:
    """Hash a JSON-serializable payload deterministically."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def compute_source_hash(text: str) -> str:
    """Compute a source hash for normalized legal text."""

    return sha256_text(text)


def compute_evidence_hash(
    *,
    chunk_id: str,
    corpus: str,
    jurisdiction: str,
    source_hash: str,
) -> str:
    """Compute an evidence hash from chunk identity and source hash."""

    return hash_json(
        {
            "chunk_id": chunk_id,
            "corpus": corpus,
            "jurisdiction": jurisdiction,
            "source_hash": source_hash,
        }
    )


def compute_audit_row_hash(row: dict) -> str:
    """Compute an audit hash for one benchmark result row.

    Existing `audit_row_hash` is excluded to avoid self-reference.
    """

    clean = dict(row)
    clean.pop("audit_row_hash", None)
    return hash_json(clean)