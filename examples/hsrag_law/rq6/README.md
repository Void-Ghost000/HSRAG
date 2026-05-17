# HSRAG LAW RQ6 — Conversational Legal Collision Benchmark

RQ6 tests whether retrieval systems can resist **cross-jurisdiction context contamination** in multi-turn legal retrieval conversations.

In plain language:

> If a user first asks about an EU law and then asks about a similar U.S. law, will the retrieval system correctly switch legal corpus and jurisdiction, or will it accidentally carry over the previous EU context?

Example:

```text
Turn 1: Find EU AI Act Article 5 prohibited AI practices.
Turn 2: Now find U.S. FTC Act Section 5 on unfair or deceptive acts or practices.
```

A contaminated retrieval system may incorrectly retrieve EU AI Act content again in Turn 2, even though the user switched to U.S. law.

RQ6 compares baseline retrieval methods against HSRAG-style boundary-first retrieval.

---

## Current Status

```text
RQ6 version: v0.1.1
Status: MC=20000 stress pass
Rows: 720000
Demo mode: False
Corpus source: examples/hsrag_law/results/rq4_rebuilt_chunks.csv
Available corpora: EU_AI_ACT, EU_DMA, US_CDA230, US_COPPA, US_FTC_ACT5
```

HSRAG modes achieved:

```text
target_correct_rate: 1.000
hit_target_correct_rate: 1.000
wrong_corpus_collision_rate: 0.000
wrong_jurisdiction_escape_rate: 0.000
no_evidence_false_allow_rate: 0.000
ambiguous_false_allow_rate: 0.000
cross_turn_contamination_rate: 0.000
switch_turn_contamination_rate: 0.000
HSRAG failure sample count: 0
```

This is a **real/public rebuilt corpus stress benchmark**, not a publication-grade final claim.

Detailed report:

```text
RQ6_SMOKE_REPORT.md
```

---

## What RQ6 Tests

RQ6 focuses on multi-turn legal retrieval collisions involving similar laws, similar concepts, or similar numbering across EU and U.S. jurisdictions.

Examples include:

- EU AI Act Article 5
- U.S. FTC Act Section 5
- U.S. CDA Section 230
- EU DMA gatekeeper obligations
- U.S. COPPA children data rules
- EU GDPR Article 8, if available

RQ6 measures:

- wrong corpus retrieval
- wrong jurisdiction retrieval
- no-evidence false allow
- ambiguous false allow
- cross-turn contamination
- switch-turn contamination
- source hash presence
- audit chain completeness
- retrieval latency

---

## What RQ6 Is Not

RQ6 does **not** claim that RAG is dead.

RQ6 does **not** claim that HSRAG replaces all retrieval systems.

RQ6 does **not** provide legal advice.

RQ6 does **not** prove production readiness.

RQ6 does **not** evaluate legal reasoning correctness beyond retrieval evidence matching.

RQ6 evaluates HSRAG as a:

- boundary-first retrieval governance layer
- CTHC constrained retrieval layer
- audit layer before retrieval
- context contamination control layer

BM25 is treated as a strong lexical baseline, not as an enemy baseline.

---

## One-Click Demo Scripts

RQ6 provides three main demo levels:

| Script | MC | Expected rows | Purpose |
|---|---:|---:|---|
| `run_rq6_smoke` | 30 | 1,080 | Quick sanity check |
| `run_rq6_standard` | 3,000 | 108,000 | Standard smoke benchmark |
| `run_rq6_stress` | 20,000 | 720,000 | Stress benchmark |

A backward-compatible alias is also provided:

| Script | Meaning |
|---|---|
| `run_rq6_full` | Alias for `run_rq6_stress` |

---

## Run on Windows PowerShell

From the repository root:

### Quick smoke demo

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_smoke.ps1
```

### Standard benchmark

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_standard.ps1
```

### Stress benchmark

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_stress.ps1
```

### Backward-compatible full alias

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_full.ps1
```

