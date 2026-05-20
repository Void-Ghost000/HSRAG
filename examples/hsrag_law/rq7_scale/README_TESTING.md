# RQ7 Testing

RQ7 currently supports local one-command verification paths.

## Core Verify

Command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Expected result:

    status: OK
    one_command_verify: true
    acceptance_passed: true
    latest_report_is_clean: true

## Adapter Matrix Verify

Command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_adapters.py

Expected result:

    status: OK
    all_passed: true
    adapter_count: 3

## Artifact Inventory Scan

Command:

    python examples/hsrag_law/rq7_scale/scripts/scan_rq7_artifacts.py --root examples/hsrag_law --output examples/hsrag_law/rq7_scale/04_runs/rq7_artifact_inventory.local.json --report examples/hsrag_law/rq7_scale/04_runs/rq7_artifact_inventory.local.md

Expected result:

    status: OK
    local_only: true
    zero_network: true
    zero_secret: true

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- One-command verify: available.
- Adapter matrix verify: available.
- Artifact inventory scan: available.
- Full-scale RQ7 benchmark: not implemented yet.
- Official RQ4 corpus loader: not connected yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify commands validate pipeline integrity and artifact generation.
They do not prove full-scale benchmark performance.
They do not prove HSRAG replaces all RAG systems.
They do not provide legal advice.
