# HSRAG LAW

**HSRAG LAW** is a legal-text retrieval demonstration for **HSRAG**  
(Hash-Structured Retrieval-Augmented Generation).

This example focuses on one core question:

> Can legal retrieval be made more bounded, auditable, and resistant to cross-domain misrouting by using CTHC-style hierarchical legal addresses and salted domain hashes?

The current implementation is a research / benchmark demo.  
It is **not** legal advice, not a production legal search engine, and not a claim of complete official-law coverage.

---

## 1. What this demo shows

HSRAG LAW demonstrates:

- **CTHC-typed legal routing**  
  Legal text chunks are assigned structured hierarchical addresses such as:

  ```text
  LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
  LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
  ```

- **Salted domain-hash separation**  
  Each corpus domain receives a salted hash bucket:

  ```text
  domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)
  ```

  Retrieval is only allowed inside the matching salted domain bucket.

- **Bounded retrieval**  
  The system does not retrieve from the whole corpus when the query does not resolve to a stable legal identifier.

- **Evidence gating**  
  Unsupported, ambiguous, and conflict-form queries are rejected before evidence retrieval.

- **Auditability**  
  Benchmark runs output case-level and summary-level audit hashes.

---

## 2. Current benchmark status

The current benchmark suite contains five main verification stages.

| Stage | Purpose | Status |
|---|---|---|
| RQ1 | Publication-grade real corpus gate | PASS |
| RQ2.2 | Real EU law benchmark with four lexical baselines and 10k+ MC cases | PASS |
| RQ3 | EU × US real-law collision benchmark | PASS |
| RQ4.1 | Official/public source fetch and source rebuild smoke test | PASS |
| RQ5.5 | CTHC-typed salted-domain routing robustness benchmark | PASS |

---

## 3. Important scope note

The benchmark stages do **not** all use the same corpus snapshot.

### RQ2.2 and RQ3

RQ2.2 and RQ3 verify previously generated benchmark artifacts.

They are used as frozen verification references for:

- real-law chunk routing,
- jurisdiction/corpus collision checks,
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

## 4. RQ2.2 — Real EU Law + four baselines + 10k MC

RQ2.2 verifies a real EU-law benchmark with four lexical baselines.

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

## 5. RQ3 — EU × US real-law collision benchmark

RQ3 extends the benchmark to EU × US legal-corpus collision testing.

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

## 6. RQ4.1 — Official/public source fetch and rebuild

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

## 7. RQ5.5 — CTHC salted-domain routing robustness

RQ5.5 is the current strongest live robustness result in this demo.

It evaluates:

```text
query
→ CTHC typed route
→ salted domain hash
→ same-domain retrieval
→ evidence gate
→ audit output
```

The benchmark uses the RQ4.1 rebuilt chunks:

```text
chunks: 110
corpora: 5
domain_hash_count: 5
cases: 50,000
seed: 20260505
```

Result:

```text
decision: RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_PASS
case_audit_chain_complete: 1.0
summary_audit_chain_complete: 1.0
```

HSRAG metrics:

```text
target_correct: 1.0
wrong_corpus_misrouting: 0.0
wrong_jurisdiction_misrouting: 0.0
unsupported_query_false_allow: 0.0
ambiguous_query_false_allow: 0.0
conflict_query_false_allow: 0.0
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

The global lexical baseline is faster in raw p95 latency, but it has non-zero misrouting and always retrieves for unsupported / ambiguous / conflict-form queries.

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

## 8. How to run

From the repository root:

```powershell
python .\examples\hsrag_law\scripts\run_all_verifiers.py
```

Run RQ4.1 source rebuild:

```powershell
python .\examples\hsrag_law\scripts\verify_rq4_official_fetch.py --min-ok 2
```

Run RQ5.5 10k robustness benchmark:

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 10000 --seed 20260505
```

Run RQ5.5 50k robustness benchmark:

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505
```

Save terminal output:

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
rq5_mc_reproduction_summary.json
rq5_mc_reproduction_summary.md
rq5_case_results.csv
rq5_gate_checks.csv
rq5_baseline_comparison.csv
rq5_audit_chain.jsonl
rq5_50k_terminal_output.txt
```

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

## 10. Interpretation

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

## 11. Current limitations

Current limitations:

- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3 corpus from raw official source files.
- RQ4.1 uses official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- This demo is not legal advice.
- This demo is a retrieval architecture benchmark, not a legal reasoning benchmark.

---

## 12. Suggested next steps

Planned improvements:

1. Add a clean custom-corpus template so users can paste their own public legal text and run the same routing benchmark.
2. Add full manifest-based corpus ingestion with explicit source license / provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add README-level benchmark reproduction instructions.
6. Add a public report summarizing RQ1–RQ5.5.

---

## 13. One-line summary

HSRAG LAW demonstrates that **CTHC-typed legal addresses plus salted domain-hash retrieval** can reduce cross-domain legal retrieval risk, reject unsupported / ambiguous / conflict-form queries, preserve auditability, and significantly reduce token cost in a reproducible benchmark setting.