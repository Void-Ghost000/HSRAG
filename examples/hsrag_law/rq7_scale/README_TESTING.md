# RQ7 Testing

RQ7 currently supports local verification paths.

Core verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Adapter matrix verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_adapters.py

RQ4 metrics snapshot command:

    python examples/hsrag_law/rq7_scale/scripts/snapshot_rq7_rq4_metrics.py

RQ4 scale tier command:

    python examples/hsrag_law/rq7_scale/scripts/run_rq7_rq4_scale_tiers.py --tiers 100,300,600,889

Public report command:

    python examples/hsrag_law/rq7_scale/scripts/build_rq7_public_report.py --tiers 100,300,600,889

Master verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py

Expected current results:

    status: OK
    acceptance_passed: true
    latest_report_is_clean: true
    rq4_rebuilt_artifact_connected: true
    rq4_metrics_snapshot_available: true
    unit_derivation_is_heuristic: true

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- RQ4 rebuilt artifact verify: available.
- RQ4 metrics snapshot: available.
- RQ4 scale tier runner: available.
- RQ7 public report generator: available.
- Master verify includes RQ4 metrics snapshot.
- Full-scale RQ7 benchmark: not implemented yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify commands validate pipeline integrity and artifact generation.
RQ4 rebuilt verify connects a local RQ4 rebuilt chunk artifact, but unit derivation is still heuristic.
RQ4 scale tier runner tests selected tiers from the 889-chunk RQ4 rebuilt artifact.
The public report summarizes current local results and claim boundaries.
They do not prove full-scale benchmark performance.
They do not prove HSRAG replaces all RAG systems.
They do not provide legal advice.

