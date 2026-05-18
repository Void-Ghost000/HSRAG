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
- salted CTHC domain hash routing
"""

from .audit_chain import (
    GENESIS_HASH,
    audit_events_as_dicts,
    build_audit_chain,
    make_audit_event,
    verify_audit_chain,
)
from .hash_router import (
    BENCHMARK_SALT,
    canonical_jurisdiction,
    default_cthc_code,
    route_key_for_corpus,
    salted_domain_hash,
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
    # Shared types
    "AuditEvent",
    "Chunk",
    "CorpusId",
    "CTHCCode",
    "CTHCRoute",
    "GateDecision",
    "JurisdictionId",
    "RetrievalResult",
    # Audit chain
    "GENESIS_HASH",
    "audit_events_as_dicts",
    "build_audit_chain",
    "make_audit_event",
    "verify_audit_chain",
    # Hash router
    "BENCHMARK_SALT",
    "canonical_jurisdiction",
    "default_cthc_code",
    "route_key_for_corpus",
    "salted_domain_hash",
    # Hashing helpers
    "compute_audit_row_hash",
    "compute_evidence_hash",
    "compute_source_hash",
    "hash_json",
    "sha256_bytes",
    "sha256_text",
]