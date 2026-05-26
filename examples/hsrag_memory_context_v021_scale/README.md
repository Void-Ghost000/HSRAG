# HSRAG Memory Context Scale Baseline v0.2.1

This experiment scales the v0.2.0 memory-context baseline from small deterministic data to larger synthetic memory sets.

## Goal

Compare five memory-context strategies across increasing memory scale:

- A_FULL_RAW_CONTEXT
- B_TOPK_RAW_CHUNKS
- C_SUMMARY_MEMORY
- D_POINTER_METADATA_ONLY
- E_POINTER_ON_DEMAND_RESOLVE

## Required Metrics

- token cost / token reduction
- local construction latency P50 / P95 / P99
- retrieval accuracy
- answer expected coverage
- sensitive / forbidden memory leakage
- traceability
- memory footprint

## Planned Scale

- 1,000 memories
- 10,000 memories
- 50,000 memories
- 100,000 memories

## Boundary

Synthetic deterministic benchmark only.

No real LLM call.

No real personal data.

No GDPR claim.

<!-- V021_RESULTS_START -->

## Frozen v0.2.1 Scale Baseline

v0.2.1 is frozen as a synthetic deterministic memory-context scale benchmark.

At 100k synthetic memories, E_POINTER_ON_DEMAND_RESOLVE achieved:

- Token reduction vs full raw context: 99.9941%
- P99 local context construction latency: 0.20809 ms
- Answer coverage: 1
- Sensitive memory leak rate: 0
- Traceability rate: 1

Evidence files:

- V021_EVIDENCE_SUMMARY.md
- V021_FREEZE_SUMMARY.md
- reports/v021_scale_public_summary.md

<!-- V021_RESULTS_END -->

