# RQ7 Full Branch Status

- status: OK
- checked_at_utc: 2026-05-21T15:22:12.761152Z
- branch_scope: rq7-full-benchmark

## Current Full-Branch Additions

- full_query_seed: `examples/hsrag_law/rq7_scale/02_input/query_seed.full.example.json`
- full_query_config: `examples/hsrag_law/rq7_scale/config.rq7.full_queries.json`
- diagnostics_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.md`
- diagnostics_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.json`
- diagnostics_summary: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json`
- triage_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.md`
- triage_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.json`

## Metrics

- query_count: 21
- added_query_count: 18
- diagnostic_status: DIAGNOSTIC_WARN
- acceptance_passed: False
- raw_result_count: 420
- query_class_count: 6

## Claim Boundary

- full_query_expansion: true
- diagnostic_only: true
- triage_only: true
- acceptance_failure_allowed_for_diagnostics: true
- full_scale_benchmark: false
- vector_hybrid_baselines: false
- legal_advice: false

## Next Branches

- expanded real corpus
- 1k / 5k / 10k scale after corpus expansion
- vector baseline
- hybrid baseline
- paper-grade report
