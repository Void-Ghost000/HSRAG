# RQ7 Full Branch Status

- status: OK
- checked_at_utc: 2026-05-22T04:23:58.942673Z
- branch_scope: rq7-full-benchmark

## Current Full-Branch Additions

- full_query_seed: `examples/hsrag_law/rq7_scale/02_input/query_seed.full.example.json`
- full_query_config: `examples/hsrag_law/rq7_scale/config.rq7.full_queries.json`
- diagnostics_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.md`
- diagnostics_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS.json`
- diagnostics_summary: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json`
- triage_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.md`
- triage_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_FULL_QUERY_TRIAGE.json`
- corpus_inventory_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_CORPUS_EXPANSION_INVENTORY.md`
- corpus_inventory_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_CORPUS_EXPANSION_INVENTORY.json`
- synthetic_scale_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.md`
- synthetic_scale_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.json`
- synthetic_scale_csv: `examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.csv`

## Metrics

- query_count: 21
- added_query_count: 18
- diagnostic_status: DIAGNOSTIC_WARN
- acceptance_passed: False
- raw_result_count: 420
- query_class_count: 6
- text_corpus_candidate_count: 4
- synthetic_target_sizes: [1000, 5000, 10000]

## Claim Boundary

- full_query_expansion: true
- diagnostic_only: true
- triage_only: true
- corpus_inventory_only: true
- synthetic_expansion: true
- synthetic_scale_stress_only: true
- synthetic_expansion_is_not_new_legal_corpus: true
- acceptance_failure_allowed_for_diagnostics: true
- full_scale_real_corpus_benchmark: false
- vector_hybrid_baselines: false
- legal_advice: false

## Next Branches

- full public benchmark report
- final full synthetic checkpoint verify
- vector baseline
- hybrid baseline
- real multi-corpus expansion
