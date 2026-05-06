# HSRAG 6.3 × TACL Integrated Architecture

This document describes the future integrated architecture outlook for HSRAG 6.3 × TACL.

It is a design and roadmap document, not a claim that every component is already fully implemented in the current repository.

Current repository status:

- HSRAG LAW benchmark demo is implemented and reproducible.
- CTHC typed routing, salted domain hashing, evidence gating, and audit-chain outputs are demonstrated.
- The full HSRAG 6.3 × TACL integrated stack remains a forward architecture target.

---

## 1. Purpose

Traditional retrieval pipelines often mix together:

- query understanding
- corpus search
- evidence selection
- generation
- runtime control
- audit logging

HSRAG 6.3 × TACL separates these concerns.

In simple terms:

    HSRAG decides where the query is allowed to retrieve from.
    TACL decides whether execution should continue, stop, retry, degrade, or bail out.

The goal is to make retrieval and generation more:

- bounded
- auditable
- domain-aware
- cost-aware
- resistant to unsupported evidence mixing

---

## 2. Two-layer architecture

The integrated architecture has two main layers:

- Layer A: Governance Evolution Layer
- Layer B: Execution Architecture / Runtime Plane

Layer A defines the rules.

Layer B executes the query.

Short form:

    Layer A modifies the protocol.
    Layer B executes the runtime.

---

## 3. Layer A — Governance Evolution Layer

Layer A governs long-term protocol evolution.

It does not answer user queries directly.

It defines:

- immutable constraints
- fork-level governance
- legitimacy rules
- protocol-change rules
- rule descent into runtime

Core elements:

    Ω_core immutable constraints
    Fork domains
    Time-based legitimacy engine
    PR classification
    Rule / policy / constraint descent

Layer A exists to prevent the system from evolving in ways that break core safety, auditability, or anchor rules.

---

## 4. Layer A concise diagram

    ┌──────────────────────────────────────────────┐
    │ Layer A — Governance Evolution Layer         │
    │----------------------------------------------│
    │ Ω_core immutable constraints                 │
    │ fork governance                              │
    │ legitimacy / stability rules                 │
    │ policy evolution                             │
    │ rule descent to runtime                      │
    │                                              │
    │ Note: governs rules, does not answer query   │
    └──────────────────────────────────────────────┘
                         │
                         ▼
                 Rule / Policy Descent

---

## 5. Layer B — Execution Architecture / Runtime Plane

Layer B handles actual query execution.

It contains:

1. Client / Edge Layer
2. Query Normalize
3. CTHC Cross-Tag Hash Code
4. Hash Subset Pruner
5. Retrieval Plane
6. Evidence Assembler
7. Guard Layer
8. TACL Control Layer
9. Generator
10. Soft Release
11. Audit & Telemetry
12. Memory Writeback

Layer B is the operational path used to process a query.

---

## 6. Layer B concise diagram

    ┌──────────────────────────────────────────────┐
    │ Layer B — Execution Architecture / Runtime   │
    │----------------------------------------------│
    │ [0] Client / Edge                            │
    │ [1] Query Normalize                          │
    │ [2] CTHC Cross-Tag Hash Code                 │
    │ [3] Hash Subset Pruner                       │
    │ [4] Retrieval Plane                          │
    │ [5] Evidence Assembler                       │
    │ [6] Guard Layer                              │
    │ [6.5] TACL Control Layer                     │
    │ [7] Generator                                │
    │ [8] Soft Release                             │
    │ [9] Audit & Telemetry                        │
    │ [10] Memory Writeback                        │
    └──────────────────────────────────────────────┘

---

## 7. Runtime flow

Simplified runtime flow:

    query
    → normalize
    → CTHC typed route
    → hash subset pruner
    → retrieval plane
    → evidence assembler
    → guard layer
    → TACL control layer
    → generator
    → soft release
    → audit and telemetry
    → memory writeback

This flow is designed to reduce full-corpus fuzzy search and to make each decision auditable.

---

## 8. Runtime module roles

### [0] Client / Edge Layer

Captures the user query and may maintain a local hash-only context index.

Purpose:

- query capture
- local context pointer
- edge-side hash reference

---

### [1] Query Normalize

Normalizes the query and performs initial classification.

Purpose:

- clean query
- classify task type
- tag intent / field / risk

---

### [2] CTHC Cross-Tag Hash Code

Maps the query into a structured semantic address.

Purpose:

- hierarchical classification
- multi-tag routing
- traceable semantic address generation

---

### [3] Hash Subset Pruner

