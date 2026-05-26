# HSRAG Memory Context v0.2.1 — Evidence Summary

## Decision

- Freeze: FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE
- Source benchmark: PASS_SCALE_BENCHMARK_RUNNER

## Scope

Synthetic deterministic memory-context scale benchmark.

This benchmark compares five memory context construction strategies across 1k, 10k, 50k, and 100k synthetic memories.

## Compared Strategies

- A_FULL_RAW_CONTEXT
- B_TOPK_RAW_CHUNKS
- C_SUMMARY_MEMORY
- D_POINTER_METADATA_ONLY
- E_POINTER_ON_DEMAND_RESOLVE

## 100k Highlight — E_POINTER_ON_DEMAND_RESOLVE

| Metric | Value |
|---|---:|
| Token reduction vs full raw context | 99.9941% |
| P50 local context construction latency | 0.0981 ms |
| P95 local context construction latency | 0.161835 ms |
| P99 local context construction latency | 0.20809 ms |
| Answer coverage | 1 |
| Sensitive memory leak rate | 0 |
| Traceability rate | 1 |

## Artifacts

- V021_FREEZE_SUMMARY.md
- reports/v021_scale_public_summary.md
- reports/v021_scale_benchmark_report.md
- outputs/v021_scale_final_summary.json
- outputs/v021_scale_metrics_summary.csv
- outputs/v021_scale_strategy_results.csv

## Claim Boundary

- Synthetic only.
- No real LLM call.
- No real personal data.
- Local latency measures context construction only, not model inference.
- This does not prove GDPR compliance.
- Pointer on-demand resolve is evaluated as a context construction strategy, not a full product.

## Known Limits

- Exact memory hit is not optimized in v0.2.1.
- Dataset is synthetic and topic-structured.
- Evaluator checks deterministic answer coverage, not real LLM answer quality.
- Future work should add noisy query, semantic retrieval, real LLM evaluation, and exact-memory calibration.

