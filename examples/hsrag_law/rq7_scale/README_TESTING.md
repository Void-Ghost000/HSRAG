# RQ7 Testing

RQ7 currently supports local verification paths.

Core verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Adapter matrix verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_adapters.py

Artifact inventory scan command:

    python examples/hsrag_law/rq7_scale/scripts/scan_rq7_artifacts.py --root examples/hsrag_law --output examples/hsrag_law/rq7_scale/04_runs/rq7_artifact_inventory.local.json --report examples/hsrag_law/rq7_scale/04_runs/rq7_artifact_inventory.local.md

Candidate select and run command:

    python examples/hsrag_law/rq7_scale/scripts/run_rq7_candidate.py --root examples/hsrag_law/rq7_scale/02_input

RQ4 rebuilt artifact verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_rq4.py

RQ4 metrics snapshot command:

    python examples/hsrag_law/rq7_scale/scripts/snapshot_rq7_rq4_metrics.py

Master verify command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py

Expected master result:

    status: OK
    all_passed: true
    latest_report_is_clean: true
    local_only: true
    zero_network: true
    zero_secret: true
    rq4_rebuilt_artifact_connected: true
    rq4_metrics_snapshot_available: true
    unit_derivation_is_heuristic: true

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- One-command verify: available.
- Adapter matrix verify: available.
- Artifact inventory scan: available.
- Candidate select and run: available.
- RQ4 rebuilt artifact verify: available.
- RQ4 metrics snapshot: available.
- Master verify includes RQ4 metrics snapshot.
- Full-scale RQ7 benchmark: not implemented yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify commands validate pipeline integrity and artifact generation.
RQ4 rebuilt verify connects a local RQ4 rebuilt chunk artifact, but unit derivation is still heuristic.
RQ4 metrics snapshot extracts current RQ7 metrics from the RQ4 rebuilt run.
They do not prove full-scale benchmark performance.
They do not prove HSRAG replaces all RAG systems.
They do not provide legal advice.
