# HSRAG LAW Unified Verification Index

Final decision: `HSRAG_LAW_VERIFICATION_INDEX_PASS`
Unified audit chain complete: `1.0`

## Included Verifiers

| RQ | Role | Core decision | Audit chain | Return code |
|---|---|---|---:|---:|
| RQ1 | Publication-grade real corpus gate | `RQ1_VERIFICATION_PASS` | `1.0` | `0` |
| RQ2.2 | Real EU Law + four baselines + 10k MC | `RQ2_2_VERIFICATION_PASS` | `1.0` | `0` |
| RQ3_FIX2 | EU × US real-law collision benchmark | `RQ3_FIX2_VERIFICATION_PASS` | `1.0` | `0` |

## Key Metrics

### RQ1 — Publication-grade real corpus gate

- decision: `RQ1_PUBLICATION_GRADE_PASS`
- real_primary_corpus_rate: `1.0`
- real_primary_chunk_rate: `1.0`
- source_hash_final_present_rate: `1.0`
- primary_real_rows: `1211`
- primary_real_target_correct_rate: `1.0`
- primary_real_wrong_collision_rate: `0.0`
- fail_count: `0`
- warn_count: `0`
- mc_scope_decision: `MC_NOT_REQUIRED_FOR_RQ1_PASS`
- url_fetch_decision: `FETCH_SKIPPED`

### RQ2.2 — Real EU Law + four baselines + 10k MC

- decision: `RQ2_2_FOUR_BASELINES_10KMC_PASS`
- chunks: `188`
- base_queries: `424`
- mc_cases: `10176`
- baseline_modes: `4`
- hsrag_target_correct: `1.0`
- hsrag_wrong_collision: `0.0`
- hsrag_no_evidence_false_allow: `0.0`
- hsrag_ambiguous_false_allow: `0.0`
- hsrag_mismatch_escape: `0.0`
- hsrag_p95_latency_ms: `4.03891924997879`
- best_baseline_target_correct: `0.9391705974842768`
- best_baseline_wrong_collision: `0.0376375786163522`
- token_reduction_pct_max: `78.26886681010008`
- cost_reduction_pct_max: `73.33315332219127`

### RQ3_FIX2 — EU × US real-law collision benchmark

- decision: `RQ3_EU_US_REALLAW_COLLISION_PASS`
- chunks: `244`
- base_queries: `592`
- mc_cases: `14208`
- corpora: `6`
- jurisdictions: `3`
- baseline_modes: `4`
- raw_fix1_wrong_jurisdiction_escape: `0.0033783783783783786`
- fix2_normalized_wrong_jurisdiction_escape: `0.0`
- hsrag_target_correct: `1.0`
- hsrag_wrong_corpus_collision: `0.0`
- hsrag_wrong_jurisdiction_escape: `0.0`
- hsrag_no_evidence_false_allow: `0.0`
- hsrag_ambiguous_false_allow: `0.0`
- hsrag_mismatch_escape: `0.0`
- hsrag_p95_latency_ms: `5.924376599796233`
- best_baseline_target_correct: `0.9079391891891891`
- best_baseline_wrong_corpus_collision: `0.019566441441441443`
- best_baseline_wrong_jurisdiction_escape: `0.01097972972972973`
- token_reduction_pct_max: `78.70881065021146`
- cost_reduction_pct_max: `73.55123408683025`

## Notes

- This index runs the public frozen-result verifiers for RQ1, RQ2.2, and RQ3 FIX2.
- It does not re-run the full original MC benchmark packages.
- RQ1 URL fetch is skipped by default for deterministic verification.
- Official-source rebuilding is planned as a separate RQ4 pipeline.
- MC mutation reproduction is planned as a separate RQ5 pipeline.
