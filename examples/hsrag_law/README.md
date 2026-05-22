# HSRAG LAW

![RQ5.5](https://img.shields.io/badge/RQ5.5-50k_PASS-green)
![target_correct](https://img.shields.io/badge/target_correct-1.000-brightgreen)
![false_allow](https://img.shields.io/badge/false_allow-0.000-brightgreen)
![cost_reduction](https://img.shields.io/badge/cost_reduction-85.76%25-blue)
![audit_chain](https://img.shields.io/badge/audit_chain-complete-brightgreen)

**HSRAG LAW** is a legal-text retrieval benchmark demo for **HSRAG**  
(Hash-Structured Retrieval-Augmented Generation).

Legal AI retrieval systems can fail in predictable ways:

- they retrieve from the wrong legal corpus,
- they mix evidence across jurisdictions,
- they answer unsupported or ambiguous queries,
- and they often leave weak audit trails.

HSRAG LAW demonstrates a different approach:

    CTHC-typed legal addresses
    + salted domain-hash routing
    + bounded retrieval
    + evidence gating before retrieval
    + complete audit chain

On the current 50,000-case robustness benchmark:

    target_correct: 1.000
    wrong_corpus_misrouting: 0.000
    wrong_jurisdiction_misrouting: 0.000
    unsupported / ambiguous / conflict false allow: 0.000
    token / cost reduction vs lexical baselines: ≈ 85.76%

This is a research / benchmark demo.

It is **not** legal advice, not a production legal search engine, and not a claim of complete official-law coverage.

---

## Quick links

- [Custom corpus template](custom_template/)
- [QSVCS public template](custom_template/QSVCS_PUBLIC_TEMPLATE.md)
- [Main project README](../../README.md)
- [FAQ](../../docs/FAQ.md)
- [Project Manifesto](../../docs/project_manifesto.md)

---

## Quick start: run the smoke demo

From the repository root:

    python .\examples\hsrag_law\run_demo.py

Expected result:

    SMOKE_TEST_PASS

This smoke demo shows the minimal HSRAG LAW flow:

    legal query
    → CTHC-style domain classification
    → hash-structured routing
    → bounded retrieval
    → guard decision
    → audit hash chain
    → benchmark summary

Use this first if you only want to confirm that the demo can run.

For full benchmark reproduction, see the sections below.

---

## 1. What HSRAG LAW tests

HSRAG LAW focuses on one core question:

> Can legal retrieval be made more bounded, auditable, and resistant to cross-domain misrouting by using CTHC-style hierarchical legal addresses and salted domain hashes?

The demo tests whether legal text retrieval can be routed through structured addresses before evidence retrieval happens.

A simplified flow:

    query
    → CTHC typed route
    → salted domain hash
    → same-domain retrieval
    → evidence gate
    → audit output

---

## 2. Plain-language analogy

A normal legal RAG system often works like asking:

    Which legal paragraph sounds most similar?

HSRAG LAW first asks something closer to:

    Which legal shelf, jurisdiction, source, corpus, or evidence address is this query allowed to search?

Only after the query is routed to a bounded legal address does retrieval happen inside that allowed space.

In short:

    RAG searches by similarity.
    HSRAG LAW first narrows the legal shelf.

This does not make lexical search or vector RAG useless.

Instead, HSRAG LAW adds a structured addressing and evidence-governance layer before retrieval, so that downstream retrieval can operate inside a smaller, clearer, more auditable search space.

---

## 3. Quick Results Summary

| Stage | Cases | Main purpose | HSRAG target_correct | False allow | Cost / token reduction | Status |
|---|---:|---|---:|---:|---:|---|
| RQ1 | corpus gate | Publication-grade real corpus gate | 1.000 | 0.000 | n/a | PASS |
| RQ2.2 | 10,176 | Real EU law + four lexical baselines | 1.000 | 0.000 | 73.33% cost reduction | PASS |
| RQ3_FIX2 | 14,208 | EU × US real-law collision benchmark | 1.000 | 0.000 | 73.55% cost reduction | PASS |
| RQ4.1 | source rebuild | Official/public source fetch + rebuild smoke test | n/a | n/a | n/a | PASS |
| RQ5.5 | 50,000 | CTHC salted-domain routing robustness | 1.000 | 0.000 | ≈ 85.76% token / cost reduction | PASS |

Unified verification result:

    final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
    unified_audit_chain_complete: 1.0

---

## 4. What this demo shows

### CTHC-typed legal routing

Legal text chunks are assigned structured hierarchical addresses such as:

    LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
    LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL

The system does not treat legal text as undifferentiated plain text.

Each chunk carries a typed legal address.

---

### Salted domain-hash separation

Each corpus domain receives a salted hash bucket:

    domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)

Retrieval is only allowed inside the matching salted domain bucket.

This is used to reduce:

- wrong-corpus retrieval,
- jurisdiction mixing,
- and cross-domain evidence collision.

---

### Bounded retrieval

HSRAG LAW does not retrieve from the whole corpus when the query does not resolve to a stable legal identifier.

Instead, it can reject:

    unsupported query
    ambiguous query
    conflict-form query
    unroutable query

before evidence retrieval.

---

### Auditability

Benchmark runs output:

    case-level audit records
    summary-level audit records
    gate checks
    hash-chain outputs

This makes results easier to inspect, reproduce, and challenge.

---

## 5. Current benchmark stages

The current benchmark suite contains five main verification stages.

| Stage | Purpose | Status |
|---|---|---|
| RQ1 | Publication-grade real corpus gate | PASS |
| RQ2.2 | Real EU law benchmark with four lexical baselines and 10k+ MC cases | PASS |
| RQ3_FIX2 | EU × US real-law collision benchmark | PASS |
| RQ4.1 | Official/public source fetch and source rebuild smoke test | PASS |
| RQ5.5 | CTHC-typed salted-domain routing robustness benchmark | PASS |

---

## 6. Important scope note

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

    source: rq4_rebuilt_chunks
    chunks: 110
    corpora: 5
    corpora list: EU_AI_ACT | EU_DMA | US_CDA230 | US_COPPA | US_FTC_ACT5
    jurisdictions: EU | US
    domain_hash_count: 5

`US_CCPA` was included in the RQ4 source manifest, but was not included in the RQ5.5 rebuilt corpus because the live fetch/rebuild step did not produce a usable rebuilt chunk set for it in this run.

This is intentional transparency, not a hidden exclusion.

---

## 7. RQ5.5 headline result

RQ5.5 is the current strongest live robustness result in this demo.

Configuration:

    cases: 50,000
    seed: 20260505
    chunks: 110
    corpora: 5
    domain_hash_count: 5

HSRAG result:

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

Global lexical baseline:

    target_correct: 0.9179
    wrong_corpus_misrouting: 0.0821
    unsupported_query_false_allow: 1.0
    ambiguous_query_false_allow: 1.0
    conflict_query_false_allow: 1.0
    p95_latency_ms: 0.2582
    total_tokens: 50,210,848
    estimated_total_cost: 5.0210848

Domain-hint lexical baseline:

    target_correct: 1.0
    wrong_corpus_misrouting: 0.0
    unsupported_query_false_allow: 1.0
    ambiguous_query_false_allow: 1.0
    conflict_query_false_allow: 1.0
    p95_latency_ms: 0.6697
    total_tokens: 50,242,378
    estimated_total_cost: 5.0242378

Compared with lexical baselines, HSRAG reduced token usage and estimated cost by approximately:

    ≈ 85.76%

The global lexical baseline is faster in raw p95 latency, but it has non-zero misrouting and always retrieves for unsupported, ambiguous, and conflict-form queries.

HSRAG prioritizes:

    bounded retrieval
    zero false allow
    zero wrong-domain routing
    auditability
    lower token cost

rather than raw unbounded lookup speed alone.

---

## 8. Earlier benchmark results

### RQ2.2 — Real EU Law + four baselines + 10k MC

Summary:

    decision: RQ2_2_FOUR_BASELINES_10KMC_PASS
    chunks: 188
    base_queries: 424
    mc_cases: 10,176
    baseline_modes: 4
    fail_count: 0
    audit_chain_complete: 1.0

HSRAG metrics:

    target_correct: 1.0
    wrong_collision: 0.0
    no_evidence_false_allow: 0.0
    ambiguous_false_allow: 0.0
    mismatch_escape: 0.0
    p95_latency_ms: 4.0389

Best baseline comparison:

    baseline_best_target_correct: 0.9392
    baseline_best_wrong_collision: 0.0376
    baseline_best_no_evidence_false_allow: 1.0
    baseline_best_ambiguous_false_allow: 1.0
    baseline_best_mismatch_escape: 1.0
    token_reduction_pct_max: 78.27%
    cost_reduction_pct_max: 73.33%

---

### RQ3_FIX2 — EU × US real-law collision benchmark

Summary:

    decision: RQ3_EU_US_REALLAW_COLLISION_PASS
    chunks: 244
    base_queries: 592
    mc_cases: 14,208
    corpora: 6
    jurisdictions: 3
    baseline_modes: 4
    fail_count: 0
    audit_chain_complete: 1.0

Included corpora:

    EU_AI_ACT
    EU_DMA
    US_CCPA
    US_CDA230
    US_COPPA
    US_FTC_ACT5

HSRAG metrics:

    target_correct: 1.0
    wrong_corpus_collision: 0.0
    wrong_jurisdiction_escape: 0.0
    no_evidence_false_allow: 0.0
    ambiguous_false_allow: 0.0
    mismatch_escape: 0.0
    p95_latency_ms: 5.9244

Best baseline comparison:

    baseline_best_target_correct: 0.9079
    baseline_best_wrong_corpus_collision: 0.0196
    baseline_best_wrong_jurisdiction_escape: 0.0110
    baseline_best_no_evidence_false_allow: 0.9667
    baseline_best_ambiguous_false_allow: 1.0
    baseline_best_mismatch_escape: 1.0
    token_reduction_pct_max: 78.71%
    cost_reduction_pct_max: 73.55%

---

### RQ4.1 — Official/public source fetch and rebuild

RQ4.1 tests whether the repo can fetch official or public legal references, normalize the text, rebuild chunks, and write auditable source manifests.

Summary:

    decision: RQ4_SOURCE_REBUILD_PASS
    source_count: 6
    attempt_count: 11
    fetch_ok_count: 5
    rebuild_ok_count: 5
    fetch_warn_count: 0
    fetch_error_count: 1
    rebuilt_chunk_count: 110
    audit_chain_complete: 1.0

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

## 9. How to run

### Requirements

Recommended environment:

    Python 3.10+
    pip
    Git

Install dependencies from the repository root:

    pip install -r requirements.txt

If your environment already has the required standard libraries and Python available, the current demo scripts may run without additional packages.

---

### Run the smoke demo

From the repository root:

    python .\examples\hsrag_law\run_demo.py

Expected result:

    SMOKE_TEST_PASS

---

### Run the full LAW verification chain

From the repository root:

    python .\examples\hsrag_law\scripts\run_all_verifiers.py --rq5-cases 50000 --seed 20260505

Expected final output:

    HSRAG LAW — UNIFIED VERIFICATION INDEX
    final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
    unified_audit_chain_complete: 1.0

---

### Run RQ5.5 only

    python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505

---

### Run RQ4.1 source rebuild only

    python .\examples\hsrag_law\scripts\verify_rq4_official_fetch.py --min-ok 2

---

### Save terminal output

    python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505 | Tee-Object -FilePath .\examples\hsrag_law\results\rq5_50k_terminal_output.txt

---

### Run the custom corpus template

If you want to test your own clean, legally usable public legal text, use the custom corpus template:

    examples/hsrag_law/custom_template/

Basic workflow:

1. Put clean public legal text into:

    examples/hsrag_law/custom_template/input/legal_texts/

2. Edit the manifest:

    examples/hsrag_law/custom_template/input/manifest.example.json

3. Build the custom corpus:

    python .\examples\hsrag_law\custom_template\scripts\build_custom_corpus.py

4. Run the custom benchmark:

    python .\examples\hsrag_law\custom_template\scripts\run_custom_benchmark.py

Expected smoke-test output:

    decision: CUSTOM_CORPUS_BUILD_PASS
    decision: CUSTOM_BENCHMARK_PASS
    target_correct: 1.0
    unsupported_query_false_allow: 0.0
    ambiguous_query_false_allow: 0.0
    conflict_query_false_allow: 0.0
    audit_chain_complete: 1.0

This template is designed for clean plaintext / markdown legal text first.

PDF extraction, browser automation, and official bulk ingestion are planned as separate ingestion tools.

---

## 10. Output files

The scripts write results into:

    examples/hsrag_law/results/

Important outputs include:

    unified_verification_index.json
    unified_verification_index.md
    unified_verification_audit_chain.jsonl
    unified_verification_terminal_output.txt
    rq5_mc_reproduction_summary.json
    rq5_mc_reproduction_summary.md
    rq5_gate_checks.csv
    rq5_baseline_comparison.csv
    rq5_audit_chain.jsonl

Large case-level outputs such as `rq5_case_results.csv` may be omitted from Git history to keep the repository lightweight.

RQ4.1 outputs include:

    rq4_source_rebuild_summary.json
    rq4_source_rebuild_summary.md
    rq4_source_records.csv
    rq4_fetch_attempts.csv
    rq4_rebuilt_chunks.csv
    rq4_gate_checks.csv
    rq4_rebuilt_source_manifest.json
    rq4_source_rebuild_audit_chain.jsonl

---

## 10.1 Artifact, metric, and report map

HSRAG LAW writes benchmark outputs into:

    examples/hsrag_law/results/

These artifacts are intended to make the benchmark reproducible, inspectable, and easier to challenge.

---

### Unified verification artifacts

| Artifact | Purpose |
|---|---|
| unified_verification_index.md | Human-readable final verification index for RQ1–RQ5.5 |
| unified_verification_index.json | Machine-readable final verification index |
| unified_verification_audit_chain.jsonl | Audit-chain trace for the unified verification index |
| unified_verification_terminal_output.txt | Captured terminal output for the unified verification run |

Use these files when you want to check whether the full LAW verification chain passed.

Expected high-level result:

    final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
    unified_audit_chain_complete: 1.0

---

### RQ5.5 robustness artifacts

| Artifact | Purpose |
|---|---|
| rq5_mc_reproduction_summary.md | Human-readable RQ5.5 benchmark summary |
| rq5_mc_reproduction_summary.json | Machine-readable RQ5.5 benchmark summary |
| rq5_case_results.csv | Case-level results for each generated benchmark case |
| rq5_baseline_comparison.csv | HSRAG versus lexical baseline comparison |
| rq5_gate_checks.csv | Acceptance gate checks |
| rq5_audit_chain.jsonl | RQ5.5 audit-chain trace |

Use these files when you want to inspect routing behavior, false allow behavior, token estimates, cost estimates, latency, and audit completeness.

Expected RQ5.5 result in the current 50k benchmark run:

    target_correct: 1.0
    wrong_corpus_misrouting: 0.0
    wrong_jurisdiction_misrouting: 0.0
    unsupported_query_false_allow: 0.0
    ambiguous_query_false_allow: 0.0
    conflict_query_false_allow: 0.0
    audit_chain_complete: 1.0

---

### RQ4.1 source rebuild artifacts

| Artifact | Purpose |
|---|---|
| rq4_source_rebuild_summary.md | Human-readable source fetch and rebuild summary |
| rq4_source_rebuild_summary.json | Machine-readable source rebuild summary |
| rq4_source_records.csv | Source-level fetch and rebuild records |
| rq4_fetch_attempts.csv | Fetch attempts and candidate source records |
| rq4_rebuilt_chunks.csv | Rebuilt legal-text chunks used by RQ5.5 |
| rq4_gate_checks.csv | RQ4.1 acceptance gate checks |
| rq4_rebuilt_source_manifest.json | Source manifest for rebuilt corpora |
| rq4_source_rebuild_audit_chain.jsonl | RQ4.1 audit-chain trace |

Use these files when you want to inspect which official / public references were fetched, which sources were rebuilt successfully, and which chunks were used downstream.

---

## 10.2 Metric glossary

### target_correct

Whether a supported query was routed to the expected target corpus / evidence domain.

Higher is better.

In RQ5.5:

    target_correct: 1.0

---

### wrong_corpus_misrouting

Whether the system retrieved evidence from the wrong corpus.

Lower is better.

In RQ5.5:

    wrong_corpus_misrouting: 0.0

---

### wrong_jurisdiction_misrouting

Whether the system retrieved evidence from the wrong jurisdiction.

Lower is better.

In RQ5.5:

    wrong_jurisdiction_misrouting: 0.0

---

### unsupported_query_false_allow

Whether an unsupported query was incorrectly allowed.

Lower is better.

In RQ5.5:

    unsupported_query_false_allow: 0.0

---

### ambiguous_query_false_allow

Whether an ambiguous query was incorrectly allowed.

Lower is better.

In RQ5.5:

    ambiguous_query_false_allow: 0.0

---

### conflict_query_false_allow

Whether a conflict-form query was incorrectly allowed.

Lower is better.

In RQ5.5:

    conflict_query_false_allow: 0.0

---

### audit_chain_complete

Whether the audit chain is complete and reproducible.

Expected value:

    audit_chain_complete: 1.0

---

### p95_latency_ms

The 95th percentile latency in milliseconds.

This is useful for comparing runtime behavior, but it should not be interpreted alone.

A baseline may be faster in raw lookup speed while still allowing unsupported, ambiguous, or conflict-form queries.

---

### total_tokens

Estimated retrieved token volume.

This is used to compare how much context would be passed downstream.

Lower token volume may reduce cost, especially when the retrieved context is later sent to a language model.

---

### estimated_total_cost

Estimated benchmark cost under the configured token price.

This is not a production billing guarantee.

It is a benchmark-side cost estimate used for relative comparison.

---

## 10.3 How to read the reports

For a quick check, read:

    unified_verification_index.md

For RQ5.5 benchmark details, read:

    rq5_mc_reproduction_summary.md

For case-level inspection, open:

    rq5_case_results.csv

For baseline comparison, open:

    rq5_baseline_comparison.csv

For acceptance gate verification, open:

    rq5_gate_checks.csv

For audit trace inspection, open:

    rq5_audit_chain.jsonl

A minimal reviewer path is:

    unified_verification_index.md
    → rq5_mc_reproduction_summary.md
    → rq5_baseline_comparison.csv
    → rq5_gate_checks.csv
    → rq5_audit_chain.jsonl

---

## 10.4 Important interpretation note

The artifacts do not claim that HSRAG is production-ready or that it solves all legal reasoning tasks.

They show that, under this benchmark setup, CTHC-typed routing plus salted domain-hash retrieval can reduce specific retrieval risks:

- wrong-corpus retrieval
- wrong-jurisdiction retrieval
- unsupported-query false allow
- ambiguous-query false allow
- conflict-query false allow
- weak auditability
- excessive token usage

This is a retrieval architecture benchmark, not legal advice.

---

## 11. Store classification summary

HSRAG LAW follows a three-store governance model:

| Store | Meaning | LAW usage |
|---|---|---|
| FHS | Fact Hash Store | Verified, source-linked, versioned legal text |
| EHS | Ephemeral Hash Store | Pending, unverified, temporary, or user-provided material |
| CHS | Creative / Challenge Hash Store | Synthetic, ambiguous, conflict, or failure-case material |

Default rule:

    Verified legal text → FHS
    Unverified or pending legal text → EHS
    Synthetic, ambiguous, conflict, or failure-case material → CHS

For legal and regulatory retrieval:

    FHS > EHS > CHS

EHS and CHS must not override matched FHS evidence.

If a query cannot be grounded in matched FHS evidence, HSRAG should reject, warn, or return a no-evidence decision rather than generate an unsupported legal answer.

This is a retrieval-governance rule, not legal advice.

A longer store-classification document may be added as a separate reference file.

---

## 12. Interpretation

HSRAG LAW is not claiming that lexical retrieval is useless.

Instead, this demo shows that lexical retrieval alone has difficulty distinguishing:

    supported legal query
    unsupported legal query
    ambiguous legal query
    conflict-form legal query
    wrong-corpus retrieval
    wrong-jurisdiction retrieval

HSRAG adds a structured routing layer before retrieval:

    CTHC typed legal address
    + salted domain hash
    + bounded retrieval
    + evidence gate
    + audit chain

This makes the retrieval process more conservative, more auditable, and less prone to cross-domain evidence mixing.

---

## 13. Current limitations

Current limitations:

- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3_FIX2 corpus from raw official source files.
- RQ4.1 uses official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- This demo is not legal advice.
- This demo is a retrieval architecture benchmark, not a legal reasoning benchmark.
- The custom corpus template currently supports clean plaintext / markdown input first.
- Large case-level benchmark outputs may be omitted from Git history to keep the repository lightweight.

---

## 14. Suggested next steps

Planned improvements:

1. Expand the custom-corpus template with stronger manifest validation and multi-file examples.
2. Add full manifest-based corpus ingestion with explicit source license and provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add a longer store-classification reference document.
6. Add a public report summarizing RQ1–RQ5.5.
7. Separate lightweight demo scripts from heavier benchmark artifacts.
8. Improve benchmark artifact packaging and release bundles.
9. Explore larger corpora and additional legal / regulatory domains.

---

## 15. One-line summary

HSRAG LAW demonstrates that **CTHC-typed legal addresses plus salted domain-hash retrieval** can reduce cross-domain legal retrieval risk, reject unsupported / ambiguous / conflict-form queries, preserve auditability, and significantly reduce token cost in a reproducible benchmark setting.
## RQ7 Scale Benchmark

RQ7 compares three retrieval modes:

- mainstream global search
- CTHC-pruned search
- unique address lookup

Current maturity:

- salted toy-real retrieval pipeline: verified
- one-command verify: available
- external chunk registry loader: available
- full-scale RQ7 benchmark: not implemented yet
- official RQ4 corpus loader: not connected yet
- vector / hybrid baselines: not implemented yet

One-command verify:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Expected current result:

    status: OK
    one_command_verify: true
    acceptance_passed: true
    latest_report_is_clean: true

Claim boundary:

RQ7 currently validates pipeline integrity, result contracts, salted-domain routing, artifact generation, and reporting.

It does not claim that HSRAG replaces all RAG systems.
It does not claim full-scale benchmark completion.
It does not provide legal advice.

See:

- `examples/hsrag_law/rq7_scale/README.md`
- `examples/hsrag_law/rq7_scale/README_TESTING.md`
- `examples/hsrag_law/rq7_scale/CLAIM_BOUNDARY.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_LATEST_REPORT.md`


## RQ7 Public Report

RQ7 now has a published public report:

- `rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md`
- `rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json`

Current claim boundary:

- RQ4 rebuilt artifact is connected locally.
- RQ4 scale tiers are available for 100 / 300 / 600 / 889 chunks.
- Actual elapsed timing is reported.
- This is not a full-scale benchmark.
- Vector / hybrid baselines are not implemented yet.
- Unit derivation remains heuristic.
- This is not legal advice.

Recommended verification command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889


## RQ7 Release Checkpoint

RQ7 v0.1 release checkpoint files:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json`

Current claim boundary:

- RQ4 rebuilt 889-chunk artifact connected
- RQ4 metrics snapshot available
- RQ4 scale tiers available: 100 / 300 / 600 / 889
- Actual elapsed timing available
- Full-scale benchmark pending
- Local deterministic vector / hybrid baselines available; production embedding / vector database baselines pending
- Unit derivation remains heuristic
- Not legal advice

Verify:

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889


## RQ7 Full Query Diagnostics

RQ7 full benchmark branch includes a diagnostic report for expanded query seeds:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json`

Current claim boundary:

- Full query expansion is diagnostic-only.
- Acceptance failure is allowed for diagnostics.
- Full-scale benchmark is still pending.
- Local deterministic vector / hybrid baselines are available; production embedding / vector database baselines are still pending.
- This does not provide legal advice.

Run diagnostics:

    python examples/hsrag_law/rq7_scale/scripts/analyze_rq7_full_query_diagnostics.py

Publish diagnostics:

    python examples/hsrag_law/rq7_scale/scripts/publish_rq7_full_query_diagnostics.py


## RQ7 Full Query Triage

RQ7 full benchmark branch includes a triage report for expanded query diagnostics:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.json`

Current triage categories include:

- EXPECTED_GUARD_BLOCK
- FALSE_ALLOW_RISK
- TARGET_BLOCKED
- TARGET_MISMATCH
- ALLOW_MATCHED_TARGET
- ALLOW_NO_TARGET
- OTHER

Current claim boundary:

- Triage is diagnostic-only.
- Acceptance failure is allowed for diagnostics.
- Full-scale benchmark is still pending.
- Local deterministic vector / hybrid baselines are available; production embedding / vector database baselines are still pending.
- This does not provide legal advice.

Build triage report:

    python examples/hsrag_law/rq7_scale/scripts/build_rq7_full_query_triage.py


## RQ7 Synthetic Scale Benchmark

RQ7 full benchmark branch includes a synthetic scale stress benchmark:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.csv`

Current synthetic scale tiers:

- 1,000 chunks
- 5,000 chunks
- 10,000 chunks

Claim boundary:

- Synthetic chunks are explicitly labeled.
- Synthetic expansion is not new legal corpus.
- This is a scale stress benchmark only.
- This is not a full-scale real-law corpus benchmark.
- Local deterministic vector / hybrid baselines are available; production embedding / vector database baselines are still pending.
- This does not provide legal advice.

Run benchmark:

    python examples/hsrag_law/rq7_scale/scripts/run_rq7_synthetic_scale_benchmark.py --target-sizes 1000,5000,10000


## RQ7 Vector Baseline Report

RQ7 vector baseline branch includes a local deterministic vector-style baseline report:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.csv`

Current vector modes:

- VECTOR_GLOBAL
- CTHC_PRUNED_VECTOR

Claim boundary:

- Local deterministic vector-style baseline only.
- No external embedding API.
- No network access required.
- No secrets required.
- Not a state-of-the-art vector search engine.
- Not a production vector database benchmark.
- Hybrid ranking is covered by the RQ7 Hybrid Baseline Report.
- This does not provide legal advice.

Run vector baseline report:

    python examples/hsrag_law/rq7_scale/scripts/build_rq7_vector_baseline_report.py


## RQ7 Hybrid Baseline Report

RQ7 hybrid baseline branch includes a local deterministic hybrid baseline report:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT_SUMMARY.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT.csv`

Current hybrid modes:

- HYBRID_BM25_VECTOR
- CTHC_PRUNED_HYBRID

Claim boundary:

- Local deterministic hybrid baseline only.
- No external embedding API.
- No network access required.
- No secrets required.
- Not a state-of-the-art hybrid search engine.
- Not a production vector database benchmark.
- This does not provide legal advice.

Run hybrid baseline report:

    python examples/hsrag_law/rq7_scale/scripts/build_rq7_hybrid_baseline_report.py


## RQ7 Scope and Key Findings

RQ7 evaluates HSRAG as **Hash-Structured RAG with deterministic addressing**.

RQ7 measures the retrieval, routing, and evidence-selection layer. It does **not** call an LLM, does **not** evaluate LLM reasoning, and does **not** evaluate generated-answer quality.

Current RQ7 results do not primarily show higher target correctness than BM25 / TF-IDF on the current easy query set. They show that deterministic addressing and CTHC-style boundary filtering can preserve correctness while reducing candidate search space, local measured p99 latency, estimated evidence-token cost, and evidence-alignment ambiguity.

Current RQ7 also includes local deterministic vector / hybrid baselines. Production embedding / vector database baselines remain pending.

Detailed explanation:

- `examples/hsrag_law/rq7_scale/RQ7_KEY_FINDINGS_AND_METRICS.md`




