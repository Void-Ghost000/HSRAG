# HSRAG API SQLite Demo

A local-first, zero-secret, zero-network SQLite demo for managing API specifications with HSRAG-style addressing.

This example demonstrates how API specs can be converted into:

- deterministic CTHC pointers
- deterministic source hashes
- TACL-lite authority layers
- FHS / CHS / EHS evidence classes
- revision-aware SQLite records
- guarded query results
- audit-friendly result contracts

## Status

This is an early reproducible demo inside the HSRAG repository.

It is not:

- an API gateway
- a production API registry
- a cloud service
- an LLM API wrapper
- an OpenAPI SaaS platform

## Security / Secrets

This demo is local-only.

It does not require any API key.

It does not call external services.

It does not read .env files.

It does not store Authorization headers, Bearer tokens, passwords, or secrets.

All inputs are local JSON files. All outputs are local SQLite files or local benchmark reports.

## Core Idea

API specifications should not be resolved by vague semantic guessing.

Canonical API spec lookup should use:

    CTHC pointer + authority layer + source hash

In this demo:

    CTHC identifies the API unit.
    TACL-lite defines the authority layer.
    FHS / CHS / EHS isolate evidence trust.
    Guard logic prevents ambiguous or lower-authority records from becoming canonical contracts.

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

## Input Example

The sample API spec is stored at:

    input/api_spec.example.json

It describes a small demo user service with:

    GET /users/{id}
    POST /users

## Local Benchmark

Run:

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

This produces:

    benchmarks/local_lookup_report.json

The benchmark measures local SQLite lookup latency only.

It does not benchmark cloud RAG, LLM billing, or production API latency.

## Current Validation

Benchmark scaffold has been executed locally.

Smoke test command:

    python -m pytest tests\test_benchmark_script_smoke.py

Expected result:

    1 passed

## Design Principle

Natural language helps discover candidates.

CTHC pointer decides identity.

TACL-lite decides authority layer.

FHS decides canonical contract.

Guard decides whether the result can be trusted.

Audit records why.