---

## Run on Linux / macOS / Git Bash / WSL

From the repository root:

### Quick smoke demo

```bash
bash examples/hsrag_law/rq6/run_rq6_smoke.sh
```

### Standard benchmark

```bash
bash examples/hsrag_law/rq6/run_rq6_standard.sh
```

### Stress benchmark

```bash
bash examples/hsrag_law/rq6/run_rq6_stress.sh
```

### Backward-compatible full alias

```bash
bash examples/hsrag_law/rq6/run_rq6_full.sh
```

---

## Direct Python Commands

You can also run the benchmark directly.

### Quick smoke test

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks examples\hsrag_law\results\rq4_rebuilt_chunks.csv --mc 30
```

Expected row count:

```text
30 MC trials × 6 retrieval modes × 3 context policies × 2 turns = 1080 rows
```

### Standard smoke benchmark

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks examples\hsrag_law\results\rq4_rebuilt_chunks.csv --mc 3000
```

Expected row count:

```text
3000 MC trials × 6 retrieval modes × 3 context policies × 2 turns = 108000 rows
```

### Stress benchmark

```powershell
python examples\hsrag_law\rq6\run_rq6_conversational_collision.py --chunks examples\hsrag_law\results\rq4_rebuilt_chunks.csv --mc 20000
```

Expected row count:

```text
20000 MC trials × 6 retrieval modes × 3 context policies × 2 turns = 720000 rows
```

---

## Required Corpus Format

RQ6 expects a normalized chunk CSV with at least:

```text
chunk_id
corpus or corpus_id
jurisdiction
unit or source_title
text
source_hash
```

The current RQ4 rebuilt corpus uses:

```text
examples/hsrag_law/results/rq4_rebuilt_chunks.csv
```

Known supported fields include:

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

The runner supports both:

```text
corpus
corpus_id
```

If `source_hash` is missing, the runner may backfill it with `sha256(text)`, but this is recorded in the run manifest.

If no `--chunks` file is provided, the runner may use a synthetic demo corpus.

Synthetic demo runs are smoke tests only and must not be reported as publication-grade results.

---

## Retrieval Modes

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
| `hsrag_cthc` | Boundary-first CTHC route, then BM25 inside the constrained subset |
| `hsrag_hybrid_subset` | Boundary-first CTHC route, then BM25 + TF-IDF RRF inside the constrained subset |

---

## Context Policies

RQ6 compares three conversation-memory policies:

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

## Query Pair Generator

RQ6 v0.1 includes these two-turn collision patterns:

```text
A. EU_AI_ACT Article 5 → US_FTC_ACT Section 5
B. US_FTC_ACT Section 5 → EU_AI_ACT Article 5
C. US_CDA230 platform liability → EU_DMA gatekeeper obligations
D. EU_DMA gatekeeper obligations → US_CDA230 platform liability
E. US_COPPA children data → EU_GDPR Article 8 or NO_EVIDENCE
F. Ambiguous Article 5 carryover test
```

These cases are designed to stress:

- EU / U.S. jurisdiction switching
- similar article or section numbers
- similar platform and consumer-protection concepts
- ambiguous follow-up queries
- no-evidence conditions when a corpus is unavailable

---

## Mutation Layer

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

The CTHC detector includes a lightweight normalization layer for benchmark noise such as:

- punctuation noise
- light typo mutation
- spaced acronyms
- benchmark-generated distractor warning text

This normalization does not use expected labels or answer keys.

---

## Output Artifacts

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

## Metrics

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

## MC=20000 Stress Result

Run summary:

```text
MC: 20000
Rows: 720000
Demo mode: False
Corpus source: examples/hsrag_law/results/rq4_rebuilt_chunks.csv
Available corpora: EU_AI_ACT, EU_DMA, US_CDA230, US_COPPA, US_FTC_ACT5
Source hash present rate: 1.0
Audit chain complete rate: 1.0
```

