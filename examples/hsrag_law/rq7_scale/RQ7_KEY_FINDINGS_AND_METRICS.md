# RQ7 Key Findings and Metrics

## Framing Layer

RQ7 evaluates **HSRAG as Hash-Structured RAG with deterministic addressing**.

In this document:

- **Hash-Structured RAG with deterministic addressing** is the top-level framing.
- **Deterministic addressing** is the core mechanism being tested.
- **Authority-graded retrieval** describes the source / corpus governance layer.
- **Boundary-aware retrieval** is only a result-section explanation for why CTHC-style filtering helps in this benchmark.

This avoids mixing every framing term into the main project description.

## What RQ7 Evaluates

RQ7 evaluates the retrieval, routing, and evidence-selection layer.

It compares retrieval modes by:

- target correctness
- candidate reduction
- local measured latency
- estimated evidence-token cost
- evidence-alignment indicators
- salted CTHC boundary behavior
- local deterministic vector / hybrid comparator behavior

## What RQ7 Does Not Evaluate

RQ7 does **not** call an LLM.

RQ7 does **not** evaluate LLM reasoning.

RQ7 does **not** evaluate generated answer quality.

RQ7 does **not** evaluate:

- LLM reasoning quality
- generated answer quality
- legal reasoning by an attorney
- end-to-end chatbot behavior
- production RAG service performance
- production vector database performance
- external embedding API quality
- real API billing cost

RQ7 is not legal advice.

## Core Finding

Current RQ7 results do not primarily show that HSRAG is more accurate than BM25 / TF-IDF on the current easy query set.

Instead, they show that deterministic addressing and CTHC-style boundary filtering can preserve target correctness while reducing:

- candidate search space
- local measured p99 latency
- estimated evidence-token cost
- evidence-alignment ambiguity

## Current Result Snapshot

Current RQ7 suite includes:

- RQ7 v0.1 RQ4 rebuilt 889-chunk checkpoint
- synthetic 1k / 5k / 10k scale-stress benchmark
- local deterministic vector baseline
- local deterministic hybrid baseline

The synthetic scale runs are scale-stress tests, not real-law full-scale corpus benchmarks.

The vector and hybrid baselines are local deterministic comparators, not production embedding or vector database benchmarks.

## Key Metrics

### target_correct_rate

Measures whether the retrieved result matches the expected target.

In the current RQ7 small-scale checkpoints, target correctness is often 1.0 across compared modes. Therefore, target correctness is not the main differentiator in those checkpoints.

### candidate_reduction_ratio

Measures how much of the candidate search space is removed before retrieval.

A higher value means the system searched fewer chunks.

Current RQ4 889-chunk result:

- BM25_GLOBAL / TFIDF_GLOBAL: 0.0
- CTHC_PRUNED_BM25 / CTHC_PRUNED_TFIDF: about 0.974
- UNIQUE_ADDRESS: about 0.9996

Interpretation:

- CTHC pruning removes about 97% of candidates.
- Unique address lookup removes about 99.96% of candidates.

### actual_elapsed_p99_ms

Measures local actual elapsed p99 timing.

Current RQ4 889-chunk result:

- BM25_GLOBAL: about 69.93 ms
- TFIDF_GLOBAL: about 59.72 ms
- CTHC_PRUNED_BM25: about 3.61 ms
- CTHC_PRUNED_TFIDF: about 4.32 ms
- UNIQUE_ADDRESS: about 0.14 ms

Interpretation:

Deterministic addressing and CTHC-style filtering are faster in this local benchmark because they search a much smaller candidate space.

### estimated_token_cost_usd_per_1k_queries

Estimates evidence-token cost from retrieved evidence size.

Current RQ4 889-chunk result:

- BM25_GLOBAL / TFIDF_GLOBAL: about 0.0196 per 1k queries
- CTHC_PRUNED: about 0.0133 per 1k queries
- UNIQUE_ADDRESS: about 0.00617 per 1k queries

Interpretation:

Unique address lookup uses about 31% of the global baseline cost in this checkpoint.

### ESI

ESI means Evidence Support Index.

It is a local benchmark indicator for how cleanly the retrieved evidence supports the target.

Current RQ4 889-chunk result:

- BM25_GLOBAL / TFIDF_GLOBAL: 0.333
- CTHC_PRUNED: 0.667
- UNIQUE_ADDRESS: 1.0

Interpretation:

Global search can retrieve the target, but evidence alignment is weaker. CTHC-pruned retrieval is cleaner. Unique address lookup is the cleanest in the current setup.

## Claim Boundary

RQ7 does not claim:

- HSRAG replaces all RAG systems.
- HSRAG is production-ready.
- HSRAG provides legal advice.
- RQ7 evaluates LLM reasoning.
- RQ7 evaluates generated answer quality.
- Synthetic 10k scale equals real-law 10k corpus scale.
- Local deterministic vector / hybrid baselines equal production embedding systems.
- Local deterministic vector / hybrid baselines equal production vector database benchmarks.

## Best Summary

RQ7 evaluates Hash-Structured RAG with deterministic addressing at the retrieval / routing / evidence-selection layer.

The current result is not mainly “higher answer intelligence.” It is that deterministic addressing and CTHC-style boundary filtering can preserve target correctness while reducing candidate search space, local measured p99 latency, estimated evidence-token cost, and evidence-alignment ambiguity.

