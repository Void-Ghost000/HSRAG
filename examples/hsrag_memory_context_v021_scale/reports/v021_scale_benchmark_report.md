# HSRAG Memory Context Scale Benchmark v0.2.1

Generated at UTC: 2026-05-26T15:41:58Z

## Decision

PASS_SCALE_BENCHMARK_RUNNER

## Scope

Synthetic deterministic benchmark. No real LLM call. No real personal data.

## 100k Highlight

| Strategy | Token Reduction Avg | P50 ms | P95 ms | P99 ms | Answer Rate | Sensitive Leak Avg | Traceability |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_FULL_RAW_CONTEXT | 0.0% | 17.8454 | 22.397015 | 27.949807 | 1.0 | 0.225 | 0.0 |
| B_TOPK_RAW_CHUNKS | 99.9986% | 0.1275 | 0.181985 | 0.208256 | 0.85 | 0.114 | 0.0 |
| C_SUMMARY_MEMORY | 99.9953% | 0.14145 | 0.222245 | 0.25874 | 0.86 | 0.142 | 0.0 |
| D_POINTER_METADATA_ONLY | 99.9873% | 0.2085 | 0.307005 | 0.429486 | 0.86 | 0.142 | 1.0 |
| E_POINTER_ON_DEMAND_RESOLVE | 99.9941% | 0.0981 | 0.161835 | 0.20809 | 1.0 | 0.0 | 1.0 |

## Interpretation

- Full raw context has maximal information exposure and very high memory footprint.
- Top-k raw and summary approaches reduce context size but provide weaker traceability.
- Pointer metadata and pointer on-demand resolve preserve traceability.
- Pointer on-demand resolve applies FHS/high-sensitive guard before raw memory release.

## Known Limits

- Synthetic only.
- Deterministic evaluator only.
- No real LLM answer quality judgment.
- No GDPR claim.
- Local latency measures context construction only, not model inference.
