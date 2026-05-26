# v0.2.1 Scale Benchmark Failure Diagnosis

Decision: PASS_FAILURE_DIAGNOSIS

## Target

- N: 100000
- Strategy: E_POINTER_ON_DEMAND_RESOLVE

## Main Finding

- E 100k answer rate: 0.85
- E 100k failure count: 15
- Top fail topic: audit_chain
- Top fail count: 15
- Likely root cause: SYNTHETIC_EXPECTED_TERM_MISMATCH_SUMMARY_VS_RAW_TEXT

## Recommendation

Align audit_chain raw text with expected term traceability, or include summary metadata in E resolved context. Do not lower the gate.

## Boundary

- Diagnosis only.
- No acceptance gate was lowered.
- Rerun Step 9 after applying a fix.
