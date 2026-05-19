
## Local Benchmark

Run from `examples/hsrag_api_sqlite`:

    python .\scripts\benchmark_local_lookup.py --runs 10000 --dataset-size 200

This benchmark is local-only, zero-secret, and zero-network.

It reports p50/p95/p99 latency for local SQLite lookup modes and writes:

    benchmarks/local_lookup_report.json

It does not benchmark cloud RAG, LLM billing, or production API latency.
