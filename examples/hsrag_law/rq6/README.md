# HSRAG LAW RQ6 — Conversational Legal Collision Benchmark

RQ6 tests whether retrieval systems can resist **cross-jurisdiction context contamination** in multi-turn legal retrieval conversations.

This benchmark compares lexical baselines and HSRAG-style boundary-first retrieval under conversational context policies.

RQ6 focuses on cases where similar legal references may collide across jurisdictions, such as:

- EU AI Act Article 5
- U.S. FTC Act Section 5
- U.S. CDA Section 230
- EU DMA gatekeeper obligations
- U.S. COPPA children data rules
- EU GDPR Article 8, if available

---

## 1. Core Question

RQ6 asks:

> In a multi-turn legal retrieval conversation, can the retrieval system preserve corpus, jurisdiction, and evidence boundaries when the user switches between similar EU and U.S. legal concepts?

Example:

```text
Turn 1: Find EU AI Act Article 5 prohibited AI practices.
Turn 2: Now find U.S. FTC Act Section 5 on unfair or deceptive acts or practices.
```

A contaminated retrieval system may incorrectly carry over the EU context into the U.S. turn.

RQ6 measures whether different retrieval modes produce:

- wrong corpus retrieval
- wrong jurisdiction retrieval
- no-evidence false allow
- ambiguous false allow
- cross-turn contamination
- switch-turn contamination

---

## 2. What RQ6 Is Not

RQ6 does **not** claim that RAG is dead.

RQ6 does **not** claim that HSRAG replaces all retrieval methods.

RQ6 does **not** provide legal advice.

RQ6 does **not** evaluate legal reasoning correctness beyond retrieval evidence matching.

RQ6 evaluates HSRAG as a:

- boundary-first retrieval governance layer
- CTHC constrained retrieval layer
- audit layer before retrieval
- context contamination control layer

BM25 is treated as a strong lexical baseline, not as an enemy baseline.

---

## 3. Current Status

Current benchmark status:

```text
RQ6 version: v0.1.1
Run type: local smoke benchmark
MC: 3000
Rows: 108000
Demo mode: False
Corpus source: examples/hsrag_law/results/rq4_rebuilt_chunks.csv
Available corpora: EU_AI_ACT, EU_DMA, US_CDA230, US_COPPA, US_FTC_ACT5
```

HSRAG modes passed the mc=3000 smoke benchmark with:

```text
target_correct_rate: 1.000
hit_target_correct_rate: 1.000
wrong_corpus_collision_rate: 0.000
wrong_jurisdiction_escape_rate: 0.000
no_evidence_false_allow_rate: 0.000
ambiguous_false_allow_rate: 0.000
cross_turn_contamination_rate: 0.000
switch_turn_contamination_rate: 0.000
```

This is a **smoke benchmark result**, not a publication-grade final claim.

For detailed results, see:

```text
RQ6_SMOKE_REPORT.md
```

---

## 4. Required Corpus Format

RQ6 expects a normalized chunk CSV with at least:

```text
chunk_id, corpus or corpus_id, jurisdiction, unit or source_title, text, source_hash
```

The current runner supports both:

```text
corpus
corpus_id
```

The existing RQ4 rebuilt corpus uses:

```text
examples/hsrag_law/results/rq4_rebuilt_chunks.csv
```

Known supported fields from the current RQ4 rebuilt corpus include:

```text
chunk_id
corpus_id
jurisdiction
source_title
source_url
candidate_type
source_hash
normalized_text_sha256
chunk_index
chunk_hash
char_start
char_end
text
```

If `source_hash` is missing, the runner may backfill it with `sha256(text)`, but this is recorded in the run manifest.

If no `--chunks` file is provided, the runner may use a synthetic demo corpus.

Synthetic demo runs are smoke tests only and must not be reported as publication-grade results.

---

## 5. Retrieval Modes

RQ6 compares six retrieval modes:

```text
bm25_global
bm25_domain_hint
tfidf_global
hybrid_rrf_global
hsrag_cthc
hsrag_hybrid_subset
```

| Mode | Description |
|---|---|
| `bm25_global` | Global BM25 lexical retrieval over all chunks |
| `bm25_domain_hint` | BM25 with lightweight domain filtering when a stable corpus or jurisdiction hint is detected |
| `tfidf_global` | Global TF-IDF cosine retrieval |
| `hybrid_rrf_global` | Global BM25 + TF-IDF reciprocal rank fusion |
| `hsrag_cthc` | Boundary-first CTHC route, then BM25 within the constrained subset |
| `hsrag_hybrid_subset` | Boundary-first CTHC route, then BM25 + TF-IDF RRF within the constrained subset |

---

## 6. Context Policies

RQ6 compares three context policies:

```text
no_memory
naive_memory
bounded_cthc_memory
```

| Policy | Description |
|---|---|
| `no_memory` | Each turn is retrieved independently |
| `naive_memory` | Previous query is blindly prepended to the next query; intentionally unsafe baseline |
| `bounded_cthc_memory` | Only previous actual retrieval scope is carried forward; no answer-key labels are used |

