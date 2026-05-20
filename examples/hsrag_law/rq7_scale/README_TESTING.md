# RQ7 Testing

RQ7 currently supports a local one-command verification path.

Command:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Expected result:

    status: OK
    one_command_verify: true
    acceptance_passed: true
    latest_report_is_clean: true

This command performs:

1. Build a local chunk registry from real_law_manifest.example.json.
2. Run RQ7 with the generated chunk registry.
3. Validate required artifacts.
4. Validate acceptance gates.
5. Write rq7_verify_summary.json and rq7_verify_summary.txt.

Current maturity:

- Salted toy-real retrieval pipeline: verified.
- One-command verify: available.
- Full-scale RQ7 benchmark: not implemented yet.
- Official RQ4 corpus loader: not connected yet.
- Vector / hybrid baselines: not implemented yet.

Claim boundary:

The current verify command validates pipeline integrity and artifact generation.
It does not prove full-scale benchmark performance.
It does not prove HSRAG replaces all RAG systems.
It does not provide legal advice.