Shrinks the search space before retrieval.

Purpose:

- reduce token cost
- reduce latency
- prevent full-corpus semantic search when a bounded hash route exists

---

### [4] Retrieval Plane

Retrieval has two paths:

- HAR Direct
- RAG Fuzzy Retrieval

HAR Direct means hash-addressed retrieval.

RAG Fuzzy Retrieval is a fallback path for unresolved or boundary cases.

---

### [5] Evidence Assembler

Builds the evidence set for downstream use.

Purpose:

- assemble evidence
- deduplicate evidence
- rank evidence
- prepare answer-bound context

---

### [6] Guard Layer

Applies safety and evidence constraints.

Purpose:

- anchor rules
- evidence-only constraint
- no unsupported extrapolation
- dual-gate checking where applicable

---

### [6.5] TACL Control Layer

TACL makes runtime control decisions.

Possible actions:

- CONTINUE
- STOP
- RETRY
- BAILOUT
- DEGRADED MODE

TACL evaluates:

- cost
- depth
- failure count
- evidence sufficiency
- runtime risk

---

### [7] Generator

Generates only inside the evidence-bound context.

Purpose:

- avoid unsupported generation
- avoid treating fuzzy retrieval as certain fact
- preserve anchor constraints

---

### [8] Soft Release

Performs field-aware minimal output selection.

Purpose:

- release only the minimal supported answer
- preserve field precision
- avoid over-generation

Example fields:

- YEAR
- CODE
- VALUE
- ENTITY
- JURISDICTION
- SOURCE

---

### [9] Audit & Telemetry

Writes traceable output records.

Typical records:

- query_hash
- evidence_hash
- answer_hash
- decision_trace
- guard_reason
- TACL action trace

---

### [10] Memory Writeback

Updates memory stores after runtime.

Possible stores:

- FHS: Fact Hash Store
- EHS: Ephemeral Hash Store
- CHS: Creative / Challenge Hash Store
- Edge Index

Writeback must obey governance and audit constraints.

---

## 9. Ω_core design invariants

The architecture assumes a protected invariant layer called Ω_core.

Typical invariants include:

- core invariants cannot be silently removed
- anchor rules cannot be bypassed
- auditability cannot be disabled
- runtime must remain evidence-bounded
- sovereign constraints must not be overridden by downstream public rules

These invariants define the safe boundary of system evolution.

---

## 10. Why TACL is integrated

HSRAG controls retrieval boundaries.

TACL controls runtime continuation.

This division is useful for high-stakes systems where retrieval alone is not enough.

Simplified division:

    HSRAG:
    - typed routing
    - bounded retrieval
    - evidence governance
    - auditability

    TACL:
    - runtime control
    - failure handling
    - retry / bailout logic
    - cost and depth control

Together, they form a bounded retrieval and runtime-control architecture.

---

## 11. Relation to the current repository

The current repository does not yet implement the full integrated architecture end-to-end.

Already demonstrated:

- CTHC-style routing
- salted domain hashes
- bounded legal retrieval benchmark
- evidence gating
- audit-chain outputs
- custom corpus template

Future-facing components:

- full Layer A governance evolution
- complete TACL runtime control loop
- generalized HAR + RAG hybrid retrieval stack
- edge hash-only context index
- memory writeback across FHS / EHS / CHS
- fork legitimacy and policy evolution mechanisms

This document should be read as:

    implemented benchmark foundation
    + future integrated architecture target

---

## 12. Intended positioning

HSRAG 6.3 × TACL is intended for:

- high-stakes retrieval systems
- auditable AI pipelines
- legal / policy / enterprise knowledge retrieval
- future agent systems requiring stronger runtime control
- systems where unsupported generation is costly or risky

It is not intended as a generic retrieve-everything-from-everywhere system.

Priority order:

    boundedness > blind coverage
    auditability > opaque convenience
    safe control > uncontrolled continuation

---

## 13. Current demo mapping

The current HSRAG LAW demo mainly validates a subset of Layer B.

Validated in current benchmark form:

- CTHC typed routing
- salted domain hashing
- bounded retrieval
- evidence gating
- audit-chain output
- custom corpus benchmark template

Not yet fully implemented:

- complete Layer A governance
- full TACL action loop
- generalized memory writeback
- full edge context index
- complete soft-release generation layer

---

## 14. One-line summary

HSRAG 6.3 × TACL is a future integrated architecture that combines typed hash-addressed retrieval with runtime control, so AI systems can retrieve, decide, and generate under bounded, auditable, and policy-governed constraints.