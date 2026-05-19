# README_TESTING

This file describes how to test and verify the HSRAG API SQLite demo locally.

## Scope

All normal verification commands are:

- local-only
- zero-secret
- zero-network

No API key is required.

No external service is called by the importer, demo, query layer, benchmark, or verifier.

No LLM call is made.

## Install Test Dependency

From this directory:

    python -m pip install pytest

## Run All Tests

    python -m pytest

Expected result in the current verified prototype:

    all tests passed

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

## Run Local OpenAPI JSON Importer

    python .\src\hsrag_api_sqlite\openapi_importer.py

Expected local outputs:

    data/openapi_import.sqlite3
    data/openapi_normalized.json

The importer is local-only, zero-secret, and zero-network.

It accepts local JSON files only.

It does not support YAML in this version.

It does not fetch remote URLs.

It does not require an API key.

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

## Manual External OpenAPI Validation

The importer can be manually tested with an external OpenAPI JSON file saved locally.

Example workflow:

    1. Download a public OpenAPI JSON file manually.
    2. Save it under input/.
    3. Run openapi_importer.py against that local file.
    4. Query the generated SQLite DB.

Recommended authority behavior:

    Unreviewed external spec:
        evidence_class = EHS
        tacl_layer = L3
        contract_role = candidate

    Reviewed external spec:
        evidence_class = FHS
        tacl_layer = L0
        contract_role = core

Expected behavior:

    EHS / L3 / candidate returns found_with_warning.
    FHS / L0 / core can return found API_SPEC_FOUND.

Manual validation already performed locally:

    External Petstore OpenAPI JSON
    EHS candidate mode: found_with_warning
    FHS reviewed mode: found API_SPEC_FOUND
    Reviewed import count: 19 records

This external validation is manual and not part of CI.

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

Observed locally:

    pytest: passed
    demo: passed
    benchmark: passed
    acceptance gates: passed

## Notes

This is a verified local prototype, not a production deployment.

Do not commit generated local artifacts under data/ or benchmark reports under benchmarks/.
