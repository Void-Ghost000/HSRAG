# HSRAG API SQLite Demo

HSRAG API SQLite is a local-first, hash-addressed API specification SQLite demo.

It shows how API specifications can be stored, versioned, queried, and audited using HSRAG-style CTHC pointers, TACL-lite authority layers, and FHS / CHS / EHS evidence isolation.

## Current Status

Status: Verified local prototype

Current verified scope:

- local-only
- zero-secret
- zero-network
- SQLite-based
- deterministic CTHC hash
- deterministic source hash
- deterministic authority hash
- TACL-lite evidence guard
- FHS / CHS / EHS isolation
- revision tracking
- pointer-based lookup
- candidates-only semantic discovery
- one-command local verification

Last local verification target:

- pytest: 69 passed
- demo: passed
- benchmark: passed
- acceptance gates: passed

This is not production-ready. It is a reproducible verified prototype.

## What This Demo Is

This demo provides a minimal local API specification registry with:

- API spec ingest from local JSON
- deterministic CTHC address and CTHC hash generation
- deterministic source hash generation
- TACL-lite authority hash generation
- FHS / CHS / EHS evidence classification
- lower-layer override blocking
- spec revision tracking
- query by CTHC hash
- query by CTHC address
- query by method and path
- revision history lookup
- candidates-only semantic discovery
- local benchmark reporting
- one-command verification

## What This Demo Is Not

This demo is not:

- an API gateway
- a production API registry
- an OpenAPI SaaS platform
- a cloud service
- an LLM API wrapper
- a vector database
- a remote crawler
- a full OpenAPI importer
- a security authentication system
- a production permission engine

## Security / Secrets

This demo does not require any API key.

It does not call external services.

It does not read .env files.

It does not store Authorization headers, Bearer tokens, passwords, API keys, or secrets.

All inputs are local JSON files.

All outputs are local SQLite databases, JSON reports, or benchmark reports.

## Core Principle

API specifications should not be resolved by vague semantic guessing.

Canonical API spec lookup should use:

    CTHC pointer + authority layer + source hash

In this demo:

    CTHC identifies the API unit.
    TACL-lite defines the authority layer.
    FHS / CHS / EHS isolate evidence trust.
    Guard logic prevents ambiguous or lower-authority records from becoming canonical contracts.
    Audit records why a result was accepted, blocked, or returned as warning.

## Evidence Classes

| Class | Meaning | Canonical Contract |
|---|---|---|
| FHS | Fixed / official / verified API contract | Yes |
| CHS | Changeable heuristic or supplemental note | No |
| EHS | Emerging, external, or unverified candidate | No |

## TACL-lite Layers

| Layer | Evidence | Role | Meaning |
|---|---|---|---|
| L0 | FHS | core | official canonical contract |
| L1 | CHS | supplement | verified supplement |
| L2 | CHS | supplement | usage note / SDK note |
| L3 | EHS | candidate | unverified candidate |
| L4 | EHS | discovery | semantic discovery only |

## Input Format

The sample input is:

    input/api_spec.example.json

It contains a small demo user service:

    GET /users/{id}
    POST /users

The normalized JSON shape is:

    service_name
    api_version
    source_type
    evidence_class
    tacl_layer
    contract_role
    endpoints[]

Each endpoint contains:

    method
    path
    summary
    parameters
    responses
    constraints

## Main Commands

Run all tests:

    python -m pytest

Run the end-to-end demo:

    python .\src\hsrag_api_sqlite\demo.py

Run the local benchmark:

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

Run one-command local verification:

    python .\scripts\verify_local.py

## One-command Verification

The verifier runs:

    1. python -m pytest
    2. python .\src\hsrag_api_sqlite\demo.py
    3. python .\scripts\benchmark_local_lookup.py

Expected result:

    "status": "passed"

Generated local artifacts:

    data/verify_report.json
    data/verify_demo_report.json
    data/verify_demo_api_specs.sqlite3
    data/verify_benchmark_report.json

These generated files are ignored by git.

## Benchmark Scope

The benchmark measures local SQLite lookup latency only.

It reports p50 / p95 / p99 for:

- CTHC hash lookup
- method + path lookup
- semantic-discovery-like lookup

It does not benchmark:

- cloud RAG
- LLM billing
- vector database latency
- production API gateway latency
- real external API calls

The benchmark is intentionally local-only, zero-secret, and zero-network.

## Query Semantics

Recommended canonical lookup:

    query_by_cthc_hash

Allowed structural lookup:

    query_by_method_path with service_name and api_version

Allowed but non-canonical discovery:

    semantic_discovery

Semantic discovery only returns candidates. It cannot return canonical contracts without pointer confirmation.

## Revision Rule

Same CTHC hash plus same source hash:

    idempotent reingest

Same CTHC hash plus different source hash:

    new spec_revision

Different API version:

    new CTHC branch

## Result Contract

Important operations return a stable result shape:

    status
    reason_code
    retryable
    data
    errors
    warnings

The demo avoids vague success or failure values such as None, False, or empty strings.

## Acceptance Gates

A successful local verification must satisfy:

- pytest passes
- demo report generated
- demo confirms local-only / zero-secret / zero-network
- ingest and revision tracking pass
- CTHC pointer lookup passes
- semantic discovery remains candidates-only
- benchmark report generated
- benchmark confirms local-only / zero-secret / zero-network
- no API key required
- no network calls
- no LLM calls
- p99 latency values reported

## Known Limits

Current v0.1 limits:

- no YAML OpenAPI import
- no remote URL ingestion
- no API key support
- no multi-user permission system
- no web UI
- no FastAPI server
- no LLM-assisted API parsing
- no automatic EHS to FHS promotion
- no production database hardening
- no CI workflow yet

## Design Summary

Natural language helps discover candidates.

CTHC pointer decides identity.

TACL-lite decides authority layer.

FHS decides canonical contract.

CHS supplements but cannot override FHS.

EHS can be stored as candidate but cannot become canonical.

Guard decides whether the result can be trusted.

Audit records why.
