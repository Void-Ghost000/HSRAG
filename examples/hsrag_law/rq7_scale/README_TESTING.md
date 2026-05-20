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

Adapters covered:

- txt_manifest
- fixed_csv
- auto_csv

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- One-command verify: available.
- Adapter matrix verify: available.
- Full-scale RQ7 benchmark: not implemented yet.
- Official RQ4 corpus loader: not connected yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify commands validate pipeline integrity and artifact generation.
They do not prove full-scale benchmark performance.
They do not prove HSRAG replaces all RAG systems.
They do not provide legal advice.
