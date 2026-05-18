"""
HSRAG core package.

Current status:
- Research / benchmark implementation.
- Runnable HSRAG LAW demos live under `examples/hsrag_law/`.
- `src/hsrag/` is the reusable core being extracted from RQ1-RQ6.

This package intentionally starts small:
- shared types
- deterministic hashing
- audit-chain helpers
"""

from .audit_chain import (
    GENESIS_HASH,
    audit_events_as_dicts,
    build_audit_chain,
    make_audit_event,
    verify_audit_chain,
)
from .hashing import (
    compute_audit_row_hash,
    compute_evidence_hash,
    compute_source_hash,
    hash_json,
    sha256_bytes,
    sha256_text,
)
from .types import (
    AuditEvent,
    Chunk,
    CorpusId,
    CTHCCode,
    CTHCRoute,
    GateDecision,
    JurisdictionId,
    RetrievalResult,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AuditEvent",
    "Chunk",
    "CorpusId",
    "CTHCCode",
    "CTHCRoute",
    "GateDecision",
    "JurisdictionId",
    "RetrievalResult",
    "GENESIS_HASH",
    "audit_events_as_dicts",
    "build_audit_chain",
    "make_audit_event",
    "verify_audit_chain",
    "compute_audit_row_hash",
    "compute_evidence_hash",
    "compute_source_hash",
    "hash_json",
    "sha256_bytes",
    "sha256_text",
]