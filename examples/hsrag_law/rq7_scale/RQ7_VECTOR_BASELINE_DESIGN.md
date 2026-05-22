# RQ7 Vector Baseline Design

## Status

This document defines the first vector baseline scope for the RQ7 vector branch.

Branch:

    rq7-vector-baseline

## Goal

Add a local-only deterministic vector-style retrieval baseline for RQ7.

This baseline is intended to compare against:

- BM25_GLOBAL
- TFIDF_GLOBAL
- CTHC_PRUNED_BM25
- CTHC_PRUNED_TFIDF
- UNIQUE_ADDRESS

## Initial Baseline Type

The first vector baseline must be:

    LOCAL_DETERMINISTIC_VECTOR

Meaning:

- no external embedding API
- no network access
- no secrets
- no model download
- no GPU requirement
- deterministic output
- reproducible in CI/local pytest

## Allowed Implementation

Allowed:

- local bag-of-words vector
- local hashed term-frequency vector
- local character n-gram vector
- cosine similarity
- deterministic tokenization
- fixed dimension hashing

## Forbidden Implementation

Forbidden:

- OpenAI embeddings
- external embedding APIs
- downloading models at runtime
- requiring API keys
- network calls
- non-deterministic ranking
- hidden remote cache
- claiming semantic embedding parity

## Claim Boundary

This baseline is not a state-of-the-art vector search engine.

It is a local deterministic vector-style baseline used for RQ7 comparison.

It does not prove performance against production vector databases.

It does not replace real embedding benchmarks.

It does not provide legal advice.

## Required Modes

Future implementation should add:

- VECTOR_GLOBAL
- CTHC_PRUNED_VECTOR

Optional later:

- HYBRID_BM25_VECTOR
- CTHC_PRUNED_HYBRID

## Required Metrics

The vector baseline must report the same metrics as existing modes:

- target_correct_rate
- wrong_corpus_collision_rate
- wrong_jurisdiction_collision_rate
- no_evidence_false_allow_rate
- ambiguous_false_allow_rate
- candidate_reduction_ratio
- retrieved_token_count_mean
- estimated_token_cost_usd_per_1k_queries
- latency_p99_ms
- actual_elapsed_p99_ms
- esi_mean
- returned_domain_salt_valid_rate

## Acceptance Gates

A valid first implementation must satisfy:

- local_only: true
- zero_network: true
- zero_secret: true
- deterministic ranking: true
- same query seed support as existing runner
- same registry support as existing runner
- metrics_summary includes vector modes
- metrics_by_query_class includes vector modes
- pytest RQ7 tests pass

## Known Limits

- This is not a neural embedding baseline.
- This is not a production vector database.
- This does not benchmark ANN indexes.
- This does not include hybrid ranking yet.
- This is a reproducible local comparator only.

## Next Step

RQ7-vector.2 should implement:

    local_hash_vector.py

with deterministic vectorization and cosine similarity.
