# HSRAG

![RQ5.5](https://img.shields.io/badge/RQ5.5-50k_PASS-green)
![RQ6](https://img.shields.io/badge/RQ6-20k_STRESS_PASS-brightgreen)
![RQ6_rows](https://img.shields.io/badge/RQ6_rows-720k-blue)
![target_correct](https://img.shields.io/badge/target_correct-1.000-brightgreen)
![false_allow](https://img.shields.io/badge/false_allow-0.000-brightgreen)
![cost_reduction](https://img.shields.io/badge/cost_reduction-85.76%25-blue)
![audit_chain](https://img.shields.io/badge/audit_chain-complete-brightgreen)

**HSRAG** stands for **Hash-Structured Retrieval-Augmented Generation**.

HSRAG is an experimental retrieval architecture for making AI retrieval more:

- bounded,
- auditable,
- domain-aware,
- token-efficient,
- and resistant to cross-domain or cross-jurisdiction evidence mixing.

In plain language:

> HSRAG is not about making the model guess better.  
> It is about making retrieval guess less, search inside the right evidence boundary, and leave an audit trail.

HSRAG is not intended to replace all RAG systems.

Instead, it adds a **boundary and audit layer before retrieval**, so retrieval can be narrowed, checked, and audited before generation or semantic reasoning happens.

---

## Quick Links
<!-- HSRAG_API_SQLITE_QUICK_LINK -->
- [HSRAG API SQLite demo](examples/hsrag_api_sqlite/) — local verified prototype for hash-addressed API specification management.
<!-- /HSRAG_API_SQLITE_QUICK_LINK -->


- [HSRAG core package](src/hsrag/)
- [HSRAG LAW demo](examples/hsrag_law/)
- [RQ6 Conversational Legal Collision Benchmark](examples/hsrag_law/rq6/)
- [RQ6 Smoke / Stress Report](examples/hsrag_law/rq6/RQ6_SMOKE_REPORT.md)
- [Custom corpus template](examples/hsrag_law/custom_template/)
- [FAQ](docs/FAQ.md)
- [Project Manifesto](docs/project_manifesto.md)
- [HSRAG 6.3 × TACL Integrated Architecture](docs/hsrag_6_3_tacl_architecture.md)

---

## What Is HSRAG?

Most RAG systems start by asking:

```text
Which text is semantically similar?
```

HSRAG first asks a different question:

```text
Which bounded, auditable knowledge address is this query allowed to search?
```

A simple analogy:

```text
RAG searches by similarity.
HSRAG first narrows the library shelf.
```

Then retrieval happens inside that bounded shelf.

This means HSRAG depends on clean pre-classification, such as:

```text
corpus
jurisdiction
legal unit
source hash
chunk hash
evidence hash
```

This makes it especially suitable for domains where wrong evidence retrieval is costly, such as:

- law,
- compliance,
- finance,
- healthcare,
- standards,
- internal policy,
- and other high-traceability knowledge systems.

It is less suitable for unrestricted open-ended exploration where there is no stable source base, no reliable classification, or no meaningful retrieval boundary.

---

## How Is HSRAG Different from RAG?

Traditional RAG often sends a query into a broad semantic search space.

HSRAG first performs:

```text
classification
→ typed addressing
→ boundary checks
→ constrained retrieval
→ evidence gate
→ audit logging
```

Then semantic retrieval or lexical retrieval can happen inside the allowed boundary.

| Layer | Traditional RAG | HSRAG |
|---|---|---|
| First question | Which text is similar? | Which bounded address is allowed? |
| Search scope | Often broad / global | Corpus, jurisdiction, source, and unit bounded |
| Failure handling | May still retrieve something plausible | Can return `NO_EVIDENCE`, `AMBIGUOUS`, or warning |
| Auditability | Depends on implementation | Source hash / evidence hash / audit row hash |
| Strength | Flexible semantic recall | Boundary control and traceability |
| Weakness | Can mix contexts or domains | Depends on clean upfront classification |

HSRAG can still use BM25, TF-IDF, vector search, or hybrid retrieval internally.

The key difference is that HSRAG tries to determine the allowed search boundary **before** retrieval.

---

## Why Can the Benchmark Numbers Be High?

Some HSRAG benchmark numbers are high because the task is not unrestricted general reasoning.

HSRAG performs well when:

```text
1. the corpus is pre-classified,
2. each chunk has source and corpus metadata,
3. the query can be mapped to a stable retrieval boundary,
4. ambiguous or unavailable evidence is allowed to be rejected,
5. retrieval is evaluated against evidence matching rather than broad legal reasoning.
```

This is intentional.

HSRAG does not claim to be smarter than every RAG system.

It claims that in structured domains, retrieval can become safer and more auditable when the system first asks:

```text
Where is this query allowed to search?
```

In the LAW benchmarks, HSRAG’s advantage comes from:

- corpus boundaries,
- jurisdiction boundaries,
- CTHC typed routing,
- hash-addressed chunks,
- source hash tracking,
- evidence gating,
- and audit-chain output.

If the upfront classification is wrong, incomplete, or too coarse, HSRAG can also fail or stabilize the wrong boundary.

That is why source normalization, corpus manifests, failure samples, and audit logs are part of the design.

---

## Quick Start: Minimal LAW Smoke Demo
<!-- HSRAG_API_SQLITE_QUICKSTART -->
### API SQLite demo

From the repository root:

    cd examples/hsrag_api_sqlite
    python .\scripts\verify_local.py

Expected verifier result:

    "status": "passed"

This demo is local-only, zero-secret, and zero-network.
<!-- /HSRAG_API_SQLITE_QUICKSTART -->


To run the smallest public LAW demo from the repository root:

```powershell
python .\examples\hsrag_law\run_demo.py
```

Expected result:

```text
SMOKE_TEST_PASS
```

This smoke demo shows the minimal HSRAG LAW flow:

```text
legal query
→ CTHC-style domain classification
→ hash-structured routing
→ bounded retrieval
→ guard decision
→ audit hash chain
→ benchmark summary
```

For larger benchmark reproduction, see:

[HSRAG LAW demo](examples/hsrag_law/)

---

## RQ6 One-Click Demos

RQ6 tests conversational legal retrieval contamination.

It asks:

> If a user first asks about an EU law and then asks about a similar U.S. law, will the retrieval system correctly switch corpus and jurisdiction?

Example:

```text
Turn 1: Find EU AI Act Article 5 prohibited AI practices.
Turn 2: Now find U.S. FTC Act Section 5 on unfair or deceptive acts or practices.
```

A contaminated retrieval system may incorrectly carry over the EU context into the U.S. turn.

### Windows PowerShell

Quick smoke demo:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_smoke.ps1
```

Standard benchmark:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_standard.ps1
```

Stress benchmark:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_stress.ps1
```

Backward-compatible full alias:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_full.ps1
```

### Linux / macOS / Git Bash / WSL

Quick smoke demo:

```bash
bash examples/hsrag_law/rq6/run_rq6_smoke.sh
```

Standard benchmark:

```bash
bash examples/hsrag_law/rq6/run_rq6_standard.sh
```

Stress benchmark:

```bash
bash examples/hsrag_law/rq6/run_rq6_stress.sh
```

Backward-compatible full alias:

```bash
bash examples/hsrag_law/rq6/run_rq6_full.sh
```

Demo levels:

| Script | MC | Expected rows | Purpose |
|---|---:|---:|---|
| `run_rq6_smoke` | 30 | 1,080 | Quick sanity check |
| `run_rq6_standard` | 3,000 | 108,000 | Standard smoke benchmark |
| `run_rq6_stress` | 20,000 | 720,000 | Stress benchmark |
| `run_rq6_full` | 20,000 | 720,000 | Backward-compatible alias for stress |

---

## Plain-Language Analogy

A normal RAG system is like searching an entire library for the paragraph that sounds most similar.

HSRAG first checks the catalog:

```text
Which shelf is this query allowed to search?
Which source does this shelf come from?
Which jurisdiction does it belong to?
Can this result be audited?
```

Only then does retrieval happen inside the allowed shelf.

Another analogy is a maze.

Traditional RAG may move through the maze by semantic similarity.

HSRAG adds walls, labels, and gates before retrieval, so the search is less likely to exit through the wrong legal domain.

This does not make RAG useless.

It makes retrieval more governed when the cost of wrong evidence is high.

---

## CTHC: Typed Retrieval Addressing

CTHC is a typed addressing and constraint layer.

It describes where a knowledge chunk belongs and what boundary it should be retrieved under.

For legal text, a simplified CTHC path may look like:

```text
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.ARTICLE_5
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.SECTION_230
```

CTHC does not try to “understand everything.”

It performs a more conservative function:

```text
Before retrieval, decide whether this query can enter a stable knowledge boundary.
```

---

## Example: Hash Chunk as an Auditable Address

A legal evidence chunk is not stored as plain text only.

It is attached to a typed address and source hash:

```text
mem://law/EU/EU_AI_ACT/Article_5/Chunk_0001
  corpus         = EU_AI_ACT
  jurisdiction   = EU
  unit           = Article_5
  chunk_id       = EU_AI_ACT_RQ4_CHUNK_0001
  source_hash    = sha256:...
  evidence_hash  = sha256:...
```

This creates a hierarchy:

```text
Law
└── EU
    └── EU_AI_ACT
        └── Article_5
            └── Chunk_0001
                └── source_hash
```

The goal is to make retrieval bounded and auditable before generation.

---

## Three-Store Model

HSRAG uses a three-store governance model:

| Store | Meaning | Example |
|---|---|---|
| FHS | Fact Hash Store | Verified, source-linked legal text |
| EHS | Ephemeral Hash Store | Pending, temporary, user-provided, or not-yet-verified material |
| CHS | Creative / Challenge Hash Store | Synthetic, ambiguous, conflict, or failure-case material |

Default legal retrieval priority:

```text
FHS > EHS > CHS
```

EHS and CHS should not override matched FHS evidence.

If no matched FHS evidence exists, HSRAG should return:

```text
NO_EVIDENCE
AMBIGUOUS
WARNING
```

instead of forcing an unsupported legal answer.

This is a retrieval-governance rule, not legal advice.

---

## Why HSRAG May Reject a Query

HSRAG does not try to answer every query.

In high-risk retrieval settings, refusing unsupported or ambiguous retrieval can be safer than forcing a plausible but wrong answer.

### `NO_EVIDENCE`

`NO_EVIDENCE` means the query asks for a corpus or legal unit that is not available in the current indexed corpus.

Example:

```text
Now find EU GDPR Article 8 on children's consent.
```

If the current run does not include `EU_GDPR` chunks, HSRAG should not force a result from `US_COPPA`, `EU_AI_ACT`, or any other nearby corpus.

The correct retrieval decision is:

```text
NO_EVIDENCE
```

### `AMBIGUOUS`

`AMBIGUOUS` means the query does not provide enough stable routing information.

Example:

```text
Now explain Article 5 obligations.
```

`Article 5` is not a unique legal address. It may refer to many different laws across different jurisdictions or corpora.

The correct retrieval decision is:

```text
AMBIGUOUS
```

The system should ask for a clearer legal target or require query decomposition instead of guessing from conversational carryover.

### Design Principle

```text
HSRAG prefers conservative refusal over wrong legal evidence matching.
```

In RQ6, a rejected query can be a correct result when the evidence boundary is missing, unstable, or unavailable.

---

## Atomic Legal Retrieval First

RQ6 v0.1 evaluates atomic or two-turn legal retrieval tasks.

The current HSRAG CTHC router is intentionally boundary-first and single-scope oriented.

A single retrieval call should target one legal corpus, jurisdiction, and legal unit whenever possible.

For multi-statute or comparative legal questions, such as comparing EU AI Act Article 5 with U.S. FTC Act Section 5, the query should first be decomposed into separate atomic retrieval tasks.

Recommended flow:

```text
User asks multi-law question
  ↓
Query decomposition layer
  ↓
Atomic retrieval task 1
Atomic retrieval task 2
Atomic retrieval task 3
  ↓
Each task receives its own:
- route_status
- source_hash
- evidence_hash
- audit_row_hash
  ↓
Answer synthesis / legal comparison layer
```

Multi-law comparison should happen after retrieval, not inside the retrieval boundary itself.

This is a governance choice, not merely a technical limitation.

---

## Reproduce Benchmark Evidence

For the RQ6 conversational legal collision benchmark:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_standard.ps1
```

For the RQ6 stress benchmark:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_stress.ps1
```

For the full LAW verification chain:

```powershell
python .\examples\hsrag_law\scripts\run_all_verifiers.py --rq5-cases 50000 --seed 20260505
```

For only the RQ5.5 robustness benchmark:

```powershell
python .\examples\hsrag_law\scripts\verify_rq5_mc_reproduction.py --cases 50000 --seed 20260505
```

For custom public legal text:

```powershell
python .\examples\hsrag_law\custom_template\scripts\build_custom_corpus.py
python .\examples\hsrag_law\custom_template\scripts\run_custom_benchmark.py
```

---

## Benchmark Artifact Map

Main RQ1–RQ5.5 benchmark outputs are written under:

```text
examples/hsrag_law/results/
```

Key files:

| Artifact | Meaning |
|---|---|
| `unified_verification_index.md` | Final RQ1–RQ5.5 verification index |
| `unified_verification_index.json` | Machine-readable unified verification summary |
| `rq5_mc_reproduction_summary.md` | RQ5.5 benchmark summary |
| `rq5_mc_reproduction_summary.json` | Machine-readable RQ5.5 summary |
| `rq5_case_results.csv` | Case-level RQ5.5 results |
| `rq5_baseline_comparison.csv` | Baseline comparison, token, cost, and latency metrics |
| `rq5_gate_checks.csv` | Acceptance gate checks |
| `rq5_audit_chain.jsonl` | RQ5.5 audit-chain trace |

RQ6 benchmark outputs are written under:

```text
runs/rq6_conversational_collision_<timestamp>/
```

Key RQ6 files:

| Artifact | Meaning |
|---|---|
| `rq6_summary.json` | Summary metrics by mode and context policy |
| `rq6_run_manifest.json` | Run configuration, corpus metadata, and config hash |
| `rq6_failure_samples.csv` | Replayable failure samples |
| `rq6_full_results.csv` | Full row-level benchmark output |
| `rq6_mode_comparison.md` | Human-readable mode comparison |
| `rq6_claim_boundary.md` | Claim boundary and limitation notes |

Do not delete failure samples or manifests if you want reproducible audit trails.

---

## Why HSRAG Matters

AI retrieval can fail in predictable ways:

- retrieving from the wrong domain,
- mixing evidence across jurisdictions or corpora,
- answering unsupported or ambiguous queries,
- spending too many tokens on irrelevant context,
- and leaving weak audit trails.

HSRAG introduces a structured routing layer before retrieval.

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

This makes retrieval more conservative, more inspectable, and less likely to mix evidence across unrelated domains.

RQ6 specifically tests the “mixing evidence across jurisdictions or corpora” failure mode in multi-turn legal conversations.

---

## Core Idea

HSRAG separates operations that are often mixed together:

| Layer | Question | Purpose |
|---|---|---|
| Addressing | Where is this query allowed to retrieve from? | Bound the search space |
| Retrieval | Which evidence inside that bounded space is relevant? | Select candidate evidence |
| Evidence gate | Is the result supported, ambiguous, or unsafe? | Allow / reject / warn |
| Audit | Can the decision be reproduced? | Preserve traceability |

This repository currently focuses on a research / benchmark implementation.

It is not a production system yet.

---

## Main Components

### CTHC Typed Address

CTHC is used as a structured classification and addressing layer.

For legal text, a simplified CTHC path may look like:

```text
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
```

This means a chunk is not just plain text.

It also carries a typed address.

### Salted Domain Hash

Each domain receives a salted hash bucket:

```text
domain_hash = sha256(salt || domain || source_type || jurisdiction || corpus_id)
```

Retrieval is only allowed inside the matching salted domain bucket.

This helps reduce:

- corpus collision,
- wrong-domain retrieval,
- jurisdiction mixing,
- and cross-domain evidence leakage.

### Evidence Gate

HSRAG does not automatically retrieve for every query.

It can reject:

```text
unsupported query
ambiguous query
conflict-form query
unroutable query
```

before evidence retrieval.

### Audit Chain

HSRAG writes auditable records for benchmark cases and summary decisions.

This makes results easier to inspect, reproduce, and challenge.

---

## Current Implementation Status
<!-- HSRAG_API_SQLITE_STATUS -->
- HSRAG API SQLite verified prototype for hash-addressed API specification management.
<!-- /HSRAG_API_SQLITE_STATUS -->


The main live demo is:

```text
examples/hsrag_law/
```

Current status:

```text
Research demo / early open-source implementation
```

The current repository includes:

- HSRAG LAW benchmark scripts,
- RQ1–RQ5.5 verification chain,
- RQ6 conversational legal collision benchmark,
- CTHC salted-domain routing demo,
- audit-chain outputs,
- custom corpus template for clean public legal text,
- project manifesto,
- FAQ,
- and future HSRAG 6.3 × TACL architecture documentation.

For project boundaries, update cadence, communication preference, fork policy, commercialization notes, and core invariants, see:

[HSRAG Project Manifesto](docs/project_manifesto.md)

For common questions about HSRAG, CTHC, RAG complementarity, benchmark meaning, custom corpus usage, edge hash pointers, AI memory, and forks, see:

[HSRAG FAQ](docs/FAQ.md)

---

## Core Package Status

The reusable core package is located under:

```text
src/hsrag/
```

It currently contains minimal, tested primitives for:

- shared benchmark types,
- deterministic hashing,
- audit-chain verification,
- CTHC route-opener detection,
- salted domain hash routing,
- conservative route guarding,
- and audit-ready evidence assembly.

The package is intentionally minimal and is being extracted from the working RQ1–RQ6 benchmark code.

Run core tests from the repository root:

```powershell
python -m pytest tests
```

The full benchmark scripts still live under:

```text
examples/hsrag_law/
```

---

## Future Integrated Architecture

The long-term target architecture is documented here:

[HSRAG 6.3 × TACL Integrated Architecture](docs/hsrag_6_3_tacl_architecture.md)

This architecture describes **HSRAG 6.3 × TACL**, a future integrated design that separates:

- governance evolution,
- runtime query execution,
- CTHC typed routing,
- hash-bounded retrieval,
- guard enforcement,
- TACL runtime control,
- audit telemetry,
- and memory writeback.

The current repository implements a reproducible benchmark foundation, especially through HSRAG LAW.

The full HSRAG 6.3 × TACL stack remains a forward architecture target.

---

## HSRAG LAW Demo

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

This demo is not legal advice, not a production legal search engine, and not a claim of complete official-law coverage.

It is a retrieval architecture benchmark.

---

## Quick Benchmark Results

| Stage | Cases | Main purpose | HSRAG target_correct | False allow / contamination | Cost / token reduction | Status |
|---|---:|---|---:|---:|---:|---|
| RQ1 | corpus gate | Publication-grade real corpus gate | 1.000 | 0.000 | n/a | PASS |
| RQ2.2 | 10,176 | Real EU law + four lexical baselines | 1.000 | 0.000 | 73.33% cost reduction | PASS |
| RQ3_FIX2 | 14,208 | EU × US real-law collision benchmark | 1.000 | 0.000 | 73.55% cost reduction | PASS |
| RQ4.1 | source rebuild | Official/public source fetch + rebuild smoke test | n/a | n/a | n/a | PASS |
| RQ5.5 | 50,000 | CTHC salted-domain routing robustness | 1.000 | 0.000 | ≈ 85.76% token / cost reduction | PASS |
| RQ6 v0.1.1 | 20,000 MC / 720,000 rows | Conversational EU/US legal collision stress benchmark | 1.000 on HSRAG modes | 0.000 on HSRAG modes | n/a | STRESS PASS |

Unified RQ1–RQ5.5 result:

```text
final_decision: HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS
unified_audit_chain_complete: 1.0
```

---

## RQ5.5 Headline Result

RQ5.5 is the main salted-domain routing robustness benchmark.

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

## RQ6 Headline Result

RQ6 is the main conversational legal collision benchmark.

It tests multi-turn legal retrieval contamination when switching between similar EU and U.S. legal concepts.

Configuration:

```text
mc: 20,000
rows: 720,000
corpora: EU_AI_ACT, EU_DMA, US_CDA230, US_COPPA, US_FTC_ACT5
demo_mode: False
```

HSRAG CTHC result:

```text
target_correct: 1.000
hit_target_correct: 1.000
wrong_corpus_collision: 0.000
wrong_jurisdiction_escape: 0.000
no_evidence_false_allow: 0.000
ambiguous_false_allow: 0.000
cross_turn_contamination: 0.000
switch_turn_contamination: 0.000
failure_sample_count: 0
p95_latency_ms: 1.600
```

HSRAG Hybrid Subset result:

```text
target_correct: 1.000
hit_target_correct: 1.000
wrong_corpus_collision: 0.000
wrong_jurisdiction_escape: 0.000
no_evidence_false_allow: 0.000
ambiguous_false_allow: 0.000
cross_turn_contamination: 0.000
switch_turn_contamination: 0.000
failure_sample_count: 0
p95_latency_ms: 9.036
```

Important interpretation:

RQ6 shows that naive conversational memory can contaminate baseline retrieval when switching between similar EU and U.S. legal concepts.

HSRAG CTHC keeps retrieval bounded by corpus and jurisdiction before evidence selection.

This is a real/public rebuilt corpus stress benchmark, not a production or legal-advice claim.

---

## Run the LAW Verification Chain

Recommended environment:

```text
Python 3.10+
pip
Git
```

Install dependencies from the repository root:

```powershell
pip install -r requirements.txt
```

Run the full LAW verification chain:

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

Run RQ6 quick smoke:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_smoke.ps1
```

Run RQ6 standard:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_standard.ps1
```

Run RQ6 stress:

```powershell
powershell -ExecutionPolicy Bypass -File .\examples\hsrag_law\rq6\run_rq6_stress.ps1
```

---

## Custom Corpus Template

HSRAG LAW also includes a custom corpus template for users who want to test their own clean, legally usable public legal text.

Location:

```text
examples/hsrag_law/custom_template/
```

Basic workflow:

1. Put clean public legal text into:

```text
examples/hsrag_law/custom_template/input/legal_texts/
```

2. Edit the manifest:

```text
examples/hsrag_law/custom_template/input/manifest.example.json
```

3. Build the custom corpus:

```powershell
python .\examples\hsrag_law\custom_template\scripts\build_custom_corpus.py
```

4. Run the custom benchmark:

```powershell
python .\examples\hsrag_law\custom_template\scripts\run_custom_benchmark.py
```

Current smoke-test result:

```text
decision: CUSTOM_CORPUS_BUILD_PASS
decision: CUSTOM_BENCHMARK_PASS
target_correct: 1.0
unsupported_query_false_allow: 0.0
ambiguous_query_false_allow: 0.0
conflict_query_false_allow: 0.0
audit_chain_complete: 1.0
```

This template is designed for clean plaintext / markdown legal text first.

PDF extraction, browser automation, and official bulk ingestion are planned as separate ingestion tools.

---

<!-- HSRAG_API_SQLITE_SECTION -->
## HSRAG API SQLite Demo

HSRAG API SQLite is a local-first verified prototype for managing API specifications as hash-addressed, versioned, and authority-gated records.

It demonstrates:

- CTHC hash pointer lookup
- TACL-lite authority layers
- FHS / CHS / EHS evidence isolation
- source_hash-based revision tracking
- local OpenAPI JSON import
- one-command local verification

Location:

    examples/hsrag_api_sqlite/

Run:

    cd examples/hsrag_api_sqlite
    python .\scripts\verify_local.py

This demo is local-only, zero-secret, and zero-network.

It is not a production API registry, API gateway, cloud service, or LLM API wrapper.

The goal is to show how API specs can be resolved through deterministic identity, authority layers, and auditable result contracts instead of vague semantic guessing.
<!-- /HSRAG_API_SQLITE_SECTION -->

## Documentation Map

| Document | Purpose |
|---|---|
<!-- HSRAG_API_SQLITE_DOCMAP -->
| [HSRAG API SQLite Demo](examples/hsrag_api_sqlite/) | Local verified prototype for hash-addressed API specification management with CTHC pointers, TACL-lite authority gates, and local OpenAPI JSON import. |
<!-- /HSRAG_API_SQLITE_DOCMAP -->
| [FAQ](docs/FAQ.md) | Common questions about HSRAG, RAG, CTHC, benchmarks, memory, and forks |
| [Project Manifesto](docs/project_manifesto.md) | Project boundary, update cadence, communication style, fork policy, commercialization stance, and invariants |
| [HSRAG 6.3 × TACL Architecture](docs/hsrag_6_3_tacl_architecture.md) | Future integrated architecture and roadmap target |
| [Architecture](docs/architecture.md) | General architecture notes |
| [Audit Model](docs/audit_model.md) | Audit and traceability notes |
| [Governance](docs/governance.md) | Governance-related notes |
| [HSRAG Overview](docs/hsrag_overview.md) | High-level project overview |
| [EV Evidence Section](docs/ev_evidence_section.md) | Grant / evidence-oriented summary notes |
| [HSRAG Core Package](src/hsrag/) | Minimal reusable core primitives extracted from RQ1–RQ6 |
| [RQ6 Benchmark](examples/hsrag_law/rq6/) | Conversational legal collision benchmark |
| [RQ6 Smoke / Stress Report](examples/hsrag_law/rq6/RQ6_SMOKE_REPORT.md) | RQ6 mc3000 / mc20000 results and claim boundary |

---

## Repository Layout

```text
HSRAG/
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ docs/
│  ├─ FAQ.md
│  ├─ architecture.md
│  ├─ audit_model.md
│  ├─ ev_evidence_section.md
│  ├─ governance.md
│  ├─ hsrag_6_3_tacl_architecture.md
│  ├─ hsrag_overview.md
│  └─ project_manifesto.md
├─ src/
│  └─ hsrag/
│     ├─ README.md
│     ├─ __init__.py
│     ├─ audit_chain.py
│     ├─ cthc.py
│     ├─ evidence_assembler.py
│     ├─ guard.py
│     ├─ hash_router.py
│     ├─ hashing.py
│     └─ types.py
├─ tests/
│  ├─ test_audit_chain.py
│  ├─ test_cthc.py
│  ├─ test_evidence_assembler.py
│  ├─ test_guard.py
│  └─ test_hash_router.py
└─ examples/
   └─ hsrag_law/
      ├─ README.md
      ├─ run_demo.py
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
      ├─ rq6/
      │  ├─ README.md
      │  ├─ RQ6_PROJECT_PROMPT.md
      │  ├─ RQ6_SMOKE_REPORT.md
      │  ├─ run_rq6_conversational_collision.py
      │  ├─ run_rq6_smoke.ps1
      │  ├─ run_rq6_smoke.sh
      │  ├─ run_rq6_standard.ps1
      │  ├─ run_rq6_standard.sh
      │  ├─ run_rq6_stress.ps1
      │  ├─ run_rq6_stress.sh
      │  ├─ run_rq6_full.ps1
      │  └─ run_rq6_full.sh
      ├─ data/
      ├─ results/
      └─ scripts/
         ├─ run_all_verifiers.py
         ├─ verify_rq1.py
         ├─ verify_rq2_2.py
         ├─ verify_rq3_fix2.py
         ├─ verify_rq4_official_fetch.py
         └─ verify_rq5_mc_reproduction.py
```

---

## Current Limitations

Current limitations:

- This repository is a research / benchmark demo, not a production system.
- HSRAG LAW is not legal advice.
- The current demo is a retrieval architecture benchmark, not a legal reasoning benchmark.
- HSRAG depends on clean pre-classification. If the corpus, jurisdiction, unit, or source metadata is wrong, HSRAG can stabilize the wrong boundary.
- RQ5.5 uses the RQ4.1 rebuilt corpus, currently 110 chunks and 5 corpora.
- RQ6 v0.1.1 evaluates atomic or two-turn legal retrieval tasks, not unrestricted single-query multi-law batch retrieval.
- Multi-law comparative questions should be decomposed into atomic retrieval tasks before HSRAG routing.
- The mc=20000 RQ6 result is a stress benchmark over the current rebuilt corpus, not a publication-grade final claim.
- RQ5.5 does not yet rerun the full RQ2.2 / RQ3_FIX2 corpus from raw official source files.
- Some source rebuilds rely on official/public references and fallbacks where direct official fetch is difficult.
- Some legal sources may require official bulk downloads, browser automation, PDF parsing, or manual source snapshots for full reproducibility.
- The custom corpus template currently supports clean plaintext / markdown input first.
- The HSRAG 6.3 × TACL document is a forward architecture target, not a claim of full implementation.
- HSRAG is an independent, AI-assisted research project and does not promise that every roadmap item will be implemented by the original author.

---

## Claim Boundary

Allowed claim:

```text
HSRAG demonstrates boundary-first, hash-addressed retrieval governance in reproducible legal retrieval benchmarks.
```

Allowed claim:

```text
RQ6 v0.1.1 demonstrates that HSRAG CTHC can reduce cross-jurisdiction context contamination in a controlled multi-turn legal retrieval benchmark.
```

Allowed claim:

```text
BM25 remains a strong lexical baseline, especially when domain hints are available.
```

Disallowed claim:

```text
HSRAG is production-ready.
```

Disallowed claim:

```text
HSRAG replaces all RAG systems.
```

Disallowed claim:

```text
HSRAG LAW provides legal advice.
```

Disallowed claim:

```text
A smoke or stress benchmark is automatically publication-grade evidence.
```

---

## Roadmap
<!-- HSRAG_API_SQLITE_ROADMAP -->
- Extend the API SQLite demo with larger OpenAPI fixtures, optional YAML support, and retrieval evaluation baselines.
<!-- /HSRAG_API_SQLITE_ROADMAP -->


Planned next steps:

1. Expand the custom-corpus template with stronger manifest validation and multi-file examples.
2. Add full manifest-based corpus ingestion with explicit source license and provenance metadata.
3. Add optional PDF extraction pipeline.
4. Add larger multi-jurisdiction source rebuilds.
5. Add a longer store-classification reference document.
6. Keep README-level benchmark reproduction instructions synchronized with RQ5.5 and RQ6.
7. Add a public report summarizing RQ1–RQ6.
8. Maintain separate lightweight / standard / stress demo scripts for RQ6.
9. Prepare a grant / evidence section based on the reproducible benchmark chain.
10. Continue developing the HSRAG 6.3 × TACL target architecture.
11. Add RQ6.1 query decomposition layer for multi-law comparative questions.
12. Extend RQ6 corpus coverage with EU_GDPR when available.
13. Gradually extract BM25, TF-IDF, hybrid retrieval, corpus loading, and benchmark metrics from RQ6 into `src/hsrag/`.

---

## One-Line Summary

HSRAG demonstrates that typed, hash-addressed, boundary-first retrieval can reduce cross-domain evidence risk, reject unsupported or ambiguous queries before retrieval, preserve auditability, reduce token cost, and control multi-turn context contamination in reproducible benchmark settings.
## HSRAG RQ7 Scale Benchmark

A local RQ7 benchmark scaffold is available under:

    examples/hsrag_law/rq7_scale/

RQ7 tests retrieval boundary control across:

- global search
- CTHC-pruned search
- unique address lookup

Current status:

- salted toy-real pipeline verified
- one-command verify available
- full-scale benchmark pending

Run:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py

Claim boundary:

RQ7 is currently a verified local benchmark pipeline, not a production retrieval system and not a claim that HSRAG replaces all RAG systems.


## RQ7 Public Report

The RQ7 public report is available here:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json`

Current scope:

- RQ4 rebuilt 889-chunk artifact connected
- scale tiers: 100 / 300 / 600 / 889
- actual elapsed timing available
- public report published
- full-scale benchmark pending
- vector / hybrid baselines pending
- unit derivation remains heuristic

Run release verify:

    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889


## RQ7 Release Checkpoint

RQ7 v0.1 release checkpoint files:

- `examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_RELEASE_CHECKPOINT.json`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT.md`
- `examples/hsrag_law/rq7_scale/05_reports/RQ7_PUBLIC_REPORT_SUMMARY.json`

Current claim boundary:

- RQ4 rebuilt 889-chunk artifact connected
- RQ4 metrics snapshot available
- RQ4 scale tiers available: 100 / 300 / 600 / 889
- Actual elapsed timing available
- Full-scale benchmark pending
- Vector / hybrid baselines pending
- Unit derivation remains heuristic
- Not legal advice

Verify:

    python -m pytest tests -k rq7
    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889

