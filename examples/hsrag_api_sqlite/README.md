# HSRAG API SQLite Demo

HSRAG API SQLite is a local-first verified prototype for hash-addressed API specification management.

It demonstrates how API specifications can be stored, versioned, queried, and audited using:

- CTHC hash pointers
- TACL-lite authority layers
- FHS / CHS / EHS evidence isolation
- deterministic source hashes
- SQLite persistence
- guarded query results
- one-command local verification

## Why This Exists

API specs are contracts.

They should not be resolved by vague semantic guessing.

A query like:

    "find the API for getting a pet"

may be useful for discovery, but it should not automatically become a canonical API contract.

This demo follows a stricter rule:

    Natural language helps discover candidates.
    CTHC pointer decides identity.
    TACL-lite decides authority.
    Source hash decides content version.
    Guard decides whether the result can be trusted.

## Current Status

Status:

    Verified local prototype

Current verified scope:

    local-only
    zero-secret
    zero-network
    SQLite-based
    deterministic CTHC hash
    deterministic authority hash
    deterministic source hash
    TACL-lite evidence guard
    FHS / CHS / EHS isolation
    revision tracking
    pointer-based lookup
    OpenAPI JSON local importer
    candidates-only semantic discovery
    one-command local verification

Current validation target:

    pytest: 69+ tests passed before OpenAPI extension
    demo: passed
    benchmark: passed
    verifier: passed
    acceptance gates: passed

This is not production-ready.

It is a reproducible verified prototype.

## What This Demo Is

This demo provides a minimal local API specification registry with:

- API spec ingest from local JSON
- local OpenAPI JSON import
- deterministic CTHC address and CTHC hash generation
- deterministic authority hash generation
- deterministic source hash generation
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
- a full OpenAPI platform
- a security authentication system
- a production permission engine

## Security / Secrets

This demo does not require any API key.

It does not call external services during import, query, demo, benchmark, or verification.

It does not read .env files.

It does not store Authorization headers, Bearer tokens, passwords, API keys, or secrets.

All normal inputs are local JSON files.

All generated outputs are local SQLite databases, JSON reports, or benchmark reports.

## Core Principle

Canonical API spec lookup should use:

    CTHC pointer + authority layer + source hash

In this demo:

    CTHC identifies the API unit.
    TACL-lite defines the authority layer.
    FHS / CHS / EHS isolate evidence trust.
    Source hash tracks content version.
    Guard logic prevents ambiguous or lower-authority records from becoming canonical contracts.
    Audit-style reports explain why a result was accepted, blocked, or returned as a warning.

## CTHC Hash vs Authority Hash vs Source Hash

This demo separates API identity from authority level and content version.

cthc_hash identifies the API specification unit.

It is generated from:

    API|{service_name}|{api_version}|{method}|{path}

Example:

    API|external-petstore3|v1|GET|/pet/{petId}

authority_hash identifies the TACL-lite authority layer.

It is generated from:

    TACL|{tacl_layer}|{evidence_class}|{contract_role}

Example:

    TACL|L0|FHS|core

source_hash identifies the normalized content version of the API specification.

The three hashes have different responsibilities:

| Hash | Purpose |
|---|---|
| cthc_hash | Which API spec unit is this? |
| authority_hash | What authority layer does this record belong to? |
| source_hash | Has the API spec content changed? |

In this design, the TACL-lite layer is not embedded inside the CTHC hash.

Instead:

    CTHC hash decides identity.
    Authority hash decides authority.
    Source hash decides content version.

This keeps API identity, trust level, and version history auditable and independently testable.

## Authority Mapping

Importers and users must explicitly provide:

    evidence_class
    tacl_layer
    contract_role

Allowed mappings:

| Layer | Evidence Class | Contract Role | Meaning |
|---|---|---|---|
| L0 | FHS | core | canonical API contract |
| L1 | CHS | supplement | verified supplement |
| L2 | CHS | supplement | usage note / SDK note |
| L3 | EHS | candidate | unverified candidate |
| L4 | EHS | discovery | semantic discovery only |

Invalid mappings are blocked by Guard.

For example:

    L0 / EHS / core

is invalid because unverified EHS data cannot become a canonical contract.

## Important Note About Authority Hash

authority_hash is not a secret.

authority_hash is not an API key.

authority_hash is not an authentication token.

It is a deterministic structural guard key.

It helps prevent lower-authority records, such as CHS or EHS, from being treated as canonical FHS API contracts.

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

## Input Samples

The demo includes local input samples:

    input/api_spec.example.json
    input/petstore_subset.api_spec.json
    input/openapi_petstore_minimal.json

The first two are normalized HSRAG API spec JSON files.

The third is a local OpenAPI JSON sample used by the importer.

## Local OpenAPI JSON Importer

The importer supports local OpenAPI JSON files.

It does not support YAML in this version.

It does not fetch remote URLs.

It does not require an API key.

Run the importer:

    python .\src\hsrag_api_sqlite\openapi_importer.py

Expected local outputs:

    data/openapi_import.sqlite3
    data/openapi_normalized.json

## External OpenAPI Validation

Manual external validation was performed with Swagger Petstore 3 OpenAPI JSON saved as a local file.

The importer was tested in two authority modes:

    EHS / L3 / candidate
    FHS / L0 / core

Observed behavior:

    EHS / L3 / candidate returned found_with_warning and did not become canonical.
    FHS / L0 / core returned found API_SPEC_FOUND after explicit reviewed import mode.
    External Petstore OpenAPI import produced 19 API spec records in the reviewed FHS test.

This external validation is manual and local.

It is not part of CI and should not be treated as a network-dependent guarantee.

## Main Commands

Run all tests:

    python -m pytest

Run the end-to-end demo:

    python .\src\hsrag_api_sqlite\demo.py

Run the local benchmark:

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

Run local OpenAPI importer:

    python .\src\hsrag_api_sqlite\openapi_importer.py

Run one-command local verification:

    python .\scripts\verify_local.py

## 60-second Quickstart

From this directory:

    python -m pytest
    python .\scripts\verify_local.py

Expected verifier result:

    "status": "passed"

## One-command Verification

The verifier runs:

    1. python -m pytest
    2. python .\src\hsrag_api_sqlite\demo.py
    3. python .\scripts\benchmark_local_lookup.py

Expected local outputs:

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

Semantic discovery only returns candidates.

It cannot return canonical contracts without pointer confirmation.

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

Current limits:

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

Source hash decides content version.

FHS decides canonical contract.

CHS supplements but cannot override FHS.

EHS can be stored as candidate but cannot become canonical.

Guard decides whether the result can be trusted.

Audit-style outputs record why.
