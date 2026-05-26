# HSRAG Memory Context Baseline v0.2.0

Deterministic benchmark for comparing memory-context injection strategies.

## Purpose

This experiment compares whether different memory feeding strategies are cheaper, safer, more traceable, or more answer-complete.

This is not a production memory system. It does not call a real LLM.

## Strategies Tested

1. A_FULL_RAW_CONTEXT
2. B_TOPK_RAW_CHUNKS
3. C_SUMMARY_MEMORY
4. D_POINTER_METADATA_ONLY
5. E_POINTER_ON_DEMAND_RESOLVE

## Current Decision

PASS_INTERPRETATION_REPORT

## Main Finding

E_POINTER_ON_DEMAND_RESOLVE is the best governed balance in this deterministic run.

Key result:

- Answer expected coverage: 100.00%
- Sensitive memory leak rate: 0.00%
- Forbidden memory leak count: 0
- Traceability rate: 100.00%
- Source hash presence: 100.00%
- Pointer presence: 100.00%
- Token reduction vs full raw: 69.23%
- P99 local construction latency: 30.5985 ms

## Metric Summary

| Strategy | Token Reduction | Answer Rate | Sensitive Leak | Forbidden Leaks | Traceability | P99 Local Latency |
|---|---:|---:|---:|---:|---:|---:|
| `A_FULL_RAW_CONTEXT` | 0.00% | 100.00% | 19.58% | 27 | 0.00% | 0.0704 ms |
| `B_TOPK_RAW_CHUNKS` | 72.45% | 100.00% | 12.50% | 4 | 100.00% | 3.5722 ms |
| `C_SUMMARY_MEMORY` | 79.92% | 66.67% | 12.50% | 4 | 100.00% | 5.9573 ms |
| `D_POINTER_METADATA_ONLY` | 40.75% | 66.67% | 12.50% | 4 | 100.00% | 5.2279 ms |
| `E_POINTER_ON_DEMAND_RESOLVE` | 69.23% | 100.00% | 0.00% | 0 | 100.00% | 30.5985 ms |

## Output Files

- data/memory_items.jsonl
- data/queries.jsonl
- outputs/hsrag_memory_context_v020_strategy_results.csv
- outputs/hsrag_memory_context_v020_metrics_summary.csv
- outputs/hsrag_memory_context_v020_final_summary.json
- outputs/hsrag_memory_context_v020_interpretation_summary.json
- reports/hsrag_memory_context_v020_report.md
- reports/hsrag_memory_context_v020_interpretation_report.md
- V020_EVIDENCE_SUMMARY.md
- README_TESTING.md

## Reproduction Commands

Run from repository root:

- Set base path: `$base = "examples/hsrag_memory_context_v020"`
- Generate dataset: `python "$base/make_v020_dataset.py"`
- Run baselines: `python "$base/run_v020_baselines.py"`
- Generate interpretation: `python "$base/interpret_v020_results.py"`

## Boundaries

- Synthetic data only.
- Deterministic evaluator only.
- Token count is character-estimated, not tokenizer-verified.
- Local latency only; no real LLM latency.
- Content guard is placeholder logic, not production privacy protection.
- This benchmark does not prove GDPR compliance.

Generated at UTC: 2026-05-26T14:23:37Z
