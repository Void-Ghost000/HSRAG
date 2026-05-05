# RQ3 FIX2 Verification Summary

Core decision: `RQ3_FIX2_VERIFICATION_PASS`
Audit chain complete: `1.0`

## RQ3 Purpose

RQ3 verifies the HSRAG LAW EU × US real-law collision benchmark, testing wrong-corpus collision and wrong-jurisdiction escape across multiple legal corpora and jurisdictions.

## FIX2 Jurisdiction Normalization

- fix_label: `FIX2_JURISDICTION_HIERARCHY_NORMALIZATION`
- raw FIX1 wrong_jurisdiction_escape: `0.0033783783783783786`
- FIX2 normalized wrong_jurisdiction_escape: `0.0`

## Benchmark Scope

- semantic label: `REAL_EU_US_PUBLIC_LEGAL_REFERENCE_WITH_OFFICIAL_URLS`
- chunks: `244`
- base queries: `592`
- MC cases: `14208`
- corpora: `6`
- jurisdictions: `3`
- baseline modes: `4`
- fail_count: `0`

## HSRAG Metrics

- target_correct: `1.0`
- wrong_corpus_collision: `0.0`
- wrong_jurisdiction_escape: `0.0`
- no_evidence_false_allow: `0.0`
- ambiguous_false_allow: `0.0`
- mismatch_escape: `0.0`
- audit_chain_complete: `1.0`
- p95_latency_ms: `5.924376599796233`

## Best Baseline Comparison

- target_correct: `0.9079391891891891`
- wrong_corpus_collision: `0.019566441441441443`
- wrong_jurisdiction_escape: `0.01097972972972973`
- no_evidence_false_allow: `0.9666666666666667`
- ambiguous_false_allow: `1.0`
- mismatch_escape: `1.0`
- token_reduction_pct_max: `78.70881065021146`
- cost_reduction_pct_max: `73.55123408683025`
- p95_latency_ms: `6.7050616002234165`

## Gate Summary

- passed gates: `20/20`

## Baseline Details

| mode | target_correct | wrong_corpus_collision | wrong_jurisdiction_escape | p95_latency_ms |
|---|---:|---:|---:|---:|
| bm25_domain_hint_topk | 0.9079391891891891 | 0.019566441441441443 | 0.01097972972972973 | 6.7050616002234165 |
| bm25_global_topk | 0.8760557432432432 | 0.47740709459459457 | 0.03265765765765766 | 7.362108 |
| tfidf_domain_hint_topk | 0.9066019144144144 | 0.02005855855855856 | 0.011050112612612613 | 6.127217 |
| tfidf_global_topk | 0.8669763513513513 | 0.5244228603603603 | 0.04490427927927928 | 6.699384 |

## Notes

- This verifier checks the frozen RQ3 FIX2 benchmark summary.
- It does not re-run the full original MC benchmark package.
- RQ3 FIX2 corrects jurisdiction hierarchy metric semantics.
- Official URL fetch reproducibility should be handled in a separate RQ4 pipeline.
