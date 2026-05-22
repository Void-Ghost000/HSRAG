# RQ7 Hybrid Baseline Design

## Status

This document defines the first hybrid baseline scope for the RQ7 hybrid branch.

Branch:

    rq7-hybrid-baseline

## Goal

Add a local-only deterministic hybrid retrieval baseline for RQ7.

The hybrid baseline combines:

- lexical retrieval signal
- local deterministic vector-style signal
- optional CTHC boundary pruning

## Required Modes

Initial modes:

- HYBRID_BM25_VECTOR
- CTHC_PRUNED_HYBRID

## Baseline Type

The first hybrid baseline must be:

    LOCAL_DETERMINISTIC_HYBRID

Meaning:

- no external embedding API
- no network access
- no secrets
- no model download
- no GPU requirement
- deterministic ranking
- reproducible in local pytest

## Scoring Rule

Initial scoring may use:

    hybrid_score = alpha * lexical_score + beta * vector_score

Default:

    alpha = 0.5
    beta = 0.5

The scoring rule must be explicit and deterministic.

## Claim Boundary

This is not a state-of-the-art hybrid search engine.

This is not a production vector database benchmark.

This does not use neural embeddings.

This does not require external APIs.

This does not provide legal advice.

## Required Metrics

Hybrid modes must report the same RQ7 metrics as existing modes:

- target_correct_rate
- candidate_reduction_ratio
- retrieved_token_count_mean
- estimated_token_cost_usd_per_1k_queries
- latency_p99_ms
- actual_elapsed_p99_ms
- esi_mean
- returned_domain_salt_valid_rate

## Acceptance Gates

A valid implementation must satisfy:

- local_only: true
- zero_network: true
- zero_secret: true
- deterministic ranking: true
- HYBRID_BM25_VECTOR appears in metrics_summary
- CTHC_PRUNED_HYBRID appears in metrics_summary
- CTHC_PRUNED_HYBRID uses salted CTHC boundary
- pytest RQ7 tests pass

## Next Step

RQ7-hybrid.2 should implement local hybrid scoring without modifying external dependencies.
