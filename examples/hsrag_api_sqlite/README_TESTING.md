# README_TESTING

## Install test dependency

From this directory:

    python -m pip install pytest

## Run benchmark smoke test

    python -m pytest tests\test_benchmark_script_smoke.py

Expected result:

    1 passed

## Run local benchmark

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

Expected output file:

    benchmarks/local_lookup_report.json

## Scope

This benchmark is local-only, zero-secret, and zero-network.

It reports p50 / p95 / p99 latency for local SQLite lookup modes.

It does not benchmark cloud RAG, LLM billing, or production API latency.

## Current Verified Command

Already verified locally:

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200
    python -m pytest tests\test_benchmark_script_smoke.py

Observed result:

    Benchmark report generated.
    1 passed.

## Future full verification command

Once core modules are implemented:

    python -m pytest

## End-to-End Demo

Run from this directory:

    python .\src\hsrag_api_sqlite\demo.py

This demo performs:

    1. ingest input/api_spec.example.json
    2. create a second revision for one endpoint
    3. query by method/path
    4. query by CTHC hash pointer
    5. query revision history
    6. run semantic discovery as candidates-only

Expected local outputs:

    data/demo_api_specs.sqlite3
    data/demo_report.json

The demo is local-only, zero-secret, and zero-network.