Important rule:

```text
bounded_cthc_memory must only use previous actual retrieval results.
It must not use expected_corpus, expected_jurisdiction, or any answer key.
```

---

## 7. Query Pair Generator

RQ6 v0.1 includes these two-turn collision patterns:

```text
A. EU_AI_ACT Article 5 → US_FTC_ACT Section 5
B. US_FTC_ACT Section 5 → EU_AI_ACT Article 5
C. US_CDA230 platform liability → EU_DMA gatekeeper obligations
D. EU_DMA gatekeeper obligations → US_CDA230 platform liability
E. US_COPPA children data → EU_GDPR Article 8 or NO_EVIDENCE
F. Ambiguous Article 5 carryover test
```

These cases are designed to stress similar legal concepts, similar numbering, and EU / U.S. jurisdiction switching.

---

## 8. Mutation Layer

Each query pair is tested under controlled perturbations:

```text
none
polite_prefix
irrelevant_tail
punctuation_noise
typo_light
jurisdiction_reminder
legalese_prefix
distractor_warning
```

The CTHC scope detector includes a lightweight normalization layer for benchmark noise such as:

- punctuation noise
- light typo mutation
- spaced acronyms
- benchmark-generated distractor warning text

This normalization does not use expected labels or answer keys.

---

## 9. How to Run

### 9.1 Quick smoke test

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks examples\hsrag_law\results\rq4_rebuilt_chunks.csv --mc 30
```

Expected row count:

```text
30 MC trials × 6 retrieval modes × 3 context policies × 2 turns = 1080 rows
```

### 9.2 Standard smoke benchmark

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks examples\hsrag_law\results\rq4_rebuilt_chunks.csv --mc 3000
```

Expected row count:

```text
3000 MC trials × 6 retrieval modes × 3 context policies × 2 turns = 108000 rows
```

### 9.3 Formal run

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks path\to\real_law_chunks.csv --mc 20000
```

Formal runs should use a real legal corpus with complete source metadata.

---

## 10. Output Artifacts

Each run writes to:

```text
runs/rq6_conversational_collision_<timestamp>/
```

Required outputs:

```text
rq6_summary.json
rq6_run_manifest.json
rq6_failure_samples.csv
```

Additional outputs:

```text
rq6_full_results.csv
rq6_mode_comparison.md
rq6_claim_boundary.md
```

Do not delete:

```text
rq6_failure_samples.csv
rq6_run_manifest.json
rq6_full_results.csv
```

These files are required for replay, audit, and failure analysis.

---

## 11. Metrics

RQ6 summary metrics include:

```text
target_correct_rate
hit_target_correct_rate
wrong_corpus_collision_rate
wrong_jurisdiction_escape_rate
no_evidence_false_allow_rate
ambiguous_false_allow_rate
cross_turn_contamination_rate
switch_turn_contamination_rate
source_hash_present_rate
audit_chain_complete_rate
p95_latency_ms
```

| Metric | Meaning |
|---|---|
| `target_correct_rate` | Overall expected-status correctness |
| `hit_target_correct_rate` | Correctness on expected HIT cases only |
| `wrong_corpus_collision_rate` | Retrieved the wrong legal corpus when a HIT was expected |
| `wrong_jurisdiction_escape_rate` | Retrieved the wrong jurisdiction when a HIT was expected |
| `no_evidence_false_allow_rate` | Returned HIT when expected status was NO_EVIDENCE |
| `ambiguous_false_allow_rate` | Returned HIT when expected status was AMBIGUOUS |
| `cross_turn_contamination_rate` | Turn 2 reused Turn 1 corpus when it should switch |
| `switch_turn_contamination_rate` | Turn 2 reused Turn 1 jurisdiction when it should switch |
| `source_hash_present_rate` | HIT rows with source hash present |
| `audit_chain_complete_rate` | Rows with audit row hash present |
| `p95_latency_ms` | p95 retrieval latency |

---

## 12. RQ6 v0.1.1 Smoke Result

Local standard smoke run:

```text
MC: 3000
Rows: 108000
Demo mode: False
Corpus source: examples/hsrag_law/results/rq4_rebuilt_chunks.csv
Available corpora: EU_AI_ACT, EU_DMA, US_CDA230, US_COPPA, US_FTC_ACT5
Source hash present rate: 1.0
Audit chain complete rate: 1.0
```

Overall result across all modes and policies:

```text
target_correct_rate: 0.790962962962963
hit_target_correct_rate: 0.8769333333333333
wrong_corpus_collision_rate: 0.10255555555555555
wrong_jurisdiction_escape_rate: 0.09500925925925927
no_evidence_false_allow_rate: 0.05092592592592592
ambiguous_false_allow_rate: 0.05555555555555555
cross_turn_contamination_rate: 0.10706481481481482
switch_turn_contamination_rate: 0.12153703703703704
source_hash_present_rate: 1.0
audit_chain_complete_rate: 1.0
p95_latency_ms: 10.5725
```

The overall result includes both baseline and HSRAG modes.

The main RQ6 comparison should be read by:

```text
mode × context_policy
```

---

## 13. HSRAG Smoke Result

RQ6 v0.1.1 `mc=3000` HSRAG result:

| Mode | Context policy | target | hit | wrong corpus | wrong jurisdiction | no-evidence false allow | ambiguous false allow | cross-turn | switch-turn | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `hsrag_cthc` | `bounded_cthc_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.050 ms |
| `hsrag_cthc` | `naive_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.156 ms |
| `hsrag_cthc` | `no_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.355 ms |
| `hsrag_hybrid_subset` | `bounded_cthc_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 6.688 ms |
| `hsrag_hybrid_subset` | `naive_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 6.609 ms |
| `hsrag_hybrid_subset` | `no_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 6.569 ms |

Additional check:

```text
HSRAG failure sample count: 0
```

Interpretation:

```text
In this mc=3000 smoke benchmark, HSRAG CTHC and HSRAG Hybrid Subset produced no wrong-corpus retrieval, no wrong-jurisdiction retrieval, no false allow on NO_EVIDENCE or AMBIGUOUS cases, and no cross-turn contamination.
```

This is a smoke benchmark result, not a publication-grade final claim.

---

## 14. Baseline Contamination Signal

Selected baseline results from the same `mc=3000` run:

| Mode | Context policy | target | wrong corpus | wrong jurisdiction | cross-turn | switch-turn | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|
| `bm25_domain_hint` | `no_memory` | 0.917 | 0.000 | 0.000 | 0.000 | 0.000 | 3.347 ms |
| `bm25_domain_hint` | `naive_memory` | 0.667 | 0.167 | 0.167 | 0.250 | 0.250 | 6.304 ms |
| `bm25_global` | `no_memory` | 0.770 | 0.063 | 0.052 | 0.083 | 0.104 | 6.689 ms |
| `bm25_global` | `naive_memory` | 0.625 | 0.209 | 0.198 | 0.250 | 0.250 | 7.572 ms |
| `hybrid_rrf_global` | `naive_memory` | 0.625 | 0.209 | 0.198 | 0.250 | 0.250 | 36.245 ms |
| `tfidf_global` | `naive_memory` | 0.573 | 0.260 | 0.229 | 0.229 | 0.250 | 27.863 ms |

Interpretation:

```text
The naive memory policy increases cross-turn contamination for baseline retrieval modes.
BM25 domain hint is a strong lexical baseline under no_memory, but naive memory can still pollute retrieval context.
```

This supports the RQ6 hypothesis that conversational legal retrieval requires explicit context boundaries.

---

## 15. Limitation: Atomic Legal Retrieval First

RQ6 v0.1 evaluates atomic or two-turn legal retrieval tasks.

The current HSRAG CTHC router is intentionally boundary-first and single-scope oriented.

A single retrieval call should target one legal corpus, jurisdiction, and legal unit whenever possible.

For multi-statute or comparative legal questions, such as comparing EU AI Act Article 5 with U.S. FTC Act Section 5, the query should first be decomposed into separate atomic retrieval tasks.

Recommended flow:

```text
User asks multi-law question
  ↓
