# V020 Evidence Summary — HSRAG Memory Context Baseline

Generated at UTC: 2026-05-26T14:23:37Z

## Decision

PASS_INTERPRETATION_REPORT

## Experiment Scope

- Version: HSRAG_MEMORY_CONTEXT_BASELINE_V0_2_0
- Memory records: 20
- Query count: 12
- Strategy count: 5
- Evaluator: deterministic
- LLM call: no
- Real personal data: no

## Best-by-category Result

| Category | Strategy | Reason |
|---|---|---|
| Best token cost | C_SUMMARY_MEMORY | 79.92% token reduction vs full raw. |
| Best raw answer completeness | B_TOPK_RAW_CHUNKS | 100.00% expected answer coverage. |
| Best governed balance | E_POINTER_ON_DEMAND_RESOLVE | Zero sensitive leak, zero forbidden leak, full traceability. |

## Core Evidence

| Metric | A Full Raw | B Top-K Raw | C Summary | E Pointer Resolve |
|---|---:|---:|---:|---:|
| Token reduction vs full raw | 0.00% | 72.45% | 79.92% | 69.23% |
| Answer expected coverage | 100.00% | 100.00% | 66.67% | 100.00% |
| Sensitive leak rate | 19.58% | 12.50% | 12.50% | 0.00% |
| Forbidden leak count | 27 | 4 | 4 | 0 |
| Traceability | 0.00% | 100.00% | 100.00% | 100.00% |
| Source hash presence | 0.00% | 0.00% | 0.00% | 100.00% |
| Pointer presence | 0.00% | 0.00% | 0.00% | 100.00% |
| P99 local latency | 0.0704 ms | 3.5722 ms | 5.9573 ms | 30.5985 ms |

## Interpretation

The v0.2.0 result separates raw answer correctness from governed usefulness.

Full raw context and top-k raw chunks can answer correctly, but they expose irrelevant and sensitive memory. Summary memory is cheaper, but loses detail. Pointer metadata is traceable, but short-record metadata overhead is high. Pointer on-demand resolve is not the cheapest or fastest, but it is the only strategy in this run that combines complete expected answers with zero sensitive or forbidden leakage and full pointer/source-hash traceability.

## Report-safe Claim

In a deterministic synthetic v0.2.0 memory-context baseline with 20 memory records and 12 queries, Pointer On-Demand Resolve preserved expected answer coverage while achieving zero forbidden-memory leaks, zero unexpected high-sensitivity leaks, and full pointer/source-hash traceability. This does not measure real LLM answer quality.

## Known Limits

- Synthetic data only.
- Deterministic evaluator only.
- No real LLM answer quality is measured.
- Token count is character-estimated.
- Local latency only.
- Content guard is placeholder logic.
- This benchmark does not prove GDPR compliance.
