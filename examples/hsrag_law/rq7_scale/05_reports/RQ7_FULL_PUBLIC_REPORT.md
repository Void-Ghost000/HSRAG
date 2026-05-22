# RQ7 Full Public Report

## Status

- status: OK
- generated_at_utc: 2026-05-22T04:45:49.641861Z
- branch_scope: rq7-full-benchmark

## What This Report Covers

- full query seed expansion
- full query diagnostics
- full query triage
- corpus expansion inventory
- synthetic 1k / 5k / 10k scale stress benchmark

## Claim Boundary

- diagnostic_only: true
- triage_only: true
- synthetic_expansion: true
- synthetic_scale_stress_only: true
- synthetic_expansion_is_not_new_legal_corpus: true
- full_scale_real_corpus_benchmark: false
- vector_hybrid_baselines: false
- legal_advice: false

This report does not claim a full-scale real-law corpus benchmark.

This report does not include vector or hybrid baselines.

Synthetic chunks are explicitly labeled and are not additional legal evidence.

## Full Query Expansion

- query_count: 21
- added_query_count: 18

## Diagnostics

- diagnostic_status: DIAGNOSTIC_WARN
- acceptance_passed: False
- raw_result_count: 420
- query_class_count: 6

## Triage Summary

- ALLOW_MATCHED_TARGET: 124
- EXPECTED_GUARD_BLOCK: 64
- FALSE_ALLOW_RISK: 96
- TARGET_BLOCKED: 136

## Corpus Inventory

- artifact_count: 26
- text_corpus_candidate_count: 4

## Synthetic Scale Benchmark

- target_sizes: [1000, 5000, 10000]

