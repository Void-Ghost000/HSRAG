"""
HSRAG shared types.

QSVCS scope:
- I / Intent:
  Define stable contracts shared by CTHC routing, salted hash routing,
  guard decisions, evidence assembly, and RQ benchmark metrics.
- V / Validation:
  Keep corpus_id and jurisdiction as strings because RQ1-RQ6 use extensible
  legal corpora such as EU_AI_ACT, EU_DMA, US_CDA230, US_CCPA, and US-CA.
- O / Operation:
  Provide small dataclasses only. No retrieval, no benchmark logic here.
- P / Postcondition:
  Other modules can import these types without triggering side effects.
- F / Feedback:
  If RQ scripts add new statuses or fields, update this contract explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


CorpusId = str
JurisdictionId = str


@dataclass(frozen=True)
class Chunk:
    """A normalized legal evidence chunk.

    This matches the RQ6 normalized corpus contract:

    - chunk_id
    - corpus
    - jurisdiction
    - unit
    - text
    - source_hash
    - source_hash_backfilled
    """

    chunk_id: str
    corpus: CorpusId
    jurisdiction: JurisdictionId
    unit: str
    text: str
    source_hash: str
    source_hash_backfilled: bool = False


@dataclass(frozen=True)
class CTHCCode:
    """Typed CTHC legal address used by RQ5/RQ6 routing.

    Example path:

        LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL

    This is a typed address, not a semantic embedding.
    """

    domain: str
    source_type: str
    jurisdiction: JurisdictionId
    corpus_id: CorpusId
    topic: str = "GENERAL"

    def path(self) -> str:
        """Serialize the CTHC address into a stable dotted path."""

        return (
            f"{self.domain}."
            f"{self.source_type}."
            f"{self.jurisdiction}."
            f"{self.corpus_id}."
            f"{self.topic}"
        )


@dataclass(frozen=True)
class CTHCRoute:
    """Result of CTHC route classification.

    The route classifier must not read expected labels from benchmark cases.
    It may only use query text and available corpus/domain information.
    """

    status: str
    code: Optional[CTHCCode]
    domain_hash: Optional[str]
    confidence: str
    reason: str
    detected_corpus_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    """Minimal retrieval result shared by benchmark and package code."""

    result_status: str
    top_chunk: Optional[Chunk]
    route_status: str
    route_reason: str
    evidence_hash: str
    source_hash: str
    latency_ms: float


@dataclass(frozen=True)
class AuditEvent:
    """Append-only audit-chain event.

    The event hash is computed from:

    - index
    - event_type
    - payload
    - previous_hash
    """

    index: int
    event_type: str
    payload: dict
    previous_hash: str
    event_hash: str


@dataclass(frozen=True)
class GateDecision:
    """Conservative retrieval gate decision."""

    status: str
    reason: str
    route: Optional[CTHCRoute] = None