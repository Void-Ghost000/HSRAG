# HSRAG Core Package

`src/hsrag/` contains the reusable core primitives being extracted from the HSRAG LAW benchmark line.

Current status:

- Research / benchmark implementation
- Not production-ready
- Not legal advice
- Runnable benchmark scripts still live under `examples/hsrag_law/`
- This package is gradually extracted from RQ1–RQ6 without changing benchmark behavior

The goal of this directory is to make the core HSRAG mechanics readable, importable, and testable.

---

## What HSRAG is in this package

HSRAG is treated here as a **boundary-first retrieval governance layer**.

It does not replace BM25, TF-IDF, vector search, or hybrid retrieval.

Instead, it provides a small set of primitives for:

1. Typed legal scope detection
2. Salted domain hash routing
3. Conservative route gating
4. Audit-ready evidence assembly
5. Deterministic hash-chain verification

In the LAW benchmark line, these primitives are used to reduce:

- wrong-corpus retrieval
- wrong-jurisdiction escape
- no-evidence false allow
- ambiguous-query false allow
- cross-turn context contamination

---

## Reading order

For a first pass, read the modules in this order:

| Order | Module | Purpose |
|---:|---|---|
| 1 | `types.py` | Shared dataclasses and contracts |
| 2 | `hashing.py` | Deterministic `sha256:` helpers |
| 3 | `audit_chain.py` | Append-only audit-chain helpers |
| 4 | `hash_router.py` | Salted CTHC domain hash routing |
| 5 | `cthc.py` | Stable legal route-opener detection |
| 6 | `guard.py` | Conservative route decision layer |
| 7 | `evidence_assembler.py` | Audit-ready evidence pack assembly |

This core should be readable in about 30 minutes.

---

## Module map

### `types.py`

Defines shared contracts used across the package:

- `Chunk`
- `CTHCCode`
- `CTHCRoute`
- `RetrievalResult`
- `AuditEvent`
- `GateDecision`

Important design choice:

`corpus` and `jurisdiction` are kept as strings, not hard enums.

This is intentional because the RQ1–RQ6 benchmark line uses extensible legal identifiers such as:

- `EU_AI_ACT`
- `EU_DMA`
- `EU_GDPR`
- `US_COPPA`
- `US_CDA230`
- `US_FTC_ACT5`
- `US_CCPA`
- `US-CA`

---

### `hashing.py`

Provides deterministic hash helpers:

- `sha256_text`
- `sha256_bytes`
- `hash_json`
- `compute_source_hash`
- `compute_evidence_hash`
- `compute_audit_row_hash`

All public hashes use the `sha256:` prefix to match the benchmark artifacts.

---

### `audit_chain.py`

Implements a minimal append-only audit chain:

```text
GENESIS -> event_0_hash -> event_1_hash -> ... -> event_n_hash
```

Used by the benchmark family to preserve replayable evidence of:

- configuration
- routing decisions
- retrieval outputs
- final summaries

Tampering with event payloads or previous-hash linkage should fail verification.

---

### `hash_router.py`

Implements salted CTHC domain hash routing.

Core idea:

```text
CTHCCode(domain, source_type, jurisdiction, corpus_id)
        -> salted_domain_hash
        -> bounded retrieval bucket
```

This aligns with RQ5.5 salted-domain routing semantics.

Example:

```python
from hsrag.hash_router import route_key_for_corpus

domain_hash = route_key_for_corpus(corpus_id="EU_AI_ACT")
```

The salt used in the public benchmark branch is:

```text
HSRAG_LAW_RQ5_5_PUBLIC_REPRODUCIBLE_SALT_v1
```

---

### `cthc.py`

Detects stable legal route openers from query text.

Examples of stable openers:

- `EU AI Act`
- `Digital Markets Act`
- `COPPA`
- `CDA Section 230`
- `47 U.S.C. 230`
- `FTC Act Section 5`
- `15 U.S.C. 45`
- `CCPA`

Important rule:

Generic legal words alone should not open a route.

For example, this should not route directly:

```text
What does the platform law say about online services?
```

It should be treated as ambiguous or unsupported until a stable legal identifier is present.

---

### `guard.py`

Turns CTHC detection into conservative retrieval decisions.

Decision order:

```text
conflict -> unsupported -> ambiguous -> routable -> no evidence
```

The guard does not read benchmark answer labels.

It only uses:

- query text
- detected stable route openers
- available salted domain hashes

Possible result statuses:

- `HIT`
- `NO_EVIDENCE`
- `AMBIGUOUS`
- `ROUTE_CONFLICT`

This aligns with the RQ5.5 and RQ6 principle:

> Do not silently return wrong-domain content.

---

### `evidence_assembler.py`

Builds audit-ready evidence packs.

A retrieved chunk becomes an `Evidence` item containing:

- `chunk_id`
- `corpus`
- `jurisdiction`
- `unit`
- `text_hash`
- `source_hash`
- `evidence_hash`

Even `NO_EVIDENCE`, `AMBIGUOUS`, or `ROUTE_CONFLICT` outcomes can produce an audit hash.

This is important because failed or blocked retrieval attempts are still part of the benchmark evidence trail.

---

## Relationship to RQ1–RQ6

This package is being extracted from the HSRAG LAW research benchmark line.

| RQ | What it tested | Relevant core modules |
|---|---|---|
| RQ1 | Source integrity / source hash / real corpus gate | `hashing.py`, `audit_chain.py` |
| RQ2.2 | Real EU law + BM25/TF-IDF baselines + MC mutations | `types.py`, `hashing.py` |
| RQ3 FIX2 | EU × US legal collision + jurisdiction normalization | `types.py`, `guard.py` |
| RQ4.1 | Official/public source fetch and rebuild | `hashing.py`, `evidence_assembler.py` |
| RQ5.5 | CTHC typed salted-domain routing robustness | `cthc.py`, `hash_router.py`, `guard.py` |
| RQ6 | Multi-retrieval conversational legal collision benchmark | `cthc.py`, `guard.py`, `evidence_assembler.py` |

The runnable benchmark scripts remain under:

```text
examples/hsrag_law/
```

The purpose of `src/hsrag/` is to expose the reusable core logic behind those experiments.

---

## Current tests

The current minimal tests cover:

```text
tests/test_audit_chain.py
tests/test_hash_router.py
tests/test_cthc.py
tests/test_guard.py
tests/test_evidence_assembler.py
```

Run all tests from repository root:

```bash
python -m pytest tests
```

Expected result:

```text
all tests passed
```

---

## Current limitations

This package is intentionally minimal.

Not included yet:

- full BM25 / TF-IDF extraction from RQ6
- full RQ6 conversational benchmark refactor into package imports
- live official-source fetcher from RQ4
- production storage backends
- vector retrieval backends
- multi-tenant access-control policy
- legal answer synthesis

Those pieces remain in the benchmark scripts or roadmap.

---

## Claim boundary

This package does not claim:

- production readiness
- legal advice
- universal retrieval superiority
- replacement of RAG
- replacement of BM25 / vector / hybrid retrieval

The current claim is narrower:

> HSRAG provides boundary-first retrieval governance primitives that can support auditable, source-bounded retrieval experiments in high-risk domains.

For runnable evidence, see:

```text
examples/hsrag_law/
```