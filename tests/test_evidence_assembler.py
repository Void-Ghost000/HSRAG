"""
Tests for HSRAG evidence assembly.

These tests align with RQ1-RQ6:
- source_hash must be present for evidence
- evidence_hash must be deterministic
- no-evidence outcomes still produce an audit hash
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hsrag.evidence_assembler import (
    assemble_evidence,
    chunk_to_evidence,
    evidence_hashes,
    evidence_pack_as_dict,
    source_hashes,
)
from hsrag.hashing import sha256_text
from hsrag.types import Chunk


def make_chunk() -> Chunk:
    return Chunk(
        chunk_id="EU_AI_ACT_ART5_001",
        corpus="EU_AI_ACT",
        jurisdiction="EU",
        unit="Article 5",
        text="EU AI Act Article 5 concerns prohibited AI practices.",
        source_hash=sha256_text("official source text"),
        source_hash_backfilled=False,
    )


def test_chunk_to_evidence_has_source_and_evidence_hash() -> None:
    evidence = chunk_to_evidence(make_chunk())

    assert evidence.chunk_id == "EU_AI_ACT_ART5_001"
    assert evidence.corpus == "EU_AI_ACT"
    assert evidence.jurisdiction == "EU"
    assert evidence.source_hash.startswith("sha256:")
    assert evidence.evidence_hash.startswith("sha256:")
    assert evidence.text_hash.startswith("sha256:")


def test_assemble_evidence_pack_is_complete_for_hit() -> None:
    chunk = make_chunk()

    pack = assemble_evidence(
        query="Find EU AI Act Article 5.",
        result_status="HIT",
        route_status="HIT",
        route_reason="CTHC constrained retrieval to corpus=EU_AI_ACT.",
        chunks=[chunk],
        answer="Retrieved one bounded evidence chunk.",
    )

    assert pack.is_complete is True
    assert pack.result_status == "HIT"
    assert len(pack.evidence) == 1
    assert evidence_hashes(pack) == [pack.evidence[0].evidence_hash]
    assert source_hashes(pack) == [chunk.source_hash]


def test_assemble_evidence_pack_is_deterministic() -> None:
    chunk = make_chunk()

    pack1 = assemble_evidence(
        query="Find EU AI Act Article 5.",
        result_status="HIT",
        route_status="HIT",
        route_reason="CTHC constrained retrieval to corpus=EU_AI_ACT.",
        chunks=[chunk],
        answer="Retrieved one bounded evidence chunk.",
    )

    pack2 = assemble_evidence(
        query="Find EU AI Act Article 5.",
        result_status="HIT",
        route_status="HIT",
        route_reason="CTHC constrained retrieval to corpus=EU_AI_ACT.",
        chunks=[chunk],
        answer="Retrieved one bounded evidence chunk.",
    )

    assert pack1.audit_hash == pack2.audit_hash


def test_no_evidence_pack_still_has_audit_hash() -> None:
    pack = assemble_evidence(
        query="What does PIPEDA require?",
        result_status="NO_EVIDENCE",
        route_status="NO_EVIDENCE",
        route_reason="Unsupported legal topic outside local corpus.",
        chunks=[],
    )

    assert pack.is_complete is True
    assert pack.evidence == ()
    assert pack.audit_hash.startswith("sha256:")


def test_evidence_pack_as_dict_is_json_ready() -> None:
    pack = assemble_evidence(
        query="Find EU AI Act Article 5.",
        result_status="HIT",
        route_status="HIT",
        route_reason="CTHC constrained retrieval to corpus=EU_AI_ACT.",
        chunks=[make_chunk()],
    )

    payload = evidence_pack_as_dict(pack)

    assert payload["is_complete"] is True
    assert payload["result_status"] == "HIT"
    assert payload["evidence"][0]["corpus"] == "EU_AI_ACT"