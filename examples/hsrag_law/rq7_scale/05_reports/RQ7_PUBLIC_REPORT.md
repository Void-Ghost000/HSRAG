# HSRAG RQ7 Public Report

## Status

- report_id: rq7_public_report_20260521T121233821565z
- run_started_at_utc: 2026-05-21T12:12:33.821565Z
- status: OK
- rq4_rebuilt_chunk_count: 889
- scale_tiers: 100, 300, 600, 889
- actual_elapsed_timing_available: true

## What This Report Covers

This report summarizes the current RQ7 local verification stack using the RQ4 rebuilt chunk artifact.

It covers:

- RQ4 rebuilt artifact connection
- RQ4 metrics snapshot
- RQ4 scale-tier run
- retrieval-mode comparison output
- query-class metrics availability
- actual elapsed timing propagation

## Claim Boundary

This report does not claim that HSRAG replaces all RAG systems.

This report does not claim full-scale benchmark completion.

This report does not provide legal advice.

This report does not include vector or hybrid baselines.

The current RQ4 unit derivation is heuristic.

Latency values include local actual elapsed measurements, but this is not a production latency benchmark.

## RQ4 Metrics Snapshot

- snapshot_status: OK
- acceptance_passed: True
- latest_report_is_clean: True
- chunk_count: 889
- unit_count: 7
- unit_derivation_is_heuristic: True

## Available Modes

- BM25_GLOBAL
- CTHC_PRUNED_BM25
- CTHC_PRUNED_TFIDF
- TFIDF_GLOBAL
- UNIQUE_ADDRESS

## Available Query Classes

- ambiguous_cross_domain
- exact_unit
- no_evidence

## Scale Tier Metrics

| tier_size | mode | target_correct | candidate_reduction | estimated_p99_ms | actual_elapsed_p99_ms | token_cost_per_1k | esi |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | BM25_GLOBAL | 1.0 | 0.0 | 10.26 | 6.8793 | 0.02006667 | 0.333333 |
| 100 | CTHC_PRUNED_BM25 | 1.0 | 0.993333 | 2.64 | 0.1436 | 0.00686667 | 1.0 |
| 100 | CTHC_PRUNED_TFIDF | 1.0 | 0.993333 | 2.64 | 0.1293 | 0.00686667 | 1.0 |
| 100 | TFIDF_GLOBAL | 1.0 | 0.0 | 10.26 | 6.9385 | 0.02006667 | 0.333333 |
| 100 | UNIQUE_ADDRESS | 1.0 | 0.996667 | 0.41 | 0.0243 | 0.007 | 1.0 |
| 300 | BM25_GLOBAL | 1.0 | 0.0 | 12.168 | 24.6964 | 0.01986667 | 0.333333 |
| 300 | CTHC_PRUNED_BM25 | 1.0 | 0.99 | 2.64 | 0.6748 | 0.00666667 | 1.0 |
| 300 | CTHC_PRUNED_TFIDF | 1.0 | 0.99 | 2.64 | 0.6508 | 0.00666667 | 1.0 |
| 300 | TFIDF_GLOBAL | 1.0 | 0.0 | 12.168 | 22.9292 | 0.01986667 | 0.333333 |
| 300 | UNIQUE_ADDRESS | 1.0 | 0.998889 | 0.41 | 0.0505 | 0.007 | 1.0 |
| 600 | BM25_GLOBAL | 1.0 | 0.0 | 13.373 | 41.0625 | 0.02033333 | 0.333333 |
| 600 | CTHC_PRUNED_BM25 | 1.0 | 0.967778 | 3.645 | 3.8516 | 0.00666667 | 1.0 |
| 600 | CTHC_PRUNED_TFIDF | 1.0 | 0.967778 | 3.645 | 4.8507 | 0.00666667 | 1.0 |
| 600 | TFIDF_GLOBAL | 1.0 | 0.0 | 13.373 | 39.3719 | 0.02033333 | 0.333333 |
| 600 | UNIQUE_ADDRESS | 1.0 | 0.999444 | 0.41 | 0.1075 | 0.00616667 | 1.0 |
| 889 | BM25_GLOBAL | 1.0 | 0.0 | 14.056 | 69.9304 | 0.01963333 | 0.333333 |
| 889 | CTHC_PRUNED_BM25 | 1.0 | 0.974128 | 3.645 | 3.6108 | 0.01326667 | 0.666667 |
| 889 | CTHC_PRUNED_TFIDF | 1.0 | 0.974128 | 3.645 | 4.3209 | 0.01326667 | 0.666667 |
| 889 | TFIDF_GLOBAL | 1.0 | 0.0 | 14.056 | 59.7207 | 0.01963333 | 0.333333 |
| 889 | UNIQUE_ADDRESS | 1.0 | 0.999625 | 0.41 | 0.1397 | 0.00616667 | 1.0 |

## Reproduction Commands

Run RQ7 master verify:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py

Run RQ4 metrics snapshot:

    python examples/hsrag_law/rq7_scale/scripts/snapshot_rq7_rq4_metrics.py

Run RQ4 scale tiers:

    python examples/hsrag_law/rq7_scale/scripts/run_rq7_rq4_scale_tiers.py --tiers 100,300,600,889

Run all RQ7 tests:

    python -m pytest tests -k rq7

## Known Limits

- RQ4 unit derivation is heuristic.
- Full-scale benchmark is still pending.
- Vector and hybrid baselines are not implemented yet.
- Token cost is estimated, not API billing.
- Production latency is not measured.
- This is not legal advice.
