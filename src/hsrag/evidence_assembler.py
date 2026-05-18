"""
HSRAG evidence assembly.

QSVCS scope:
- I / Intent:
  Convert retrieved chunks into audit-ready evidence records.
- V / Validation:
  Every evidence record must carry source_hash and evidence_hash.
  NO_EVIDENCE / AMBIGUOUS / ROUTE_CONFLICT cases may have no chunks, but still
  produce an audit hash.
- O / Operation:
  chunk -> Evidence -> EvidencePack -> audit_hash.
- P / Postcondition:
  Evidence packs are deterministic and JSON-serializable.
- F / Feedback:
  This module supports RQ1-RQ6 artifact semantics without making legal-advice
  or production-readiness claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Optional, Tuple

from .hashing import compute_evidence_hash, hash_json, sha256_text
from .types import Chunk


@dataclass(frozen=True)
class Evidence:
    """A single audit-ready evidence item."""

    chunk_id: str
    corpus: str
    jurisdiction: str
    unit: str
    text_hash: str
    source_hash: str
    evidence_hash: str
    source_hash_backfilled: bool = False


@dataclass(frozen=True)
class EvidencePack:
    """Audit-ready evidence pack for one query turn.

    This is intentionally smaller than a full answer object. RQ scripts can
    attach additional benchmark fields such as pair_id, turn_id, mode, context
    policy, latency, and mutation labels.
    """

    query_hash: str
    result_status: str
    route_status: str
    route_reason: str
    evidence: Tuple[Evidence, ...]
    answer_hash: str
    audit_hash: str

    @property
    def is_complete(self) -> bool:
        """Return True if the audit linkage is structurally complete."""

        if not self.query_hash:
            return False

        if not self.result_status:
            return False

        if not self.audit_hash:
            return False

        for item in self.evidence:
            if not item.source_hash:
                return False
            if not item.evidence_hash:
                return False

        return True


def chunk_to_evidence(chunk: Chunk) -> Evidence:
    """Convert a normalized Chunk into an audit-ready Evidence item."""

    evidence_hash = compute_evidence_hash(
        chunk_id=chunk.chunk_id,
        corpus=chunk.corpus,
        jurisdiction=chunk.jurisdiction,
        source_hash=chunk.source_hash,
    )

    return Evidence(
        chunk_id=chunk.chunk_id,
        corpus=chunk.corpus,
        jurisdiction=chunk.jurisdiction,
        unit=chunk.unit,
        text_hash=sha256_text(chunk.text),
        source_hash=chunk.source_hash,
        evidence_hash=evidence_hash,
        source_hash_backfilled=chunk.source_hash_backfilled,
    )


def assemble_evidence(
    *,
    query: str,
    result_status: str,
    route_status: str,
    route_reason: str,
    chunks: Iterable[Chunk] = (),
    answer: str = "",
) -> EvidencePack:
    """Assemble an audit-ready evidence pack.

    The function is deterministic:
    same query + same route/result metadata + same chunks + same answer
    produces the same audit_hash.
    """

    evidence = tuple(chunk_to_evidence(chunk) for chunk in chunks)
    query_hash = sha256_text(query)
    answer_hash = sha256_text(answer)

    audit_payload = {
        "query_hash": query_hash,
        "result_status": result_status,
        "route_status": route_status,
        "route_reason": route_reason,
        "evidence_hashes": [item.evidence_hash for item in evidence],
        "source_hashes": [item.source_hash for item in evidence],
        "answer_hash": answer_hash,
    }

    return EvidencePack(
        query_hash=query_hash,
        result_status=result_status,
        route_status=route_status,
        route_reason=route_reason,
        evidence=evidence,
        answer_hash=answer_hash,
        audit_hash=hash_json(audit_payload),
    )


def evidence_pack_as_dict(pack: EvidencePack) -> dict:
    """Serialize an EvidencePack into a plain dictionary."""

    payload = asdict(pack)
    payload["is_complete"] = pack.is_complete
    return payload


def evidence_hashes(pack: EvidencePack) -> list[str]:
    """Return evidence hashes from a pack."""

    return [item.evidence_hash for item in pack.evidence]


def source_hashes(pack: EvidencePack) -> list[str]:
    """Return source hashes from a pack."""

    return [item.source_hash for item in pack.evidence]