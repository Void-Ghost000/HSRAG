# RQ5.5 CTHC-Typed Salted Domain Routing Robustness Summary

Core decision: `RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_PASS`
Case audit chain complete: `1.0`
Summary audit chain complete: `1.0`

## Config
- cases: `50000`
- seed: `20260505`
- top_k: `5`
- max_chunks_per_corpus: `80`
- min_cases: `10000`
- cost_per_1k: `0.0001`
- max_p95_latency_ms: `20.0`
- benchmark_salt: `HSRAG_LAW_RQ5_5_PUBLIC_REPRODUCIBLE_SALT_v1`
- elapsed_ms_total: `69809.8601999227`

## Corpus Summary
- corpus_source: `rq4_rebuilt_chunks`
- chunk_count: `257`
- corpus_count: `5`
- corpora: `EU_AI_ACT|EU_DMA|US_CDA230|US_COPPA|US_FTC_ACT5`
- jurisdiction_count: `2`
- jurisdictions: `EU|US`
- domain_hash_count: `5`

## HSRAG Metrics
- target_cases: `27500`
- unsupported_query_cases: `7500`
- ambiguous_query_cases: `7500`
- conflict_query_cases: `7500`
- target_correct: `1.0`
- wrong_corpus_misrouting: `0.0`
- wrong_jurisdiction_misrouting: `0.0`
- unsupported_query_false_allow: `0.0`
- ambiguous_query_false_allow: `0.0`
- conflict_query_false_allow: `0.0`
- p50_latency_ms: `0.3637999761849642`
- p95_latency_ms: `0.6840050802566107`
- total_tokens: `7187467`
- avg_tokens: `143.74934`
- total_cost: `0.7187467000000001`
- avg_cost: `1.4374934e-05`

## Global Lexical Baseline
- mode: `global`
- target_correct: `0.9247636363636363`
- wrong_corpus_misrouting: `0.07523636363636364`
- wrong_jurisdiction_misrouting: `0.0017454545454545455`
- unsupported_query_false_allow: `1.0`
- ambiguous_query_false_allow: `1.0`
- conflict_query_false_allow: `1.0`
- p50_latency_ms: `0.3564499784260988`
- p95_latency_ms: `0.6506100646220139`
- total_tokens: `50038521`
- avg_tokens: `1000.77042`
- total_cost: `5.0038521000000005`
- avg_cost: `0.000100077042`

## Domain-Hint Lexical Baseline
- mode: `domain_hint`
- target_correct: `1.0`
- wrong_corpus_misrouting: `0.0`
- wrong_jurisdiction_misrouting: `0.0`
- unsupported_query_false_allow: `1.0`
- ambiguous_query_false_allow: `1.0`
- conflict_query_false_allow: `1.0`
- p50_latency_ms: `0.4635999212041497`
- p95_latency_ms: `0.9535099263302973`
- total_tokens: `50111587`
- avg_tokens: `1002.23174`
- total_cost: `5.0111587`
- avg_cost: `0.000100223174`

## Baseline Comparison

| baseline | token_reduction_pct | cost_reduction_pct | p95_latency_ratio |
|---|---:|---:|---:|
| global | 85.63613221102199 | 85.63613221102199 | 0.9511772403472963 |
| domain_hint | 85.65707567792654 | 85.65707567792654 | 1.3940100064353023 |

## Gate Checks

| gate_id | passed | expected | actual | severity |
|---|---:|---|---|---|
| RQ5_MC_CASES_MINIMUM | `True` | `>= 10000` | `50000` | `HARD` |
| HSRAG_TARGET_CORRECT | `True` | `>= 0.995` | `1.0` | `HARD` |
| HSRAG_WRONG_CORPUS_MISROUTING_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_WRONG_JURISDICTION_MISROUTING_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_UNSUPPORTED_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_AMBIGUOUS_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_CONFLICT_QUERY_FALSE_ALLOW_ZERO | `True` | `0.0` | `0.0` | `HARD` |
| HSRAG_AUDIT_CHAIN_COMPLETE | `True` | `1.0` | `1.0` | `HARD` |
| HSRAG_P95_LATENCY_BOUND | `True` | `< 20.0 ms` | `0.6840050802566107` | `HARD` |
| BASELINE_FALSE_ALLOW_PRESENT | `True` | `> 0` | `1.0` | `SOFT` |

## Notes

- This is a live benchmark, not a frozen-result verifier.
- Routing does not read case_type.
- Query routing emits a CTHCRoute object.
- Retrieval only uses chunks in the matching salted domain_hash bucket.
- Strict acceptance gates are preserved.
- Generic legal words cannot open a corpus route.
- RQ5.5 adds structured U.S.C. citation fragment recovery.
