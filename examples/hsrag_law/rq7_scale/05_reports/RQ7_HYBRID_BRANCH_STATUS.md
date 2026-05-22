# RQ7 Hybrid Branch Status

- status: OK
- checked_at_utc: 2026-05-22T13:06:32.687942Z
- branch_scope: rq7-hybrid-baseline
- final_checkpoint_ready: true

## Hybrid Modes

- CTHC_PRUNED_HYBRID
- HYBRID_BM25_VECTOR

## Published Files

- `examples/hsrag_law/rq7_scale/RQ7_HYBRID_BASELINE_DESIGN.md`
- `examples/hsrag_law/rq7_scale/scripts/local_hybrid_scorer.py`
- `examples/hsrag_law/rq7_scale/config.rq7.hybrid.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT_SUMMARY.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BASELINE_REPORT.csv`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_HYBRID_BRANCH_STATUS.json`

## Claim Boundary

- local_deterministic_hybrid_baseline: true
- external_embedding_api: false
- network_required: false
- secret_required: false
- state_of_the_art_hybrid_search: false
- production_vector_database: false
- legal_advice: false

## Verify

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/build_rq7_hybrid_branch_status.py
