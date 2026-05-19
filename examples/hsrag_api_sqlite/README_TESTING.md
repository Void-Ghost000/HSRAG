# README_TESTING

This file describes how to test and verify the HSRAG API SQLite demo locally.

## Scope

All verification commands are:

- local-only
- zero-secret
- zero-network

No API key is required.

No external service is called.

No LLM call is made.

## Install Test Dependency

From this directory:

    python -m pip install pytest

## Run All Tests

    python -m pytest

Expected result in the current verified prototype:

    69 passed

## Run Benchmark Smoke Test

    python -m pytest tests\test_benchmark_script_smoke.py

Expected result:

    1 passed

## Run Local Benchmark

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

Expected output file:

    benchmarks/local_lookup_report.json

The benchmark reports p50 / p95 / p99 latency for local SQLite lookup modes.

It does not benchmark cloud RAG, LLM billing, or production API latency.

## Run End-to-End Demo

    python .\src\hsrag_api_sqlite\demo.py

The demo performs:

    1. ingest input/api_spec.example.json
    2. create a second revision for one endpoint
    3. query by method/path
    4. query by CTHC hash pointer
    5. query revision history
    6. run semantic discovery as candidates-only

Expected local outputs:

    data/demo_api_specs.sqlite3
    data/demo_report.json

These files are local artifacts and are ignored by git.

## One-command Verify

    python .\scripts\verify_local.py

This command runs:

    1. python -m pytest
    2. python .\src\hsrag_api_sqlite\demo.py
    3. python .\scripts\benchmark_local_lookup.py

Expected local outputs:

    data/verify_report.json
    data/verify_demo_report.json
    data/verify_demo_api_specs.sqlite3
    data/verify_benchmark_report.json

These files are local artifacts and are ignored by git.

A successful run reports:

    "status": "passed"

## Acceptance Gates

The verifier checks:

- pytest passed
- demo report generated
- demo scope is local-only / zero-secret / zero-network
- ingest and revision passed
- pointer lookup passed
- semantic discovery is candidates-only
- benchmark report generated
- benchmark scope is local-only / zero-secret / zero-network
- no external API key required
- no network calls
- no LLM calls
- p99 latency values reported

## Current Validation Result

Current local verification status:

    passed

Observed in local run:

    pytest: 69 passed
    demo: passed
    benchmark: passed
    acceptance gates: passed

## Notes

This is a verified local prototype, not a production deployment.

Do not commit generated local artifacts under data/ or benchmark reports under benchmarks/.

## Petstore-style Subset Sample

This demo also includes a small normalized Petstore-style sample:

    input/petstore_subset.api_spec.json

It contains:

    GET /pet/{petId}
    POST /pet
    DELETE /pet/{petId}

This file is a local fixed sample for demonstrating HSRAG-style API spec ingest.

It is not fetched from the network.

It does not require an API key.

It does not call a real Petstore service.

Run its tests with:

    python -m pytest tests\test_petstore_subset.py

The sample demonstrates that the ingest and query pipeline can handle a second API spec dataset beyond the toy user-service sample.
