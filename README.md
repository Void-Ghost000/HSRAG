# HSRAG

**HSRAG** stands for **Hash-Structured Retrieval-Augmented Generation**.

It is a retrieval architecture designed to make AI retrieval more:

- bounded,
- auditable,
- domain-aware,
- token-efficient,
- and resistant to cross-domain evidence mixing.

HSRAG is not intended to replace all RAG systems.

Instead, it separates **addressing** from **reasoning**:

```text
RAG usually asks:
"Which text is semantically similar?"

HSRAG first asks:
"Which bounded, auditable knowledge address is this query allowed to touch?"
```

The goal is to reduce hallucination risk, wrong-domain retrieval, and unnecessary token usage before generation or reasoning happens.

---

## 1. Core idea

The current HSRAG design uses structured hash-based routing before retrieval.

A simplified flow:

```text
query
→ normalize
→ CTHC typed route
→ salted domain hash
→ bounded retrieval
→ evidence gate
→ audit chain
→ output
```

Where:

- **CTHC** is a hierarchical classification/addressing code.
- **Salted domain hash** separates retrieval domains into non-confusing hash buckets.
- **Bounded retrieval** prevents the system from searching the whole corpus when the query lacks a stable domain address.
- **Evidence gating** rejects unsupported, ambiguous, or conflict-form queries.
- **Audit chain** records reproducible decision traces.

---

## 2. Why HSRAG?

Traditional retrieval-augmented generation systems often rely heavily on fuzzy semantic retrieval.

This is powerful, but in high-stakes domains it can create several failure modes:

```text
wrong-domain retrieval
wrong-jurisdiction retrieval
unsupported query false allow
ambiguous query false allow
conflict-form query false allow
large token waste
weak auditability
```

HSRAG introduces a structured routing layer before retrieval.

Instead of immediately searching all text chunks, HSRAG first attempts to resolve the query into a bounded, typed, auditable route.

---

## 3. Main components

### CTHC typed address

CTHC is used as a structured classification and addressing layer.

For legal text, a simplified CTHC path may look like:

```text
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
```

This means a chunk is not just plain text.  
It also carries a typed address.

---

### Salted domain hash

Each domain receives a salted hash bucket:

```text
domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)
```

Retrieval is only allowed inside the matching salted domain bucket.

This is used to reduce corpus collision and cross-domain retrieval risk.

---

### Evidence gate

HSRAG does not automatically retrieve for every query.

It can reject:

```text
unsupported query
ambiguous query
conflict-form query
unroutable query
```

before evidence retrieval.

---

### Audit chain

HSRAG writes auditable records for benchmark cases and summary decisions.

This makes results easier to inspect, reproduce, and challenge.

---

## 4. Current implementation status

This repository currently contains a research / benchmark implementation.

The main live demo is:

```text
examples/hsrag_law/
```

Current status:

```text
Research demo / early open-source implementation
```

This is not a production system yet.

---

## 5. HSRAG LAW demo

**HSRAG LAW** is a legal-text retrieval demonstration.

It tests whether legal retrieval can be made more bounded and auditable by using:

```text
CTHC typed legal routing
+ salted domain hashes
+ bounded retrieval
+ evidence gating
+ audit chains
```

The LAW demo is located here:

```text
examples/hsrag_law/
```

---

## 6. HSRAG LAW verification status

Current verification stages:

| Stage | Purpose | Status |
|---|---|---|
| RQ1 | Publication-grade real corpus gate | PASS |
| RQ2.2 | Real EU law benchmark with four lexical baselines and 10k+ MC cases | PASS |
| RQ3_FIX2 | EU × US real-law collision benchmark | PASS |
| RQ4.1 | Official/public source fetch and source rebuild smoke test | PASS |
| RQ5.5 | CTHC-typed salted-domain routing robustness benchmark | PASS |

Unified result:

```text
final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
unified_audit_chain_complete: 1.0
```

---

## 7. RQ5.5 headline result

RQ5.5 is currently the strongest live robustness benchmark in this repo.

It runs over the RQ4.1 rebuilt public legal-text chunks.

Configuration:

```text
cases: 50,000
seed: 20260505
chunks: 110
corpora: 5
domain_hash_count: 5
```

HSRAG result:

```text
target_correct: 1.0
wrong_corpus_misrouting: 0.0
wrong_jurisdiction_misrouting: 0.0
unsupported_query_false_allow: 0.0
ambiguous_query_false_allow: 0.0
conflict_query_false_allow: 0.0
case_audit_chain_complete: 1.0
summary_audit_chain_complete: 1.0
p95_latency_ms: 0.5603
```

Compared with lexical baselines, HSRAG reduced token usage and estimated cost by approximately:

```text
≈ 85.76%
```

Important interpretation:

The global lexical baseline was faster in raw p95 latency, but it had non-zero misrouting and always retrieved for unsupported, ambiguous, and conflict-form queries.

HSRAG prioritizes:

```text
bounded retrieval
zero false allow
zero wrong-domain routing
auditability
lower token cost
```

rather than raw unbounded lookup speed alone.

---

## 8. How to run the LAW verification chain

From the repository root:

```powershell
python .\examples\hsrag_law\scripts\run_all_verifiers.py --rq5-cases 50000 --seed 20260505
```

Expected final output:

```text
HSRAG LAW — UNIFIED VERIFICATION INDEX
final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
unified_audit_chain_complete: 1.0
```

Run only RQ5.5:

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505
```

Run RQ4.1 source rebuild:

```powershell
python .\examples\hsrag_law\scripts\verify_rq4_official_fetch.py --min-ok 2
```

---

## 9. Repository layout

```text
HSRAG/
├─ README.md
├─ docs/
│  ├─ architecture.md
│  ├─ audit_model.md
│  ├─ governance.md
│  └─ hsrag_overview.md
├─ src/
│  ├─ cthc.py
│  ├─ evidence_assembler.py
│  ├─ guard.py
│  └─ hash_router.py
├─ tests/
│  ├─ test_audit_chain.py
│  ├─ test_guard.py
│  └─ test_hash_router.py
└─ examples/
   └─ hsrag_law/
      ├─ README.md
      ├─ data/
      ├─ results/
      ├─ scripts/
      └─ run_demo.py
```

---

## 10. Current limitations

Current limitations:

- This repository is a research / benchmark demo, not a production system.
- HSRAG LAW is not legal advice.
- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3 corpus from raw official source files.
- Some source rebuilds rely on official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- The current demo is a retrieval architecture benchmark, not a legal reasoning benchmark.

---

## 11. Roadmap

Planned next steps:

1. Add a clean custom-corpus template so users can paste their own public legal text and run the same routing benchmark.
2. Add full manifest-based corpus ingestion with explicit source license and provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add README-level benchmark reproduction instructions.
6. Add a public report summarizing RQ1–RQ5.5.
7. Separate lightweight demo scripts from heavier benchmark artifacts.
8. Prepare an EV / grant evidence section based on the reproducible benchmark chain.

---

## 12. One-line summary

HSRAG demonstrates that **typed hash-addressed retrieval** can reduce cross-domain evidence risk, reject unsupported or ambiguous queries before retrieval, preserve auditability, and significantly reduce token cost in reproducible benchmark settings.