# RQ7 Release Checkpoint

- status: OK
- checked_at_utc: 2026-05-21T11:30:35.026541Z
- rq7_v0_1_checkpoint: true
- rq4_rebuilt_artifact_connected: true
- rq4_metrics_snapshot_available: true
- rq4_scale_tiers_available: true
- public_report_published: true
- actual_elapsed_timing_available: true
- full_scale_benchmark: false
- vector_hybrid_baselines: false
- unit_derivation_is_heuristic: true
- legal_advice: false

## Published Files

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.json`

## Verify

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889

## Claim Boundary

This checkpoint does not claim full-scale benchmark completion.

This checkpoint does not include vector or hybrid baselines.

The current RQ4 unit derivation is heuristic.

This is not legal advice.
