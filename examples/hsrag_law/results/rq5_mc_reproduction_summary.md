# RQ5.5 CTHC-Typed Salted Domain Routing Robustness Summary

Core decision: `RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_PASS`
Case audit chain complete: `1.0`
Summary audit chain complete: `1.0`

## Config
- cases: `10000`
- seed: `20260505`
- top_k: `5`
- max_chunks_per_corpus: `80`
- min_cases: `10000`
- cost_per_1k: `0.0001`
- max_p95_latency_ms: `20.0`
- benchmark_salt: `HSRAG_LAW_RQ5_5_PUBLIC_REPRODUCIBLE_SALT_v1`
- elapsed_ms_total: `9838.736600009724`

## Corpus Summary
- corpus_source: `rq4_rebuilt_chunks`
- chunk_count: `110`
- corpus_count: `5`
- corpora: `EU_AI_ACT|EU_DMA|US_CDA230|US_COPPA|US_FTC_ACT5`
- jurisdiction_count: `2`
- jurisdictions: `EU|US`
- domain_hash_count: `5`

## HSRAG Metrics
- target_cases: `5500`
- unsupported_query_cases: `1500`
- ambiguous_query_cases: `1500`
- conflict_query_cases: `1500`
- target_correct: `1.0`
- wrong_corpus_misrouting: `0.0`
- wrong_jurisdiction_misrouting: `0.0`
- unsupported_query_false_allow: `0.0`
- ambiguous_query_false_allow: `0.0`
- conflict_query_false_allow: `0.0`
- p50_latency_ms: `0.3155999584123492`
- p95_latency_ms: `0.5798799917101849`
- total_tokens: `1429788`
- avg_tokens: `142.9788`
- total_cost: `0.14297880000000002`
- avg_cost: `1.4297880000000001e-05`

## Global Lexical Baseline
- mode: `global`
- target_correct: `0.9163636363636364`
- wrong_corpus_misrouting: `0.08363636363636363`
- wrong_jurisdiction_misrouting: `0.0`
- unsupported_query_false_allow: `1.0`
- ambiguous_query_false_allow: `1.0`
- conflict_query_false_allow: `1.0`
- p50_latency_ms: `0.1425000373274088`
- p95_latency_ms: `0.2655000425875187`
- total_tokens: `10044275`
- avg_tokens: `1004.4275`
- total_cost: `1.0044275`
- avg_cost: `0.00010044275`

## Domain-Hint Lexical Baseline
- mode: `domain_hint`
- target_correct: `1.0`
- wrong_corpus_misrouting: `0.0`
- wrong_jurisdiction_misrouting: `0.0`
- unsupported_query_false_allow: `1.0`
- ambiguous_query_false_allow: `1.0`
- conflict_query_false_allow: `1.0`
- p50_latency_ms: `0.3446500049903989`
- p95_latency_ms: `0.7112148334272204`
- total_tokens: `10050364`
- avg_tokens: `1005.0364`
- total_cost: `1.0050364`
- avg_cost: `0.00010050364`

## Baseline Comparison

| baseline | token_reduction_pct | cost_reduction_pct | p95_latency_ratio |
|---|---:|---:|---:|
| global | 85.76514482130368 | 85.76514482130368 | 0.4578534289560581 |
| domain_hint | 85.77376898985946 | 85.77376898985946 | 1.2264862447309177 |

## Gate Checks

| gate_id | passed | expected | actual | severity |
|---|---:|---|---|---|
| RQ5_MC_CASES_MINIMUM | `True` | `>= 10000` | `10000` | `HARD` |
| HSRAG_TARGET_CORRECT | `True` | `>= 0.995` | `1.0` | `HARD` |
| HSRAG_WRONG_CORPUS_MISROUTING_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_WRONG_JURISDICTION_MISROUTING_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_UNSUPPORTED_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_AMBIGUOUS_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_CONFLICT_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_AUDIT_CHAIN_COMPLETE | `True` | `1.0` | `1.0` | `HARD` |
| HSRAG_P95_LATENCY_BOUND | `True` | `< 20.0 ms` | `0.5798799917101849` | `HARD` |
| BASELINE_FALSE_ALLOW_PRESENT | `True` | `> 0` | `1.0` | `SOFT` |

## Notes

- This is a live benchmark, not a frozen-result verifier.
- Routing does not read case_type.
- Query routing emits a CTHCRoute object.
- Retrieval only uses chunks in the matching salted domain_hash bucket.
- Strict acceptance gates are preserved.
- Generic legal words cannot open a corpus route.
- RQ5.5 adds structured U.S.C. citation fragment recovery.
