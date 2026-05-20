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
- query-class metrics: available
- reporting layer: available
- one-command verify: available

Current delivery level:

Level 2A+ — QSVCS Tested / Toy-real RQ7 pipeline.

## One-command Verify

Run:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Expected current result:

    status: OK
    one_command_verify: true
    acceptance_passed: true
    latest_report_is_clean: true

## Full RQ7 Test Command

Run:

    python -m pytest tests -k rq7

Expected current result:

    all selected RQ7 tests pass

Recent local checkpoint:

    67 items collected
    27 deselected
    40 selected

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

## Claim Boundary

RQ7 currently does not claim:

- HSRAG replaces all RAG systems
- full-scale RQ7 benchmark completion
- production retrieval performance
- legal advice
- official RQ4 corpus validation
- vector / hybrid baseline coverage
- real API billing cost
- production latency measurement

Current RQ7 validates pipeline integrity, artifact generation, salted-domain routing, query-class metrics, and one-command local verification.

## Known Limits

- The current corpus is toy-real / local sample data.
- The current scale noise is synthetic.
- Latency is estimated by deterministic local formulas.
- Token cost is estimated, not actual API billing.
- ESI is rule-based.
- Official RQ4 corpus is not connected yet.
- Vector and hybrid baselines are not implemented yet.
- Full-scale RQ7 benchmark is pending.

## Next Engineering Gate

The next major gate is:

RQ7.3 — Real Corpus Connection

Goal:

    existing RQ4 / RQ2 / RQ3 LAW artifacts
    -> RQ7 chunk registry
    -> salted-domain RQ7 runner
    -> query-class metrics
    -> report
    -> one-command verify

Acceptance target:

- real artifact loader works
- official/public corpus provenance is preserved
- source_hash remains deterministic
- cthc_address remains deterministic
- result contract remains stable
- all RQ7 tests continue passing
