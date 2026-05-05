# HSRAG — Hash-Structured Retrieval-Augmented Generation

HSRAG is a hash-structured retrieval architecture designed to make AI retrieval more auditable, domain-bounded, and token-efficient.

It is not intended to replace all RAG systems. Instead, HSRAG separates **addressing** from **reasoning**: structured hash addressing is used to narrow the evidence space before generation or semantic reasoning happens.

## Why HSRAG?

Traditional retrieval-augmented generation systems often rely heavily on fuzzy semantic retrieval. This is powerful, but in high-stakes domains it can create several failure modes:

- wrong-domain retrieval
- jurisdiction or corpus collision
- ambiguous query over-allowance
- no-evidence false positives
- high token cost
- weak auditability

HSRAG is designed to reduce these risks by adding a structured, hash-addressed retrieval layer before evidence assembly and generation.

## Core Idea

HSRAG maps a query into structured classification and hash-addressable domains before retrieval.

```text
Query
  ↓
Query Normalize
  ↓
CTHC Classification / Cross-Tag Hash Code
  ↓
Hash Subset Pruning
  ↓
Retrieval Plane
  ├─ Hash Direct Retrieval
  └─ RAG / Fuzzy Retrieval
  ↓
Evidence Assembler
  ↓
Guard Layer
  ↓
Generator
  ↓
Audit Chain
```

The main principle is:

```text
Do not ask the model to search everything.
First constrain the evidence space, then reason over bounded evidence.
```

## Current Public Demo

The first public implementation demo is:

```text
examples/hsrag_law/
```

HSRAG LAW demonstrates HSRAG on legal retrieval and cross-jurisdiction collision control.

Current benchmark direction:

- EU AI Act + DMA legal retrieval
- EU × US legal corpus collision tests
- ambiguous query blocking
- no-evidence handling
- audit-chain verification
- baseline comparison against lexical retrieval methods

## Repository Structure

```text
hsrag/
├─ README.md
├─ docs/
│  ├─ architecture.md
│  ├─ hsrag_overview.md
│  ├─ audit_model.md
│  ├─ governance.md
│  └─ ev_evidence_section.md
│
├─ examples/
│  └─ hsrag_law/
│     ├─ README.md
│     ├─ data_manifest.md
│     ├─ run_demo.py
│     ├─ scripts/
│     └─ results/
│
├─ src/
│  └─ hsrag/
│     ├─ cthc.py
│     ├─ hash_router.py
│     ├─ evidence_assembler.py
│     ├─ guard.py
│     └─ audit_chain.py
│
├─ tests/
└─ assets/
```

## Project Status

This repository is an early open-source research implementation.

Current focus:

- minimal public architecture
- reproducible legal retrieval demo
- benchmark summaries
- audit-friendly result reporting
- lightweight Python implementation

This is not a production legal search engine and does not provide legal advice.

## Roadmap

Planned next steps:

- stabilize HSRAG LAW demo
- add reproducible benchmark scripts
- document HSRAG architecture
- add CTHC classification examples
- add audit-chain examples
- prepare public report and EV application evidence section

## License

License information will be added in `LICENSE`.