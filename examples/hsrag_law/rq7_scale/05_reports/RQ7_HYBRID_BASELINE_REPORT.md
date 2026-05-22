# RQ7 Hybrid Baseline Report

- status: OK
- generated_at_utc: 2026-05-22T11:44:25.125715Z
- runner_status: OK
- runner_passed: True

## Claim Boundary

- local_deterministic_hybrid_baseline: true
- external_embedding_api: false
- network_required: false
- secret_required: false
- state_of_the_art_hybrid_search: false
- production_vector_database: false
- legal_advice: false

## Hybrid Modes

- CTHC_PRUNED_HYBRID
- HYBRID_BM25_VECTOR

## Metrics

| mode | corpus_size | target_correct | candidate_reduction | estimated_p99_ms | actual_elapsed_p99_ms | token_cost_per_1k | esi | salt_valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CTHC_PRUNED_HYBRID | 1000 | 1.0 | 0.999333 | 2.64 | 4.6878 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_HYBRID | 5000 | 1.0 | 0.999867 | 2.64 | 4.4743 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_HYBRID | 10000 | 1.0 | 0.999933 | 2.64 | 6.9725 | 0.00153333 | 0.666667 | 1.0 |
| CTHC_PRUNED_HYBRID | 50000 | 1.0 | 0.999987 | 2.64 | 16.9502 | 0.00153333 | 0.666667 | 1.0 |
| HYBRID_BM25_VECTOR | 1000 | 1.0 | 0.0 | 14.26 | 1908.8526 | 0.00223333 | 0.333333 | 1.0 |
| HYBRID_BM25_VECTOR | 5000 | 1.0 | 0.0 | 17.056 | 7025.3069 | 0.00223333 | 0.333333 | 1.0 |
| HYBRID_BM25_VECTOR | 10000 | 1.0 | 0.0 | 18.26 | 17134.4203 | 0.00223333 | 0.333333 | 1.0 |
| HYBRID_BM25_VECTOR | 50000 | 1.0 | 0.0 | 21.056 | 70943.1268 | 0.00223333 | 0.333333 | 1.0 |

## Verify

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/build_rq7_hybrid_baseline_report.py

## Known Limits

- This is a local deterministic hybrid baseline.
- It does not use external embeddings.
- It does not call any embedding API.
- It is not a production vector database benchmark.
- This is not legal advice.