Query decomposition layer
  ↓
Atomic retrieval task 1
Atomic retrieval task 2
Atomic retrieval task 3
  ↓
Each task receives its own:
- route_status
- source_hash
- evidence_hash
- audit_row_hash
  ↓
Answer synthesis / legal comparison layer
```

Multi-law comparison should happen after retrieval, not inside the retrieval boundary itself.

RQ6 v0.1 does not claim to solve unrestricted multi-law batch retrieval in a single query.

This is a governance choice, not merely a technical limitation.

---

## 16. Claim Boundary

Allowed claim:

```text
RQ6 v0.1.1 demonstrates that boundary-first CTHC retrieval can reduce cross-jurisdiction context contamination in a controlled multi-turn legal retrieval benchmark.
```

Allowed claim:

```text
Naive conversational memory can contaminate baseline retrieval when the user switches between similar legal concepts across jurisdictions.
```

Allowed claim:

```text
BM25 remains a strong lexical baseline, especially when domain hints are available.
```

Disallowed claim:

```text
HSRAG is production-ready.
```

Disallowed claim:

```text
HSRAG replaces all RAG systems.
```

Disallowed claim:

```text
RQ6 provides legal advice.
```

Disallowed claim:

```text
A smoke benchmark is publication-grade evidence.
```

---

## 17. Recommended Next Steps

Suggested next steps:

```text
1. Keep RQ6 v0.1.1 as the mc3000 smoke-pass baseline.
2. Run mc=20000 with the same corpus.
3. Add or update RQ6_SMOKE_REPORT.md with stable mc3000 and mc20000 results.
4. Add optional query decomposition layer for RQ6.1.
5. Extend real corpus coverage to include EU_GDPR if available.
6. Keep failure samples and manifests for audit replay.
```

Do not lower acceptance gates after seeing results.

Do not delete failure samples.

Do not present synthetic demo results as publication-grade.
