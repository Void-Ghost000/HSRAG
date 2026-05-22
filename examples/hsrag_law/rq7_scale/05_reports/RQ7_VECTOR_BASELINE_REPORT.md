# RQ7 Vector Baseline Report

- status: OK
- generated_at_utc: 2026-05-22T07:19:31.003903Z
- runner_status: OK
- runner_passed: True

## Claim Boundary

- local_deterministic_vector_baseline: true
- external_embedding_api: false
- network_required: false
- secret_required: false
- state_of_the_art_vector_search: false
- production_vector_database: false
- legal_advice: false

This is a local deterministic vector-style baseline.

It is not a neural embedding baseline, not a production vector database benchmark, and not a state-of-the-art semantic search comparison.

## Vector Modes

- CTHC_PRUNED_VECTOR
- VECTOR_GLOBAL

## Metrics

| mode | corpus_size | target_correct | candidate_reduction | estimated_p99_ms | actual_elapsed_p99_ms | token_cost_per_1k | esi | salt_valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CTHC_PRUNED_VECTOR | 1000 | 1.0 | 0.999333 | 2.64 | 0.6593 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_VECTOR | 5000 | 1.0 | 0.999867 | 2.64 | 1.9225 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_VECTOR | 10000 | 1.0 | 0.999933 | 2.64 | 1.6653 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_VECTOR | 50000 | 1.0 | 0.999987 | 2.64 | 5.4894 | 0.00153333 | 0.666667 | 1.0 |
| VECTOR_GLOBAL | 1000 | 1.0 | 0.0 | 14.26 | 17.5332 | 0.00206667 | 0.333333 | 1.0 |
| VECTOR_GLOBAL | 5000 | 1.0 | 0.0 | 17.056 | 91.8216 | 0.00216667 | 0.333333 | 1.0 |
| VECTOR_GLOBAL | 10000 | 1.0 | 0.0 | 18.26 | 180.0392 | 0.00216667 | 0.333333 | 1.0 |
| VECTOR_GLOBAL | 50000 | 1.0 | 0.0 | 21.056 | 886.2918 | 0.00216667 | 0.333333 | 1.0 |

## Verify

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/build_rq7_vector_baseline_report.py

## Known Limits

- This does not use external embeddings.
- This does not call any embedding API.
- This does not benchmark ANN/vector databases.
- Hybrid ranking is not included yet.
- This is not legal advice.