Overall result across all modes and policies:

```text
target_correct_rate: 0.7910888888888888
hit_target_correct_rate: 0.877074125184163
wrong_corpus_collision_rate: 0.10244027777777778
wrong_jurisdiction_escape_rate: 0.09491666666666666
no_evidence_false_allow_rate: 0.05092083333333333
ambiguous_false_allow_rate: 0.05555
cross_turn_contamination_rate: 0.1070611111111111
switch_turn_contamination_rate: 0.12152638888888889
source_hash_present_rate: 1.0
audit_chain_complete_rate: 1.0
p95_latency_ms: 22.6012
```

The overall result includes both baseline and HSRAG modes.

The main comparison should be read by:

```text
mode × context_policy
```

---

## HSRAG MC=20000 Result

| Mode | Context policy | target | hit | wrong corpus | wrong jurisdiction | no-evidence false allow | ambiguous false allow | cross-turn | switch-turn | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `hsrag_cthc` | `bounded_cthc_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.600 ms |
| `hsrag_cthc` | `naive_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.725 ms |
| `hsrag_cthc` | `no_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2.009 ms |
| `hsrag_hybrid_subset` | `bounded_cthc_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 9.036 ms |
| `hsrag_hybrid_subset` | `naive_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 9.042 ms |
| `hsrag_hybrid_subset` | `no_memory` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 8.986 ms |

Additional check:

```text
HSRAG target_correct=False failure sample count: 0
```

Interpretation:

```text
In the MC=20000 stress benchmark, HSRAG CTHC and HSRAG Hybrid Subset produced no wrong-corpus retrieval, no wrong-jurisdiction retrieval, no false allow on NO_EVIDENCE or AMBIGUOUS cases, and no cross-turn contamination.
```

---

## Baseline Contamination Signal

Selected baseline results from the same benchmark family:

| Mode | Context policy | target | wrong corpus | wrong jurisdiction | cross-turn | switch-turn |
|---|---|---:|---:|---:|---:|---:|
| `bm25_domain_hint` | `no_memory` | 0.917 | 0.000 | 0.000 | 0.000 | 0.000 |
| `bm25_domain_hint` | `naive_memory` | 0.667 | 0.167 | 0.167 | 0.250 | 0.250 |
| `bm25_global` | `naive_memory` | 0.625 | 0.209 | 0.198 | 0.250 | 0.250 |
| `hybrid_rrf_global` | `naive_memory` | 0.625 | 0.209 | 0.198 | 0.250 | 0.250 |
| `tfidf_global` | `naive_memory` | 0.573 | 0.260 | 0.229 | 0.229 | 0.250 |

Interpretation:

```text
The naive memory policy increases cross-turn contamination for baseline retrieval modes.
BM25 domain hint is a strong lexical baseline under no_memory, but naive memory can still pollute retrieval context.
```

This supports the RQ6 hypothesis that conversational legal retrieval requires explicit context boundaries.

---

## Limitation: Atomic Legal Retrieval First

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

## Claim Boundary

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

Allowed claim:

```text
HSRAG CTHC achieved zero wrong-corpus retrieval, zero wrong-jurisdiction retrieval, zero false allow on NO_EVIDENCE / AMBIGUOUS cases, and zero cross-turn contamination in the MC=20000 RQ6 stress benchmark.
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
A smoke or stress benchmark is automatically publication-grade evidence.
```

---

## Recommended Next Steps

```text
1. Keep RQ6 v0.1.1 as the current MC=20000 stress-pass baseline.
2. Keep one-click demo scripts stable.
3. Add optional query decomposition layer for RQ6.1.
4. Extend real corpus coverage to include EU_GDPR if available.
5. Keep failure samples and manifests for audit replay.
6. Do not lower acceptance gates after seeing results.
7. Do not delete failure samples.
8. Do not present synthetic demo results as publication-grade.
```