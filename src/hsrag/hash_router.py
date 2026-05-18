"""
HSRAG salted hash router.

QSVCS scope:
- I / Intent:
  Provide deterministic salted domain hashes for CTHC legal routing.
- V / Validation:
  Same CTHC code + same salt must produce the same hash.
  Different corpus / jurisdiction / salt must produce a different hash.
- O / Operation:
  Convert corpus_id + jurisdiction into a typed CTHCCode, then hash it.
- P / Postcondition:
  HSRAG can use domain_hash as a bounded retrieval bucket key.
- F / Feedback:
  This module is aligned with RQ5.5 salted-domain routing semantics.
"""

from __future__ import annotations

from .hashing import hash_json
from .types import CTHCCode


BENCHMARK_SALT = "HSRAG_LAW_RQ5_5_PUBLIC_REPRODUCIBLE_SALT_v1"

DEFAULT_DOMAIN = "LEGAL"
DEFAULT_SOURCE_TYPE = "PUBLIC_LEGAL_TEXT"
DEFAULT_TOPIC = "GENERAL"


CORPUS_JURISDICTION_DEFAULTS: dict[str, str] = {
    "EU_AI_ACT": "EU",
    "EU_DMA": "EU",
    "EU_GDPR": "EU",
    "US_COPPA": "US",
    "US_CDA230": "US",
    "US_FTC_ACT5": "US",
    "US_CCPA": "US-CA",
}


def canonical_jurisdiction(corpus_id: str, jurisdiction: str | None = None) -> str:
    """Return a stable jurisdiction for a corpus.

    RQ3/RQ6 require flexible jurisdiction strings because `US-CA` is a valid
    subjurisdiction while still being compatible with broader `US` checks.
    """

    if jurisdiction:
        return jurisdiction

    return CORPUS_JURISDICTION_DEFAULTS.get(corpus_id, "UNKNOWN")


def default_cthc_code(
    *,
    corpus_id: str,
    jurisdiction: str | None = None,
    topic: str = DEFAULT_TOPIC,
) -> CTHCCode:
    """Build the default legal CTHC address for a corpus."""

    return CTHCCode(
        domain=DEFAULT_DOMAIN,
        source_type=DEFAULT_SOURCE_TYPE,
        jurisdiction=canonical_jurisdiction(corpus_id, jurisdiction),
        corpus_id=corpus_id,
        topic=topic,
    )


def salted_domain_hash(
    code: CTHCCode,
    *,
    salt: str = BENCHMARK_SALT,
) -> str:
    """Compute the salted domain hash for a CTHC address.

    The hash is intentionally based on the retrieval boundary fields:

    - salt
    - domain
    - source_type
    - jurisdiction
    - corpus_id

    Topic is not included by default because RQ5.5 used domain buckets at
    corpus/jurisdiction scope.
    """

    return hash_json(
        {
            "salt": salt,
            "domain": code.domain,
            "source_type": code.source_type,
            "jurisdiction": code.jurisdiction,
            "corpus_id": code.corpus_id,
        }
    )


def route_key_for_corpus(
    *,
    corpus_id: str,
    jurisdiction: str | None = None,
    salt: str = BENCHMARK_SALT,
) -> str:
    """Return the salted retrieval bucket key for a corpus."""

    code = default_cthc_code(corpus_id=corpus_id, jurisdiction=jurisdiction)
    return salted_domain_hash(code, salt=salt)