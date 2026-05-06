# HSRAG

![RQ5.5](https://img.shields.io/badge/RQ5.5-50k_PASS-green)
![target_correct](https://img.shields.io/badge/target_correct-1.000-brightgreen)
![false_allow](https://img.shields.io/badge/false_allow-0.000-brightgreen)
![cost_reduction](https://img.shields.io/badge/cost_reduction-85.76%25-blue)
![audit_chain](https://img.shields.io/badge/audit_chain-complete-brightgreen)

**HSRAG** stands for **Hash-Structured Retrieval-Augmented Generation**.

Traditional RAG systems often ask:

    Which text is semantically similar?

HSRAG first asks:

    Which bounded, auditable knowledge address is this query allowed to touch?

The goal is to make AI retrieval more:

- bounded,
- auditable,
- domain-aware,
- token-efficient,
- and resistant to cross-domain evidence mixing.

HSRAG is not intended to replace all RAG systems.

Instead, it separates **addressing** from **reasoning** so that retrieval can be narrowed, checked, and audited before generation or semantic reasoning happens.

---

## 1. Why HSRAG matters

AI retrieval can fail in predictable ways:

- retrieving from the wrong domain,
- mixing evidence across jurisdictions or corpora,
- answering unsupported or ambiguous queries,
- spending too many tokens on irrelevant context,
- and leaving weak audit trails.

HSRAG introduces a structured routing layer before retrieval.

A simplified flow:

    query
    → normalize
    → CTHC typed route
    → salted domain hash
    → bounded retrieval
    → evidence gate
    → audit chain
    → output

This makes retrieval more conservative, more inspectable, and less likely to mix evidence across unrelated domains.

---

## 2. Core idea

HSRAG separates two operations that are often mixed together:

| Layer | Question | Purpose |
|---|---|---|
| Addressing | Where is this query allowed to retrieve from? | Bound the search space |
| Retrieval | Which evidence inside that bounded space is relevant? | Select candidate evidence |
| Evidence gate | Is the result supported, ambiguous, or unsafe? | Allow / reject / warn |
| Audit | Can the decision be reproduced? | Preserve traceability |

This repo currently focuses on a research / benchmark implementation.

It is not a production system yet.

---

## 3. Main components

### CTHC typed address

CTHC is used as a structured classification and addressing layer.

For legal text, a simplified CTHC path may look like:

    LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
    LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL

This means a chunk is not just plain text.  
It also carries a typed address.

---

### Salted domain hash

Each domain receives a salted hash bucket:

    domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)

Retrieval is only allowed inside the matching salted domain bucket.

This helps reduce:

- corpus collision,
- wrong-domain retrieval,
- jurisdiction mixing,
- and cross-domain evidence leakage.

---

### Evidence gate

HSRAG does not automatically retrieve for every query.

It can reject:

    unsupported query
    ambiguous query
    conflict-form query
    unroutable query

before evidence retrieval.

---

### Audit chain

HSRAG writes auditable records for benchmark cases and summary decisions.

This makes results easier to inspect, reproduce, and challenge.

---

## 4. Current implementation status

The main live demo is:

    examples/hsrag_law/

Current status:

    Research demo / early open-source implementation

The current repo includes:

- HSRAG LAW benchmark scripts,
- RQ1–RQ5.5 verification chain,
- CTHC salted-domain routing demo,
- audit-chain outputs,
- and a custom corpus template for clean public legal text.

---

## 5. HSRAG LAW demo

**HSRAG LAW** is a legal-text retrieval demonstration.

It tests whether legal retrieval can be made more bounded and auditable by using:

    CTHC typed legal routing
    + salted domain hashes
    + bounded retrieval
    + evidence gating
    + audit chains

The LAW demo is located here:

    examples/hsrag_law/

This demo is not legal advice, not a production legal search engine, and not a claim of complete official-law coverage.

It is a retrieval architecture benchmark.

---

## 6. Quick benchmark results

| Stage | Cases | Main purpose | HSRAG target_correct | False allow | Cost / token reduction | Status |
|---|---:|---|---:|---:|---:|---|
| RQ1 | corpus gate | Publication-grade real corpus gate | 1.000 | 0.000 | n/a | PASS |
| RQ2.2 | 10,176 | Real EU law + four lexical baselines | 1.000 | 0.000 | 73.33% cost reduction | PASS |
| RQ3_FIX2 | 14,208 | EU × US real-law collision benchmark | 1.000 | 0.000 | 73.55% cost reduction | PASS |
| RQ4.1 | source rebuild | Official/public source fetch + rebuild smoke test | n/a | n/a | n/a | PASS |
| RQ5.5 | 50,000 | CTHC salted-domain routing robustness | 1.000 | 0.000 | ≈ 85.76% token / cost reduction | PASS |

Unified result:

    final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
    unified_audit_chain_complete: 1.0

---

## 7. RQ5.5 headline result

RQ5.5 is currently the strongest live robustness benchmark in this repo.

It runs over the RQ4.1 rebuilt public legal-text chunks.

Configuration:

    cases: 50,000
    seed: 20260505
    chunks: 110
    corpora: 5
    domain_hash_count: 5

HSRAG result:

    target_correct: 1.0
    wrong_corpus_misrouting: 0.0
    wrong_jurisdiction_misrouting: 0.0
    unsupported_query_false_allow: 0.0
    ambiguous_query_false_allow: 0.0
    conflict_query_false_allow: 0.0
    case_audit_chain_complete: 1.0
    summary_audit_chain_complete: 1.0
    p95_latency_ms: 0.5603

Compared with lexical baselines, HSRAG reduced token usage and estimated cost by approximately:

    ≈ 85.76%

Important interpretation:

The global lexical baseline was faster in raw p95 latency, but it had non-zero misrouting and always retrieved for unsupported, ambiguous, and conflict-form queries.

HSRAG prioritizes:

    bounded retrieval
    zero false allow
    zero wrong-domain routing
    auditability
    lower token cost

rather than raw unbounded lookup speed alone.

---

## 8. Run the LAW verification chain

Recommended environment:

    Python 3.10+
    pip
    Git

Install dependencies from the repository root:

    pip install -r requirements.txt

Run the full LAW verification chain:

    python .\examples\hsrag_law\scripts\run_all_verifiers.py --rq5-cases 50000 --seed 20260505

Expected final output:

    HSRAG LAW — UNIFIED VERIFICATION INDEX
    final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
    unified_audit_chain_complete: 1.0

Run only RQ5.5:

    python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505

Run RQ4.1 source rebuild:

    python .\examples\hsrag_law\scripts\verify_rq4_official_fetch.py --min-ok 2

---

## 9. Custom corpus template

HSRAG LAW also includes a custom corpus template for users who want to test their own clean, legally usable public legal text.

Location:

    examples/hsrag_law/custom_template/

Basic workflow:

1. Put clean public legal text into:

    examples/hsrag_law/custom_template/input/legal_texts/

2. Edit the manifest:

    examples/hsrag_law/custom_template/input/manifest.example.json

3. Build the custom corpus:

    python .\examples\hsrag_law\custom_template\scripts\build_custom_corpus.py

4. Run the custom benchmark:

    python .\examples\hsrag_law\custom_template\scripts\run_custom_benchmark.py

Current smoke-test result:

    decision: CUSTOM_CORPUS_BUILD_PASS
    decision: CUSTOM_BENCHMARK_PASS
    target_correct: 1.0
    unsupported_query_false_allow: 0.0
    ambiguous_query_false_allow: 0.0
    conflict_query_false_allow: 0.0
    audit_chain_complete: 1.0

This template is designed for clean plaintext / markdown legal text first.

PDF extraction, browser automation, and official bulk ingestion are planned as separate ingestion tools.

---

## 10. Repository layout

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
          ├─ custom_template/
          │  ├─ README.md
          │  ├─ QSVCS_PUBLIC_TEMPLATE.md
          │  ├─ input/
          │  │  ├─ manifest.example.json
          │  │  └─ legal_texts/
          │  │     └─ example_law.txt
          │  ├─ output/
          │  └─ scripts/
          │     ├─ build_custom_corpus.py
          │     └─ run_custom_benchmark.py
          ├─ data/
          ├─ results/
          ├─ scripts/
          │  ├─ run_all_verifiers.py
          │  ├─ verify_rq4_official_fetch.py
          │  └─ verify_rq5_mc_reproduction.py
          └─ run_demo.py

---

## 11. Store classification summary

HSRAG LAW follows a three-store governance model:

| Store | Meaning | LAW usage |
|---|---|---|
| FHS | Fact Hash Store | Verified, source-linked, versioned legal text |
| EHS | Ephemeral Hash Store | Pending, unverified, temporary, or user-provided material |
| CHS | Creative / Challenge Hash Store | Synthetic, ambiguous, conflict, or failure-case material |

Default rule:

    Verified legal text → FHS
    Unverified or pending legal text → EHS
    Synthetic, ambiguous, conflict, or failure-case material → CHS

For legal and regulatory retrieval:

    FHS > EHS > CHS

EHS and CHS must not override matched FHS evidence.

If a query cannot be grounded in matched FHS evidence, HSRAG should reject, warn, or return a no-evidence decision rather than generate an unsupported legal answer.

This is a retrieval-governance rule, not legal advice.

---

## 12. Current limitations

Current limitations:

- This repository is a research / benchmark demo, not a production system.
- HSRAG LAW is not legal advice.
- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3_FIX2 corpus from raw official source files.
- Some source rebuilds rely on official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- The current demo is a retrieval architecture benchmark, not a legal reasoning benchmark.
- The custom corpus template currently supports clean plaintext / markdown input first.

---

## 13. Roadmap

Planned next steps:

1. Expand the custom-corpus template with stronger manifest validation and multi-file examples.
2. Add full manifest-based corpus ingestion with explicit source license and provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add a longer store-classification reference document.
6. Add README-level benchmark reproduction instructions.
7. Add a public report summarizing RQ1–RQ5.5.
8. Separate lightweight demo scripts from heavier benchmark artifacts.
9. Prepare an EV / grant evidence section based on the reproducible benchmark chain.

---

## 14. One-line summary

HSRAG demonstrates that **typed hash-addressed retrieval** can reduce cross-domain evidence risk, reject unsupported or ambiguous queries before retrieval, preserve auditability, and significantly reduce token cost in reproducible benchmark settings.