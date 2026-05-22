# RQ7 Vector Branch Status

- status: OK
- checked_at_utc: 2026-05-22T07:48:35.788537Z
- branch_scope: rq7-vector-baseline

## Current Vector Additions

- design: `examples/hsrag_law/rq7_scale/RQ7_VECTOR_BASELINE_DESIGN.md`
- vectorizer: `examples/hsrag_law/rq7_scale/scripts/local_hash_vector.py`
- config: `examples/hsrag_law/rq7_scale/config.rq7.vector.json`
- report_md: `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.md`
- report_json: `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json`
- report_csv: `examples/hsrag_law/rq7_scale/05_reports/RQ7_VECTOR_BASELINE_REPORT.csv`

## Vector Modes

- CTHC_PRUNED_VECTOR
- VECTOR_GLOBAL

## Claim Boundary

- local_deterministic_vector_baseline: true
- external_embedding_api: false
- network_required: false
- secret_required: false
- state_of_the_art_vector_search: false
- production_vector_database: false
- hybrid_ranking: false
- legal_advice: false

## Next Steps

- RQ7-vector.8 final vector verify
- RQ7-vector.9 optional tag
- future branch: hybrid BM25/vector baseline
