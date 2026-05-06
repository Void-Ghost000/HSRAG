# HSRAG LAW

![RQ5.5](https://img.shields.io/badge/RQ5.5-50k_PASS-green)
![target_correct](https://img.shields.io/badge/target_correct-1.000-brightgreen)
![false_allow](https://img.shields.io/badge/false_allow-0.000-brightgreen)
![cost_reduction](https://img.shields.io/badge/cost_reduction-85.76%25-blue)
![audit_chain](https://img.shields.io/badge/audit_chain-complete-brightgreen)

Legal AI retrieval systems can fail in predictable ways:

- they retrieve from the wrong legal corpus,
- they mix evidence across jurisdictions,
- they answer unsupported or ambiguous queries,
- and they often leave weak audit trails.

**HSRAG LAW** demonstrates a different approach:

```text
CTHC-typed legal addresses
+ salted domain-hash routing
+ bounded retrieval
+ evidence gating before retrieval
+ complete audit chain
```

On the current 50,000-case robustness benchmark:

```text
target_correct: 1.000
wrong_corpus_misrouting: 0.000
wrong_jurisdiction_misrouting: 0.000
unsupported / ambiguous / conflict false allow: 0.000
token / cost reduction vs lexical baselines: ≈ 85.76%
```

This repository is a research / benchmark demo for **HSRAG**  
(Hash-Structured Retrieval-Augmented Generation).

It is **not** legal advice, not a production legal search engine, and not a claim of complete official-law coverage.

---

## 1. What HSRAG LAW tests

HSRAG LAW focuses on one core question:

> Can legal retrieval be made more bounded, auditable, and resistant to cross-domain misrouting by using CTHC-style hierarchical legal addresses and salted domain hashes?

The demo tests whether legal text retrieval can be routed through structured addresses before evidence retrieval happens.

A simplified flow:

```text
query
→ CTHC typed route
→ salted domain hash
→ same-domain retrieval
→ evidence gate
→ audit output
```

---

## 2. Quick Results Summary

| Stage | Cases | Main purpose | HSRAG target_correct | False allow | Cost / token reduction | Status |
|---|---:|---|---:|---:|---:|---|
| RQ1 | corpus gate | Publication-grade real corpus gate | 1.000 | 0.000 | n/a | PASS |
| RQ2.2 | 10,176 | Real EU law + four lexical baselines | 1.000 | 0.000 | 73.33% cost reduction | PASS |
| RQ3_FIX2 | 14,208 | EU × US real-law collision benchmark | 1.000 | 0.000 | 73.55% cost reduction | PASS |
| RQ4.1 | source rebuild | Official/public source fetch + rebuild smoke test | n/a | n/a | n/a | PASS |
| RQ5.5 | 50,000 | CTHC salted-domain routing robustness | 1.000 | 0.000 | ≈ 85.76% token / cost reduction | PASS |

Unified verification result:

```text
final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
unified_audit_chain_complete: 1.0
```

---

## 3. What this demo shows

HSRAG LAW demonstrates:

### CTHC-typed legal routing

Legal text chunks are assigned structured hierarchical addresses such as:

```text
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
```

The system does not treat legal text as undifferentiated plain text.  
Each chunk carries a typed legal address.

---

### Salted domain-hash separation

Each corpus domain receives a salted hash bucket:

```text
domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)
```

Retrieval is only allowed inside the matching salted domain bucket.

This is used to reduce:

- wrong-corpus retrieval,
- jurisdiction mixing,
- and cross-domain evidence collision.

---

### Bounded retrieval

HSRAG LAW does not retrieve from the whole corpus when the query does not resolve to a stable legal identifier.

Instead, it can reject:

```text
unsupported query
ambiguous query
conflict-form query
unroutable query
```

before evidence retrieval.

---

### Auditability

Benchmark runs output:

```text
case-level audit records
summary-level audit records
gate checks
hash-chain outputs
```

This makes results easier to inspect, reproduce, and challenge.

---

## 4. Current benchmark stages

The current benchmark suite contains five main verification stages.

| Stage | Purpose | Status |
|---|---|---|
| RQ1 | Publication-grade real corpus gate | PASS |
| RQ2.2 | Real EU law benchmark with four lexical baselines and 10k+ MC cases | PASS |
| RQ3_FIX2 | EU × US real-law collision benchmark | PASS |
| RQ4.1 | Official/public source fetch and source rebuild smoke test | PASS |
| RQ5.5 | CTHC-typed salted-domain routing robustness benchmark | PASS |

---

## 5. Important scope note

The benchmark stages do **not** all use the same corpus snapshot.

### RQ2.2 and RQ3_FIX2

RQ2.2 and RQ3_FIX2 verify previously generated benchmark artifacts.

They are used as frozen verification references for:

- real-law chunk routing,
- jurisdiction / corpus collision checks,
- baseline comparison,
- audit-chain completeness.

### RQ4.1 and RQ5.5

RQ4.1 rebuilds a smaller live/local corpus from official or public legal reference URLs.

RQ5.5 then runs live robustness evaluation over the RQ4.1 rebuilt chunks.

Current RQ5.5 corpus:

```text
source: rq4_rebuilt_chunks
chunks: 110
corpora: 5
corpora list: EU_AI_ACT | EU_DMA | US_CDA230 | US_COPPA | US_FTC_ACT5
jurisdictions: EU | US
domain_hash_count: 5
```

`US_CCPA` was included in the RQ4 source manifest, but was not included in the RQ5.5 rebuilt corpus because the live fetch/rebuild step did not produce a usable rebuilt chunk set for it in this run.

This is intentional transparency, not a hidden exclusion.

---

## 6. RQ5.5 headline result

RQ5.5 is the current strongest live robustness result in this demo.

Configuration:

```text
cases: 50,000
seed: 20260505
chunks: 110
corpora: 5
domain_hash_count: 5
```

HSRAG result:

```text
target_correct: 1.0
wrong_corpus_misrouting: 0.0
wrong_jurisdiction_misrouting: 0.0
unsupported_query_false_allow: 0.0
ambiguous_query_false_allow: 0.0
conflict_query_false_allow: 0.0
case_audit_chain_complete: 1.0
summary_audit_chain_complete: 1.0
p95_latency_ms: 0.5603
total_tokens: 7,152,376
estimated_total_cost: 0.7152376
```

Global lexical baseline:

```text
target_correct: 0.9179
wrong_corpus_misrouting: 0.0821
unsupported_query_false_allow: 1.0
ambiguous_query_false_allow: 1.0
conflict_query_false_allow: 1.0
p95_latency_ms: 0.2582
total_tokens: 50,210,848
estimated_total_cost: 5.0210848
```

Domain-hint lexical baseline:

```text
target_correct: 1.0
wrong_corpus_misrouting: 0.0
unsupported_query_false_allow: 1.0
ambiguous_query_false_allow: 1.0
conflict_query_false_allow: 1.0
p95_latency_ms: 0.6697
total_tokens: 50,242,378
estimated_total_cost: 5.0242378
```

Compared with lexical baselines, HSRAG reduced token usage and estimated cost by approximately:

```text
≈ 85.76%
```

The global lexical baseline is faster in raw p95 latency, but it has non-zero misrouting and always retrieves for unsupported, ambiguous, and conflict-form queries.

HSRAG prioritizes:

```text
bounded retrieval
zero false allow
zero wrong-domain routing
auditability
lower token cost
```

rather than raw unbounded lookup speed alone.

---

## 7. Earlier benchmark results

### RQ2.2 — Real EU Law + four baselines + 10k MC

Summary:

```text
decision: RQ2_2_FOUR_BASELINES_10KMC_PASS
chunks: 188
base_queries: 424
mc_cases: 10,176
baseline_modes: 4
fail_count: 0
audit_chain_complete: 1.0
```

HSRAG metrics:

```text
target_correct: 1.0
wrong_collision: 0.0
no_evidence_false_allow: 0.0
ambiguous_false_allow: 0.0
mismatch_escape: 0.0
p95_latency_ms: 4.0389
```

Best baseline comparison:

```text
baseline_best_target_correct: 0.9392
baseline_best_wrong_collision: 0.0376
baseline_best_no_evidence_false_allow: 1.0
baseline_best_ambiguous_false_allow: 1.0
baseline_best_mismatch_escape: 1.0
token_reduction_pct_max: 78.27%
cost_reduction_pct_max: 73.33%
```

---

### RQ3_FIX2 — EU × US real-law collision benchmark

Summary:

```text
decision: RQ3_EU_US_REALLAW_COLLISION_PASS
chunks: 244
base_queries: 592
mc_cases: 14,208
corpora: 6
jurisdictions: 3
baseline_modes: 4
fail_count: 0
audit_chain_complete: 1.0
```

Included corpora:

```text
EU_AI_ACT
EU_DMA
US_CCPA
US_CDA230
US_COPPA
US_FTC_ACT5
```

HSRAG metrics:

```text
target_correct: 1.0
wrong_corpus_collision: 0.0
wrong_jurisdiction_escape: 0.0
no_evidence_false_allow: 0.0
ambiguous_false_allow: 0.0
mismatch_escape: 0.0
p95_latency_ms: 5.9244
```

Best baseline comparison:

```text
baseline_best_target_correct: 0.9079
baseline_best_wrong_corpus_collision: 0.0196
baseline_best_wrong_jurisdiction_escape: 0.0110
baseline_best_no_evidence_false_allow: 0.9667
baseline_best_ambiguous_false_allow: 1.0
baseline_best_mismatch_escape: 1.0
token_reduction_pct_max: 78.71%
cost_reduction_pct_max: 73.55%
```

---

### RQ4.1 — Official/public source fetch and rebuild

RQ4.1 tests whether the repo can fetch official or public legal references, normalize the text, rebuild chunks, and write auditable source manifests.

Summary:

```text
decision: RQ4_SOURCE_REBUILD_PASS
source_count: 6
attempt_count: 11
fetch_ok_count: 5
rebuild_ok_count: 5
fetch_warn_count: 0
fetch_error_count: 1
rebuilt_chunk_count: 110
audit_chain_complete: 1.0
```

Rebuilt sources:

| Corpus | Candidate type | Status | Chunks |
|---|---|---:|---:|
| EU_AI_ACT | PUBLIC_REFERENCE_AI_ACT_EXPLORER | FETCH_OK | 7 |
| EU_DMA | OFFICIAL_EC_PUBLIC_REFERENCE | FETCH_OK | 6 |
| US_COPPA | OFFICIAL_US_ECFR | FETCH_OK | 49 |
| US_CDA230 | PUBLIC_REFERENCE_CORNELL_LII_USCODE | FETCH_OK | 11 |
| US_FTC_ACT5 | PUBLIC_REFERENCE_CORNELL_LII_USCODE | FETCH_OK | 37 |
| US_CCPA | OFFICIAL_CA_OAG_REFERENCE | FETCH_ERROR | 0 |

RQ4.1 is a source-rebuild smoke test, not a full official-law ingestion pipeline.

Some public legal websites may require browser automation, PDF extraction, or official bulk datasets for more complete reproduction.

---

## 8. How to run

### Requirements

Recommended environment:

```text
Python 3.10+
pip
Git
```

Install dependencies from the repository root:

```powershell
pip install -r requirements.txt
```

If your environment already has the required standard libraries and Python available, the current demo scripts may run without additional packages.

---

### Run the full LAW verification chain

From the repository root:

```powershell
python .\examples\hsrag_law\scripts\run_all_verifiers.py --rq5-cases 50000 --seed 20260505
```

Expected final output:

```text
HSRAG LAW — UNIFIED VERIFICATION INDEX
final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
unified_audit_chain_complete: 1.0
```

---

### Run RQ5.5 only

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505
```

---

### Run RQ4.1 source rebuild only

```powershell
python .\examples\hsrag_law\scripts\verify_rq4_official_fetch.py --min-ok 2
```

---

### Save terminal output

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505 | Tee-Object -FilePath .\examples\hsrag_law\results\rq5_50k_terminal_output.txt
```

---

## 9. Output files

The scripts write results into:

```text
examples/hsrag_law/results/
```

Important outputs include:

```text
unified_verification_index.json
unified_verification_index.md
unified_verification_audit_chain.jsonl
unified_verification_terminal_output.txt
rq5_mc_reproduction_summary.json
rq5_mc_reproduction_summary.md
rq5_gate_checks.csv
rq5_baseline_comparison.csv
rq5_audit_chain.jsonl
```

Large case-level outputs such as `rq5_case_results.csv` may be omitted from Git history to keep the repository lightweight.

RQ4.1 outputs include:

```text
rq4_source_rebuild_summary.json
rq4_source_rebuild_summary.md
rq4_source_records.csv
rq4_fetch_attempts.csv
rq4_rebuilt_chunks.csv
rq4_gate_checks.csv
rq4_rebuilt_source_manifest.json
rq4_source_rebuild_audit_chain.jsonl
```

---

## 10. Store classification summary

HSRAG LAW follows a three-store governance model:

| Store | Meaning | LAW usage |
|---|---|---|
| FHS | Fact Hash Store | Verified, source-linked, versioned legal text |
| EHS | Ephemeral Hash Store | Pending, unverified, temporary, or user-provided material |
| CHS | Creative / Challenge Hash Store | Synthetic, ambiguous, conflict, or failure-case material |

Default rule:

```text
Verified legal text → FHS
Unverified or pending legal text → EHS
Synthetic, ambiguous, conflict, or failure-case material → CHS
```

For legal and regulatory retrieval:

```text
FHS > EHS > CHS
```

EHS and CHS must not override matched FHS evidence.

If a query cannot be grounded in matched FHS evidence, HSRAG should reject, warn, or return a no-evidence decision rather than generate an unsupported legal answer.

This is a retrieval-governance rule, not legal advice.

A longer store-classification document may be added as a separate reference file.

---

## 11. Interpretation

HSRAG LAW is not claiming that lexical retrieval is useless.

Instead, this demo shows that lexical retrieval alone has difficulty distinguishing:

```text
supported legal query
unsupported legal query
ambiguous legal query
conflict-form legal query
wrong-corpus retrieval
wrong-jurisdiction retrieval
```

HSRAG adds a structured routing layer before retrieval:

```text
CTHC typed legal address
+ salted domain hash
+ bounded retrieval
+ evidence gate
+ audit chain
```

This makes the retrieval process more conservative, more auditable, and less prone to cross-domain evidence mixing.

---

## 12. Current limitations

Current limitations:

- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3_FIX2 corpus from raw official source files.
- RQ4.1 uses official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- This demo is not legal advice.
- This demo is a retrieval architecture benchmark, not a legal reasoning benchmark.

---

## 13. Suggested next steps

Planned improvements:

1. Add a clean custom-corpus template so users can paste their own public legal text and run the same routing benchmark.
2. Add full manifest-based corpus ingestion with explicit source license and provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add a longer store-classification reference document.
6. Add README-level benchmark reproduction instructions.
7. Add a public report summarizing RQ1–RQ5.5.

---

## 14. One-line summary

HSRAG LAW demonstrates that **CTHC-typed legal addresses plus salted domain-hash retrieval** can reduce cross-domain legal retrieval risk, reject unsupported / ambiguous / conflict-form queries, preserve auditability, and significantly reduce token cost in a reproducible benchmark setting.