| target_size | mode | target_correct | candidate_reduction | estimated_p99_ms | actual_elapsed_p99_ms | token_cost_per_1k | esi |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1000 | BM25_GLOBAL | 1.0 | 0.0 | 14.26 | 56.6027 | 0.0205 | 0.333333 |
| 1000 | BM25_GLOBAL | 1.0 | 0.0 | 17.056 | 227.5274 | 0.0205 | 0.333333 |
| 1000 | BM25_GLOBAL | 1.0 | 0.0 | 18.26 | 173.8127 | 0.0205 | 0.333333 |
| 1000 | BM25_GLOBAL | 1.0 | 0.0 | 21.056 | 656.2762 | 0.0205 | 0.333333 |
| 1000 | CTHC_PRUNED_BM25 | 1.0 | 0.976333 | 3.667 | 3.762 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_BM25 | 1.0 | 0.995267 | 3.667 | 3.9706 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_BM25 | 1.0 | 0.997633 | 3.667 | 7.7259 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_BM25 | 1.0 | 0.999527 | 3.667 | 8.2629 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_TFIDF | 1.0 | 0.976333 | 3.667 | 3.5667 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_TFIDF | 1.0 | 0.995267 | 3.667 | 4.1458 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_TFIDF | 1.0 | 0.997633 | 3.667 | 8.2077 | 0.01413333 | 0.666667 |
| 1000 | CTHC_PRUNED_TFIDF | 1.0 | 0.999527 | 3.667 | 8.3351 | 0.01413333 | 0.666667 |
| 1000 | TFIDF_GLOBAL | 1.0 | 0.0 | 14.26 | 57.8444 | 0.0205 | 0.333333 |
| 1000 | TFIDF_GLOBAL | 1.0 | 0.0 | 17.056 | 97.8718 | 0.0205 | 0.333333 |
| 1000 | TFIDF_GLOBAL | 1.0 | 0.0 | 18.26 | 214.8419 | 0.0205 | 0.333333 |
| 1000 | TFIDF_GLOBAL | 1.0 | 0.0 | 21.056 | 727.5384 | 0.0205 | 0.333333 |
| 1000 | UNIQUE_ADDRESS | 1.0 | 0.999667 | 0.41 | 0.147 | 0.00616667 | 1.0 |
| 1000 | UNIQUE_ADDRESS | 1.0 | 0.999933 | 0.41 | 0.4568 | 0.00616667 | 1.0 |
| 1000 | UNIQUE_ADDRESS | 1.0 | 0.999967 | 0.41 | 1.4128 | 0.00616667 | 1.0 |
| 1000 | UNIQUE_ADDRESS | 1.0 | 0.999993 | 0.41 | 5.3373 | 0.00616667 | 1.0 |
| 5000 | BM25_GLOBAL | 1.0 | 0.0 | 14.26 | 73.3783 | 0.0205 | 0.333333 |
| 5000 | BM25_GLOBAL | 1.0 | 0.0 | 17.056 | 441.227 | 0.0203 | 0.333333 |
| 5000 | BM25_GLOBAL | 1.0 | 0.0 | 18.26 | 359.431 | 0.0203 | 0.333333 |
| 5000 | BM25_GLOBAL | 1.0 | 0.0 | 21.056 | 776.3173 | 0.0203 | 0.333333 |
| 5000 | CTHC_PRUNED_BM25 | 1.0 | 0.976333 | 3.667 | 3.8538 | 0.01413333 | 0.666667 |
| 5000 | CTHC_PRUNED_BM25 | 1.0 | 0.973133 | 4.812 | 22.9959 | 0.01473333 | 0.666667 |
| 5000 | CTHC_PRUNED_BM25 | 1.0 | 0.986567 | 4.812 | 23.4936 | 0.01473333 | 0.666667 |
| 5000 | CTHC_PRUNED_BM25 | 1.0 | 0.997313 | 4.812 | 27.374 | 0.01473333 | 0.666667 |
| 5000 | CTHC_PRUNED_TFIDF | 1.0 | 0.976333 | 3.667 | 3.8195 | 0.01413333 | 0.666667 |
| 5000 | CTHC_PRUNED_TFIDF | 1.0 | 0.973133 | 4.812 | 22.0353 | 0.01473333 | 0.666667 |
| 5000 | CTHC_PRUNED_TFIDF | 1.0 | 0.986567 | 4.812 | 23.2019 | 0.01473333 | 0.666667 |
| 5000 | CTHC_PRUNED_TFIDF | 1.0 | 0.997313 | 4.812 | 26.6374 | 0.01473333 | 0.666667 |
| 5000 | TFIDF_GLOBAL | 1.0 | 0.0 | 14.26 | 61.6899 | 0.0205 | 0.333333 |
| 5000 | TFIDF_GLOBAL | 1.0 | 0.0 | 17.056 | 439.9273 | 0.0203 | 0.333333 |
| 5000 | TFIDF_GLOBAL | 1.0 | 0.0 | 18.26 | 368.7749 | 0.0203 | 0.333333 |
| 5000 | TFIDF_GLOBAL | 1.0 | 0.0 | 21.056 | 769.649 | 0.0203 | 0.333333 |
| 5000 | UNIQUE_ADDRESS | 1.0 | 0.999667 | 0.41 | 0.1495 | 0.00616667 | 1.0 |
| 5000 | UNIQUE_ADDRESS | 1.0 | 0.999933 | 0.41 | 0.8986 | 0.00773333 | 1.0 |
| 5000 | UNIQUE_ADDRESS | 1.0 | 0.999967 | 0.41 | 1.7412 | 0.00773333 | 1.0 |
| 5000 | UNIQUE_ADDRESS | 1.0 | 0.999993 | 0.41 | 5.317 | 0.00773333 | 1.0 |
| 10000 | BM25_GLOBAL | 1.0 | 0.0 | 14.26 | 59.101 | 0.0205 | 0.333333 |
| 10000 | BM25_GLOBAL | 1.0 | 0.0 | 17.056 | 350.2752 | 0.0203 | 0.333333 |
| 10000 | BM25_GLOBAL | 1.0 | 0.0 | 18.26 | 620.4932 | 0.0203 | 0.333333 |
| 10000 | BM25_GLOBAL | 1.0 | 0.0 | 21.056 | 1038.7097 | 0.0203 | 0.333333 |
| 10000 | CTHC_PRUNED_BM25 | 1.0 | 0.976333 | 3.667 | 3.5025 | 0.01413333 | 0.666667 |
| 10000 | CTHC_PRUNED_BM25 | 1.0 | 0.973133 | 4.812 | 22.8172 | 0.01473333 | 0.666667 |
| 10000 | CTHC_PRUNED_BM25 | 1.0 | 0.974533 | 5.212 | 41.8545 | 0.01473333 | 0.666667 |
| 10000 | CTHC_PRUNED_BM25 | 1.0 | 0.994907 | 5.212 | 45.1357 | 0.01473333 | 0.666667 |
| 10000 | CTHC_PRUNED_TFIDF | 1.0 | 0.976333 | 3.667 | 3.5713 | 0.01413333 | 0.666667 |
| 10000 | CTHC_PRUNED_TFIDF | 1.0 | 0.973133 | 4.812 | 21.5816 | 0.01473333 | 0.666667 |
| 10000 | CTHC_PRUNED_TFIDF | 1.0 | 0.974533 | 5.212 | 41.7218 | 0.01473333 | 0.666667 |
| 10000 | CTHC_PRUNED_TFIDF | 1.0 | 0.994907 | 5.212 | 46.8418 | 0.01473333 | 0.666667 |
| 10000 | TFIDF_GLOBAL | 1.0 | 0.0 | 14.26 | 58.4373 | 0.0205 | 0.333333 |
| 10000 | TFIDF_GLOBAL | 1.0 | 0.0 | 17.056 | 310.1695 | 0.0203 | 0.333333 |
| 10000 | TFIDF_GLOBAL | 1.0 | 0.0 | 18.26 | 621.5188 | 0.0203 | 0.333333 |
| 10000 | TFIDF_GLOBAL | 1.0 | 0.0 | 21.056 | 1016.9479 | 0.0203 | 0.333333 |
| 10000 | UNIQUE_ADDRESS | 1.0 | 0.999667 | 0.41 | 0.1516 | 0.00616667 | 1.0 |
| 10000 | UNIQUE_ADDRESS | 1.0 | 0.999933 | 0.41 | 0.8121 | 0.00773333 | 1.0 |
| 10000 | UNIQUE_ADDRESS | 1.0 | 0.999967 | 0.41 | 2.3113 | 0.00723333 | 1.0 |
| 10000 | UNIQUE_ADDRESS | 1.0 | 0.999993 | 0.41 | 6.0856 | 0.00723333 | 1.0 |

## Verify

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/build_rq7_full_branch_status.py
    python examples/hsrag_law/rq7_scale/scripts/run_rq7_synthetic_scale_benchmark.py --target-sizes 1000,5000,10000

## Known Limits

- Real-law corpus currently remains limited by available source artifacts.
- Synthetic scale expansion is for scale stress only.
- Vector / hybrid baselines are pending.
- This is not legal advice.
