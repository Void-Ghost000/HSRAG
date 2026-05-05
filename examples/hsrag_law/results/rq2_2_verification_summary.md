# RQ2.2 Verification Summary

Core decision: `RQ2_2_VERIFICATION_PASS`
Audit chain complete: `1.0`

## RQ2.2 Purpose

RQ2.2 verifies the HSRAG LAW Real EU Law benchmark with four lexical baselines and 10k+ Monte Carlo mutation cases.

## Benchmark Scope

- semantic label: `REAL_UPLOADED_PDF_WITH_OFFICIAL_REFERENCE`
- chunks: `188`
- base queries: `424`
- MC seeds: `24`
- MC cases: `10176`
- baseline modes: `4`
- fail_count: `0`

## HSRAG Metrics

- target_correct: `1.0`
- wrong_collision: `0.0`
- no_evidence_false_allow: `0.0`
- ambiguous_false_allow: `0.0`
- mismatch_escape: `0.0`
- audit_chain_complete: `1.0`
- p95_latency_ms: `4.03891924997879`

## Best Baseline Comparison

- target_correct: `0.9391705974842768`
- wrong_collision: `0.0376375786163522`
- no_evidence_false_allow: `1.0`
- ambiguous_false_allow: `1.0`
- mismatch_escape: `1.0`
- token_reduction_pct_max: `78.26886681010008`
- cost_reduction_pct_max: `73.33315332219127`
- p95_latency_ms: `6.851546500001859`

## Gate Summary

- passed gates: `15/15`

## Baseline Details

| mode | target_correct | wrong_collision | p95_latency_ms |
|---|---:|---:|---:|
| bm25_domain_hint_topk | 0.9391705974842768 | 0.0376375786163522 | 6.851546500001859 |
| bm25_global_topk | 0.9300314465408805 | 0.5593553459119497 | 10.713801 |
| tfidf_domain_hint_topk | 0.9387775157232704 | 0.03803066037735849 | 6.419456 |
| tfidf_global_topk | 0.9216776729559748 | 0.5677083333333334 | 6.708151 |

## Notes

- This verifier checks the frozen RQ2.2 benchmark summary.
- It does not re-run the full original MC benchmark package.
- RQ2.2 uses real uploaded EU legal PDFs with official references.
- Official URL fetch reproducibility should be handled in a separate RQ4 pipeline.
