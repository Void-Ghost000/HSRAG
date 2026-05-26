# HSRAG Memory Context Scale Baseline v0.2.1 — Release Note

## Status

Verified prototype baseline.

## What this release tests

v0.2.1 is a synthetic deterministic benchmark for comparing memory-context construction strategies at increasing memory scale.

It compares five strategies:

- A_FULL_RAW_CONTEXT
- B_TOPK_RAW_CHUNKS
- C_SUMMARY_MEMORY
- D_POINTER_METADATA_ONLY
- E_POINTER_ON_DEMAND_RESOLVE

The benchmark runs across:

- 1,000 synthetic memories
- 10,000 synthetic memories
- 50,000 synthetic memories
- 100,000 synthetic memories

## Main 100k result

For E_POINTER_ON_DEMAND_RESOLVE at 100k synthetic memories:

| Metric | Value |
|---|---:|
| Token reduction vs full raw context | 99.9941% |
| P50 local context construction latency | 0.0981 ms |
| P95 local context construction latency | 0.161835 ms |
| P99 local context construction latency | 0.20809 ms |
| Answer coverage | 1 |
| Sensitive memory leak rate | 0 |
| Traceability rate | 1 |

## Interpretation

The result suggests that pointer-based memory context can separate addressing, selective disclosure, and traceability instead of always sending large raw memory payloads into the model context.

In this benchmark, the pointer on-demand strategy stayed very small, remained traceable, and blocked FHS/high-sensitive memory from raw release.

## Important boundary

This release does not claim production readiness.

It does not use real personal data.

It does not call a real LLM.

It does not prove GDPR compliance.

Latency measures local context construction only, not model inference latency.

## Verification

Fast verification command:

powershell -ExecutionPolicy Bypass -File examples/hsrag_memory_context_v021_scale/verify_v021.ps1 -Mode fast

Expected result includes:

- VERIFY=PASS_V021_FAST
- DATASET=PASS_SCALE_DATASET_GENERATED
- SOURCE_RESULT=PASS_SCALE_BENCHMARK_RUNNER
- FREEZE=FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE
- E_100K_ACC=1
- E_100K_SENSITIVE_LEAK=0
- E_100K_TRACEABILITY=1

## Next likely research steps

- v0.2.2 exact-memory retrieval calibration
- v0.2.3 noisy query and adversarial memory benchmark
- v0.2.4 optional real LLM answer-quality evaluation
- Later product path: local SQLite memory pointer SDK or editor/plugin wrapper

