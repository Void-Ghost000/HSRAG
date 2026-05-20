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

Expected result:

    status: OK
    acceptance_passed: true
    latest_report_is_clean: true

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- One-command verify: available.
- Adapter matrix verify: available.
- Artifact inventory scan: available.
- Candidate select and run: available.
- Full-scale RQ7 benchmark: not implemented yet.
- Official RQ4 corpus loader: not connected yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify commands validate pipeline integrity and artifact generation.
They do not prove full-scale benchmark performance.
They do not prove HSRAG replaces all RAG systems.
They do not provide legal advice.
