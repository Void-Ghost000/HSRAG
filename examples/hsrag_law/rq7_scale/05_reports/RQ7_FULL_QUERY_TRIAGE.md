# RQ7 Full Query Triage

- status: OK
- diagnostic_status: DIAGNOSTIC_WARN
- acceptance_passed: False
- raw_result_count: 420

## Triage Summary

- ALLOW_MATCHED_TARGET: 124
- EXPECTED_GUARD_BLOCK: 64
- FALSE_ALLOW_RISK: 96
- TARGET_BLOCKED: 136

## Reason by Triage

### ALLOW_MATCHED_TARGET
- FOUND: 124

### EXPECTED_GUARD_BLOCK
- NO_EVIDENCE: 24
- AMBIGUOUS_ROUTE: 8
- UNIQUE_ADDRESS_NOT_FOUND: 32

### FALSE_ALLOW_RISK
- FOUND: 96

### TARGET_BLOCKED
- NO_EVIDENCE: 128
- UNIQUE_ADDRESS_NOT_FOUND: 8

## Claim Boundary

- triage_only: true
- acceptance_failure_allowed_for_diagnostics: true
- full_query_expansion: true
- full_scale_benchmark: false
- vector_hybrid_baselines: false
- legal_advice: false
