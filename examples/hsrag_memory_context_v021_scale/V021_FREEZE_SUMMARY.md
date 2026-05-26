# HSRAG Memory Context Scale Baseline v0.2.1 — Freeze Summary

## Freeze Decision

FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE

## Scope

Synthetic deterministic benchmark for comparing memory-context construction strategies.

No real LLM call. No real personal data. No GDPR claim.

## Strategies Compared

- A_FULL_RAW_CONTEXT
- B_TOPK_RAW_CHUNKS
- C_SUMMARY_MEMORY
- D_POINTER_METADATA_ONLY
- E_POINTER_ON_DEMAND_RESOLVE

## Scale

- 1,000 memories
- 10,000 memories
- 50,000 memories
- 100,000 memories

## 100k Highlight — E_POINTER_ON_DEMAND_RESOLVE

| Metric | Value |
|---|---:|
| Token reduction vs full raw | 99.9941% |
| P50 local construction latency | 0.0981 ms |
| P95 local construction latency | 0.161835 ms |
| P99 local construction latency | 0.20809 ms |
| Answer coverage | 1.0 |
| Sensitive memory leak rate | 0.0 |
| Traceability rate | 1.0 |

## 100k Strategy Comparison

| Strategy | Token reduction avg | P50 ms | P95 ms | P99 ms | Answer rate | Sensitive leak avg | Traceability |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_FULL_RAW_CONTEXT | 0.0% | 17.8454 | 22.397015 | 27.949807 | 1.0 | 0.225 | 0.0 |
| B_TOPK_RAW_CHUNKS | 99.9986% | 0.1275 | 0.181985 | 0.208256 | 0.85 | 0.114 | 0.0 |
| C_SUMMARY_MEMORY | 99.9953% | 0.14145 | 0.222245 | 0.25874 | 0.86 | 0.142 | 0.0 |
| D_POINTER_METADATA_ONLY | 99.9873% | 0.2085 | 0.307005 | 0.429486 | 0.86 | 0.142 | 1.0 |
| E_POINTER_ON_DEMAND_RESOLVE | 99.9941% | 0.0981 | 0.161835 | 0.20809 | 1.0 | 0.0 | 1.0 |

## Acceptance Gates

- accuracy_present: True
- all_scales_executed: True
- five_strategies_executed: True
- latency_present: True
- leakage_present: True
- max_n_is_100000: True
- memory_footprint_present: True
- pointer_resolve_answer_rate_100k_is_1: True
- pointer_resolve_sensitive_leak_100k_is_0: True
- pointer_resolve_traceability_100k_is_1: True
- result_rows_present: True
- token_cost_present: True
- traceability_present: True

## Claim Boundary

- Synthetic deterministic benchmark only.
- No real LLM call.
- No real personal data.
- Latency measures local context construction only, not model inference.
- This does not prove GDPR compliance.
- Pointer on-demand resolve is evaluated as a context construction strategy, not as a full product.

## Known Limits

- Exact memory hit is not optimized in v0.2.1.
- Dataset is synthetic and topic-structured.
- Evaluator checks deterministic answer coverage, not real model answer quality.
- Future work should add noisy query, semantic retrieval, real LLM evaluation, and exact-memory calibration.

## Next Steps

- v0.2.2 exact-memory retrieval calibration.
- v0.2.3 noisy query / adversarial memory benchmark.
- v0.2.4 optional real LLM answer-quality evaluation.
- Later product line: local SQLite memory pointer SDK or VSCode/plugin wrapper.
