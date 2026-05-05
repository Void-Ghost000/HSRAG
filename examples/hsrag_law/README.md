# HSRAG LAW

HSRAG LAW is the first public implementation demo of **HSRAG — Hash-Structured Retrieval-Augmented Generation**.

It demonstrates how hash-structured retrieval can be applied to legal-domain retrieval, cross-jurisdiction comparison, wrong-corpus collision control, ambiguous-query blocking, and audit-chain verification.

This demo is part of the main HSRAG repository:

```text
examples/hsrag_law/
```

## Purpose

The purpose of HSRAG LAW is to test whether a hash-structured retrieval architecture can reduce several common retrieval failure modes in high-stakes legal or regulatory domains:

- wrong-corpus retrieval
- wrong-jurisdiction retrieval
- ambiguous query over-allowance
- no-evidence false positives
- pointer or domain mismatch escape
- weak auditability
- unnecessary token usage

HSRAG LAW is not designed to replace legal professionals or legal reasoning systems. It is a retrieval and evidence-bounding demonstration.

## Core Idea

Traditional retrieval systems often rely on lexical or semantic similarity first.

HSRAG LAW instead uses structured domain routing before evidence assembly:

```text
Legal Query
  ↓
Query Normalize
  ↓
Corpus / Jurisdiction / Unit Classification
  ↓
Hash-Structured Domain Routing
  ↓
Evidence Retrieval
  ↓
Evidence Assembly
  ↓
Guard Layer
  ↓
Auditable Result
```

The goal is simple:

```text
Constrain the legal evidence space before allowing retrieval or generation.
```

## Benchmark Scope

HSRAG LAW currently contains three benchmark directions.

### RQ1 — Publication-Grade Real Corpus Gate

RQ1 validates source-hash backfill, real-primary corpus gating, and SC1 regression behavior.

Summary:

- real primary corpus rate: 1.0
- source hash final present rate: 1.0
- target correctness: 1.0
- wrong collision rate: 0.0
- SC1 regression target correctness: 1.0
- fail count: 0
- warn count: 0

RQ1 is used as the publication-grade real-corpus gate baseline.

### RQ2 — Real EU Law Benchmark

RQ2 tests HSRAG LAW on uploaded EU legal PDFs:

- EU AI Act
- EU Digital Markets Act / DMA

Scale:

- article-level chunks: 188
- base queries: 424
- mutation / attack cases: 3,392

Result summary:

- HSRAG target correctness: 1.0
- wrong collision rate: 0.0
- no-evidence false allow rate: 0.0
- ambiguous false allow rate: 0.0
- mismatch escape rate: 0.0
- audit chain complete rate: 1.0
- p95 latency: approximately 1.43 ms

Against BM25-lite lexical baselines, HSRAG reduced token usage by approximately 78% and estimated cost by approximately 73% in this benchmark setting.

### RQ3 — EU × US Real-Law Collision Benchmark

RQ3 expands the test from EU-only legal retrieval to EU × US legal collision control.

Corpora:

- EU AI Act
- EU DMA
- US COPPA
- CDA Section 230
- FTC Act Section 5
- CCPA

Scale:

- chunks: 244
- base queries: 592
- mutation / attack cases: 14,208
- baseline modes: 4

Result summary:

- HSRAG target correctness: 1.0
- wrong corpus collision: 0.0
- wrong jurisdiction escape: 0.0
- no-evidence false allow: 0.0
- ambiguous false allow: 0.0
- mismatch escape: 0.0
- audit chain complete: 1.0
- p95 latency: approximately 5.92 ms

Best lexical baseline comparison:

- best baseline target correctness: approximately 0.908
- best baseline wrong corpus collision: approximately 0.0196
- best baseline wrong jurisdiction escape: approximately 0.0110
- best baseline no-evidence false allow: approximately 0.967
- best baseline ambiguous false allow: 1.0
- best baseline mismatch escape: 1.0

## Current Results Summary

Across the current RQ2 and RQ3 legal retrieval benchmarks, HSRAG LAW demonstrates:

- 100% target correctness in the tested benchmark cases
- 0 wrong-corpus collision
- 0 wrong-jurisdiction escape after jurisdiction hierarchy normalization
- 0 no-evidence false allow
- 0 ambiguous-query false allow
- 0 pointer mismatch escape
- complete audit-chain verification
- substantial token and cost reduction compared with lexical retrieval baselines in the RQ2 setting

These are benchmark results for the included research setup, not universal claims about all legal retrieval tasks.

## Repository Layout

```text
examples/hsrag_law/
├─ README.md
├─ data_manifest.md
├─ run_demo.py
├─ requirements.txt
│
├─ data/
│
├─ scripts/
│  ├─ build_chunks.py
│  ├─ run_benchmark.py
│  └─ compare_baselines.py
│
└─ results/
   ├─ rq1_summary.md
   ├─ rq2_real_eu_law_summary.md
   ├─ rq3_eu_us_collision_summary.md
   └─ unified_benchmark_table_v0_3.csv
```

## How to Run

This repository is currently being prepared as an open-source research demo.

The intended entry point is:

```bash
python run_demo.py
```

Benchmark scripts are located in:

```text
scripts/
```

Planned execution flow:

```bash
python scripts/build_chunks.py
python scripts/run_benchmark.py
python scripts/compare_baselines.py
```

## Notes on Data and Provenance

This demo uses legal corpus artifacts and benchmark summaries prepared for HSRAG LAW experiments.

Some benchmark stages distinguish between:

- uploaded real PDFs
- public legal references
- official-source verified corpora
- research benchmark artifacts

Source verification and provenance details should be tracked in:

```text
data_manifest.md
```

## Limitations

HSRAG LAW is currently an early research implementation.

Important limitations:

- It is not legal advice.
- It is not a production legal search engine.
- It does not replace legal interpretation by qualified professionals.
- Benchmark results are scoped to the included corpora, queries, mutations, and baseline implementations.
- Additional independent reproduction is needed before making broad production claims.

## Status

Current status:

```text
Research demo / early open-source implementation
```

Near-term goals:

- stabilize runnable scripts
- add clearer data manifest
- publish benchmark summary tables
- document HSRAG routing logic
- add minimal reproducibility instructions
- prepare public report and EV evidence section