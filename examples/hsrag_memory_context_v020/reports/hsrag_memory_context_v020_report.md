# HSRAG Memory Context Baseline v0.2.0 Report

Run timestamp UTC: `2026-05-26T13:45:03Z`

## Scope

- Synthetic data only
- Deterministic evaluator only
- No real LLM call
- No external API
- No real personal data

## Strategies

- `A_FULL_RAW_CONTEXT`
- `B_TOPK_RAW_CHUNKS`
- `C_SUMMARY_MEMORY`
- `D_POINTER_METADATA_ONLY`
- `E_POINTER_ON_DEMAND_RESOLVE`

## Metric Summary

| strategy | token_reduction_vs_full_raw_avg_pct | latency_ms_p50 | latency_ms_p95 | latency_ms_p99 | accuracy_retrieved_correct_rate | answer_contains_expected_rate | sensitive_memory_leak_rate_per_released | forbidden_memory_leak_count | traceability_rate | runtime_peak_memory_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_FULL_RAW_CONTEXT | 0.0 | 0.0125 | 0.052855 | 0.070411 | 1 | 1 | 0.195833 | 27 | 0 | 27124 |
| B_TOPK_RAW_CHUNKS | 72.45 | 1.796 | 3.45791 | 3.572222 | 1 | 1 | 0.125 | 4 | 1 | 19779 |
| C_SUMMARY_MEMORY | 79.9167 | 1.68415 | 5.00859 | 5.957318 | 1 | 0.666667 | 0.125 | 4 | 1 | 17563 |
| D_POINTER_METADATA_ONLY | 40.75 | 1.548 | 4.096935 | 5.227867 | 1 | 0.666667 | 0.125 | 4 | 1 | 17883 |
| E_POINTER_ON_DEMAND_RESOLVE | 69.2333 | 3.8136 | 22.300265 | 30.598533 | 1 | 1 | 0.0 | 0 | 1 | 18654 |

## Interpretation

- Full raw context is the cost and leakage baseline.
- Pointer metadata and pointer resolve should reduce context size and improve traceability.
- Pointer resolve should be evaluated as a selective disclosure strategy, not as a production privacy guarantee.

## Known Limits

- Token count is estimated by character length, not a model tokenizer.
- Latency measures local strategy construction only, not LLM latency.
- Accuracy is deterministic evidence availability, not real natural-language answer quality.
- Content guard is a placeholder rule, not a production classifier.
