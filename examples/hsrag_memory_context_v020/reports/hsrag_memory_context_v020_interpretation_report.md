# HSRAG Memory Context Baseline v0.2.0 — Interpretation Report

Generated at UTC: `2026-05-26T13:51:21Z`

## Decision

`PASS_INTERPRETATION_REPORT`

## Headline

Pointer on-demand resolve is the best governed strategy in this deterministic run: it preserves answer completeness while achieving zero sensitive leakage, zero forbidden leakage, and full pointer/source-hash traceability. Summary memory is cheaper, but loses expected answer details.

## Best Strategy by Category

| Category | Strategy | Reason |
|---|---|---|
| Best token cost | `C_SUMMARY_MEMORY` | Highest token reduction vs full raw: 79.92%. |
| Best answer completeness | `B_TOPK_RAW_CHUNKS` | Answer contains expected rate: 100.00%. |
| Best traceability | `E_POINTER_ON_DEMAND_RESOLVE` | Highest combined traceability/source_hash/pointer presence. |
| Best governed balance | `E_POINTER_ON_DEMAND_RESOLVE` | Best composite governance score across answer completeness, leakage, traceability, and token reduction. |

## Core Metric Table

| strategy | token_reduction | p50 | p95 | p99 | answer_rate | sensitive_leak | forbidden_leaks | traceability | source_hash | pointer | governed_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A_FULL_RAW_CONTEXT` | 0.00% | 0.0125 ms | 0.0529 ms | 0.0704 ms | 100.00% | 19.58% | 27 | 0.00% | 0.00% | 0.00% | 0.463507 |
| `B_TOPK_RAW_CHUNKS` | 72.45% | 1.7960 ms | 3.4579 ms | 3.5722 ms | 100.00% | 12.50% | 4 | 100.00% | 0.00% | 0.00% | 0.725536 |
| `C_SUMMARY_MEMORY` | 79.92% | 1.6842 ms | 5.0086 ms | 5.9573 ms | 66.67% | 12.50% | 4 | 100.00% | 0.00% | 0.00% | 0.662904 |
| `D_POINTER_METADATA_ONLY` | 40.75% | 1.5480 ms | 4.0969 ms | 5.2279 ms | 66.67% | 12.50% | 4 | 100.00% | 100.00% | 100.00% | 0.765852 |
| `E_POINTER_ON_DEMAND_RESOLVE` | 69.23% | 3.8136 ms | 22.3003 ms | 30.5985 ms | 100.00% | 0.00% | 0 | 100.00% | 100.00% | 100.00% | 0.933477 |

## Governed Score Ranking

| Rank | Strategy | Governed Score | Interpretation |
|---:|---|---:|---|
| 1 | `E_POINTER_ON_DEMAND_RESOLVE` | 0.933477 | Best governed balance: correct, traceable, zero sensitive leak, zero forbidden leak. Moderate token reduction. Traceability present. Tail latency needs optimization. |
| 2 | `D_POINTER_METADATA_ONLY` | 0.765852 | Strong traceability, but metadata overhead dominates short records and answer completeness drops. Moderate token reduction. Not all expected answer terms are preserved. Leakage risk remains. Traceability present. |
| 3 | `B_TOPK_RAW_CHUNKS` | 0.725536 | Strong cost reduction, but raw chunks can still leak irrelevant or sensitive memories. High token reduction. Leakage risk remains. Traceability present. |
| 4 | `C_SUMMARY_MEMORY` | 0.662904 | Best compression in this run, but answer completeness drops due to summary detail loss. High token reduction. Not all expected answer terms are preserved. Leakage risk remains. Traceability present. |
| 5 | `A_FULL_RAW_CONTEXT` | 0.463507 | Cost/leakage baseline; answers correctly because all memory is exposed. Low token reduction. Leakage risk remains. |

## Main Trade-off

The experiment separates raw accuracy from governed usefulness. Full raw context and top-k raw chunks can answer correctly, but they expose irrelevant and sensitive memory. Summary memory is cheaper, but loses detail. Pointer metadata is traceable, but metadata overhead is large for short records. Pointer on-demand resolve is not the cheapest or fastest, but it is the only strategy in this run that combines complete expected answers with zero sensitive/forbidden leakage and full pointer/source-hash traceability.

## Report-Safe Public Claim

> In a deterministic synthetic v0.2.0 memory-context baseline with 20 memory records and 12 queries, Pointer On-Demand Resolve preserved expected answer coverage while achieving zero forbidden-memory leaks, zero unexpected high-sensitivity leaks, and full pointer/source-hash traceability. This does not measure real LLM answer quality.

## Known Limits

- Synthetic data only; not real personal data.
- Deterministic evaluator only; no real LLM answer quality is measured.
- Token count is estimated by character length, not a model tokenizer.
- Latency measures local strategy construction only, not LLM latency.
- Dataset is intentionally small; results are not scale evidence yet.
- Governed score is an interpretation helper, not a formal metric.
- Content guard is placeholder logic, not production privacy protection.

## Acceptance Gates

| Gate | Pass |
|---|---:|
| `loaded_5_strategy_rows` | `True` |
| `baseline_runner_passed` | `True` |
| `best_governed_strategy_identified` | `True` |
| `pointer_resolve_clean_governance_pass` | `True` |
| `known_limits_declared` | `True` |
| `public_claim_is_bounded` | `True` |
