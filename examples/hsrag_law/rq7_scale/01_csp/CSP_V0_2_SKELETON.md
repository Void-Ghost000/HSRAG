# RQ7 CSP v0.2 Skeleton

Intent:
Benchmark retrieval boundary control as corpus scale grows.

Context / CTHC:
Domain: HSRAG / LAW / Retrieval Benchmark
Context: local public-law corpus and synthetic scale noise
CTHC target: domain / jurisdiction / corpus / unit / chunk

Risk Class:
Medium.

State:
- corpus_manifest
- chunk_registry
- cthc_index
- query_seed
- mutation_policy
- mode_config
- raw_results
- metrics_summary
- audit_log

Input:
- config.rq7.json
- corpus_manifest.example.json
- query_seed.example.json
- mutation_policy.example.json

L0 Basic Validity Gate:
- config exists
- corpus manifest exists
- query seed exists
- mode list non-empty
- required metrics non-empty

L1 Security / Permission Gate:
Not applicable because RQ7 v0.1 is local-only and uses no secrets.

L2 State / Resource Gate:
- scale tier must be configured
- chunk count must be bounded
- local output path must exist

L2T Temporal Gate:
- one canonical run_started_at_utc per run
- all result rows share the same run timestamp
- no local naive datetime for internal storage

L2N Network / Secret Gate:
- no network calls in v0.1
- no API keys
- no remote embedding service

L2R Retry / Recovery Gate:
- failed run must return structured reason
- partial results must be explicitly marked
- no silent skip

L3 Transition / Side Effect Gate:
Allowed side effects:
- write raw_results.jsonl
- write metrics_summary.csv
- write audit_chain.jsonl
- write acceptance_gates.json

Forbidden side effects:
- mutate source corpus
- overwrite previous run without run_id

L4 Persistence / Audit Gate:
Each run must emit:
- run_manifest.json
- raw_results.jsonl
- metrics_summary.csv
- audit_chain.jsonl
- acceptance_gates.json

Known Limits:
This scaffold does not execute the benchmark yet.
