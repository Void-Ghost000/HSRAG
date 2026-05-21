# RQ7 Evidence Summary

## Current Status

RQ7 currently provides a verified local benchmark pipeline for retrieval boundary control.

Current maturity:

- QOIM / CSP v0.2 experiment skeleton: available
- salted toy-real retrieval pipeline: verified
- global search mode: available
- CTHC-pruned search mode: available
- unique address lookup mode: available
- salted-domain gate: verified
- external chunk registry loader: available
- TXT manifest chunk registry builder: available
- CSV chunk registry adapter: available
- auto CSV artifact adapter: available
- artifact inventory scanner: available
- candidate select and run gate: available
- query-class metrics: available
- reporting layer: available
- one-command verify: available
- adapter matrix verify: available
- master verify: available
- RQ4 rebuilt artifact adapter: available
- RQ4 rebuilt artifact verify: available
- RQ4 metrics snapshot: available

Current delivery level:

Level 2B-pre — local master verify with RQ4 rebuilt artifact gate.

## One-command Verify

Run:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py

Expected current result:

    status: OK
    all_passed: true
    latest_report_is_clean: true
    local_only: true
    zero_network: true
    zero_secret: true
    rq4_rebuilt_artifact_connected: true
    rq4_metrics_snapshot_available: true
    unit_derivation_is_heuristic: true

## Full RQ7 Test Command

Run:

    python -m pytest tests -k rq7

Expected current result:

    all selected RQ7 tests pass

## What RQ7 Currently Verifies

RQ7 currently verifies:

- result contract generation
- raw_results.jsonl generation
- metrics_summary.csv generation
- metrics_by_query_class.csv generation
- acceptance_gates.json generation
- hash-linked audit_chain.jsonl generation
- run-local report generation
- latest report no-update-by-default policy
- salted domain metadata
- CTHC address hash metadata
- global search does not use salt for pruning
- CTHC-pruned search uses salted boundary
- unique address lookup returns cthc_address_hash
- generated registry can be loaded from local TXT manifest
- generated registry can be loaded from local CSV artifact
- auto CSV candidate discovery
- adapter matrix verification
- RQ4 rebuilt chunk artifact conversion
- RQ4 rebuilt artifact verification
- RQ4 metrics snapshot extraction
- master verify across local RQ7 stack

## RQ4 Rebuilt Artifact Status

RQ7 can now connect the local RQ4 rebuilt chunk artifact:

    examples/hsrag_law/results/rq4_rebuilt_chunks.csv

Current status:

- RQ4 rebuilt artifact is connected locally.
- RQ4 rebuilt registry generation is verified.
- RQ4 verify gate is available.
- RQ4 metrics snapshot is available.
- Unit derivation is heuristic.
- Full-scale benchmark remains pending.

## Claim Boundary

RQ7 currently does not claim:

- HSRAG replaces all RAG systems
- full-scale RQ7 benchmark completion
- production retrieval performance
- legal advice
- vector / hybrid baseline coverage
- real API billing cost
- production latency measurement
- perfect legal unit parsing

Current RQ7 validates pipeline integrity, artifact generation, salted-domain routing, query-class metrics, local RQ4 rebuilt artifact connection, and master verification.

## Known Limits

- RQ4 unit derivation is heuristic.
- Latency is still estimated by deterministic local formulas.
- Token cost is estimated, not actual API billing.
- ESI is rule-based.
- Vector and hybrid baselines are not implemented yet.
- Full-scale RQ7 benchmark is pending.
- Production retrieval timing is not measured yet.
- This does not provide legal advice.

## Next Engineering Gate

The next major gate is:

RQ7.14 — Real Scale Tier Runner

Goal:

    RQ4 rebuilt chunk registry
    -> scale tier selection
    -> run RQ7 at selected chunk counts
    -> compare modes
    -> emit scale-tier metrics snapshot

Acceptance target:

- scale tiers are explicit
- RQ4 registry is used
- metrics_summary and metrics_by_query_class are generated per tier
- claim boundary remains clear
- all RQ7 tests continue passing
