# VERIFY v0.2.1

This document describes how to verify the frozen HSRAG Memory Context Scale Baseline v0.2.1.

## Fast Verify

    powershell -ExecutionPolicy Bypass -File examples/hsrag_memory_context_v021_scale/verify_v021.ps1 -Mode fast

Fast mode validates existing generated artifacts and frozen summaries.

## Full Verify

    powershell -ExecutionPolicy Bypass -File examples/hsrag_memory_context_v021_scale/verify_v021.ps1 -Mode full

Full mode reruns:

- make_v021_scale_dataset.py
- run_v021_scale_benchmark.py
- make_v021_freeze_summary.py

Then it validates the frozen gates.

## Full Verify Without Leaving Tracked Output Dirty

    powershell -ExecutionPolicy Bypass -File examples/hsrag_memory_context_v021_scale/verify_v021.ps1 -Mode full -RestoreTrackedArtifacts

This reruns the benchmark, validates the output, and restores tracked generated artifacts afterward.

## Expected Result

The expected success output includes:

- VERIFY=PASS_V021_FAST or VERIFY=PASS_V021_FULL
- DATASET=PASS_SCALE_DATASET_GENERATED
- SOURCE_RESULT=PASS_SCALE_BENCHMARK_RUNNER
- FREEZE=FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE
- E_100K_ACC=1
- E_100K_SENSITIVE_LEAK=0
- E_100K_TRACEABILITY=1
- RAW_JSONL_STAGED=NO
- RAW_JSONL_IGNORED=9/9

## Boundary

This is a synthetic deterministic benchmark.

It does not call a real LLM.

It does not use real personal data.

It does not prove GDPR compliance.

Local latency measures context construction only, not model inference.
