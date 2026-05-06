
# HSRAG FAQ

This FAQ explains the basic ideas, scope, benchmark meaning, future directions, and project boundaries of HSRAG.

It is written for developers, researchers, enterprises, and community members who want a fast but accurate overview.

---

## A. Basic positioning

### Q1. What is HSRAG?

HSRAG stands for Hash-Structured Retrieval-Augmented Generation.

It is a retrieval architecture that places structured knowledge addressing before semantic retrieval or generation.

Traditional RAG often asks:

```
Which text is semantically similar?
```

HSRAG first asks:

```
Which bounded, auditable knowledge address is this query allowed to touch?
```

The goal is to reduce wrong-domain retrieval, unsupported answers, unnecessary token usage, and weak auditability.

---

### Q2. Where did the idea come from?

One major inspiration is library-style retrieval.

A library does not treat every book as one undifferentiated pile of text.

It uses classification systems, shelves, catalog records, indexes, and location addresses to narrow the search space before reading the book.

HSRAG applies a similar idea to AI retrieval:

* classify knowledge
* assign structured addresses
* restrict retrieval boundaries
* preserve evidence traceability
* audit the decision path

In simple terms, HSRAG is an attempt to build a library-like addressing layer for AI knowledge retrieval.

---

### Q3. Is HSRAG trying to replace RAG?

No.

HSRAG is not intended to replace all RAG systems.

It is better understood as a complementary architecture:

* HSRAG provides typed addressing, bounded retrieval, evidence gating, and audit traces.
* RAG / vector search can still be used inside the bounded search space.

Short version:

```
HSRAG addresses first.
RAG retrieves inside the bounded space.
```

---

### Q4. What problem does HSRAG try to solve?

HSRAG focuses on retrieval failures such as:

* wrong-domain retrieval
* wrong-jurisdiction retrieval
* unsupported query false allow
* ambiguous query false allow
* conflict-form query false allow
* cross-domain evidence mixing
* excessive token usage
* weak audit trails

It does not solve every possible AI failure mode.

It focuses on making retrieval more bounded, inspectable, and evidence-aware.

---

## B. RAG, hallucination, and complementarity

### Q5. Why can current RAG systems still hallucinate?

RAG can reduce hallucination, but it does not automatically guarantee correctness.

If retrieval returns the wrong evidence, mixes incompatible sources, or retrieves something for an unsupported query, the generator may still produce a fluent but wrong answer.

In many cases, hallucination is not only a model problem.

It is also a retrieval-boundary problem.

---

### Q6. What does HSRAG do differently?

HSRAG adds structure before retrieval.

Instead of immediately searching the entire corpus, it tries to resolve the query into a bounded, typed, auditable route.

Simplified flow:

```
query
→ normalize
→ CTHC typed address
→ salted domain hash
→ bounded retrieval
→ evidence gate
→ audit chain
→ output
```

This reduces the chance that the system retrieves evidence from the wrong domain.

---

### Q7. Does HSRAG eliminate hallucination?

No.

HSRAG does not guarantee zero hallucination in all settings.

It is designed to reduce specific retrieval-induced failure modes, especially:

* wrong-domain retrieval
* unsupported answer generation
* ambiguous query false allow
* evidence mixing across incompatible corpora
* lack of auditability

The language model may still make mistakes.

HSRAG aims to make the retrieval path more constrained and easier to inspect.

---

### Q8. How does HSRAG complement vector RAG?

Vector retrieval is useful for semantic similarity.

HSRAG does not reject that.

Instead, HSRAG can narrow the search space first, then allow vector search or fuzzy retrieval inside the bounded subset.

A practical hybrid pattern is:

```
CTHC / hash route
→ domain-pruned subset
→ vector retrieval or reranking
→ evidence gate
→ answer
```

This keeps semantic search, but reduces uncontrolled full-corpus retrieval.

---

## C. CTHC and library-style addressing

### Q9. What is CTHC?

CTHC means Cross-Tag Hash Code.

It is a structured classification and addressing layer.

It can be used to assign knowledge chunks a traceable semantic address, instead of treating them as plain text only.

For example, a legal chunk may carry an address such as:

```
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
```

or:

```
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
```

---

### Q10. How is CTHC similar to Dewey Decimal Classification or library indexing?

Dewey Decimal Classification and library catalogs help users narrow down where a book belongs before reading it.

CTHC plays a similar role for AI retrieval.

It tries to answer:

```
Which knowledge region does this query belong to?
```

before asking:

```
Which text looks semantically similar?
```

This makes CTHC closer to a classification-addressing layer than a pure search algorithm.

---

### Q11. Is CTHC only for law?

No.

HSRAG LAW is the first reproducible demo, but CTHC is not limited to legal text.

Potential domains include:

* enterprise policies
* compliance manuals
* medical or clinical guidelines, with proper validation
* financial policy documents
* technical standards
* API documentation
* game lore
* safety procedures
* personal or enterprise AI memory
* internal knowledge bases

Law is a strong first demo because legal retrieval naturally has jurisdiction, source, section, and authority boundaries.

---

### Q12. Is CTHC manually designed or automatically generated?

In the current demo, CTHC is mostly simplified and schema-driven.

Future versions may explore:

* manually defined enterprise schemas
* semi-automatic classification
* model-assisted tagging
* rule-based validation
* human review workflows

Fully automatic CTHC classification remains an open engineering and research problem.

---

## D. Hash, salt, and audit

### Q13. What is a salted domain hash?

A salted domain hash is a reproducible hash bucket for a retrieval domain.

It may combine fields such as:

* salt
* domain
* source type
* jurisdiction
* corpus ID

The purpose is to create a stable and auditable boundary for retrieval.

A query should only retrieve from the matching domain bucket unless the system explicitly allows another path.

---

### Q14. Why use salted domain hashes instead of only metadata filters?

Metadata filters are useful.

HSRAG does not reject metadata filtering.

The point of salted domain hashes is to make the domain boundary more explicit, reproducible, and audit-friendly.

A metadata filter may say:

```
jurisdiction = EU
```

A salted domain hash can make that boundary part of a traceable retrieval address.

The goal is not to replace all metadata.

The goal is to make retrieval boundaries harder to blur silently.

---

### Q15. What is evidence gating?

Evidence gating means the system checks whether retrieval should be allowed before generating an answer.

HSRAG may reject:

* unsupported queries
* ambiguous queries
* conflict-form queries
* unroutable queries
* domain mismatch cases

This allows refusal or no-evidence output before the model generates a fluent but unsupported answer.

---

### Q16. What does audit chain mean in HSRAG?

Audit chain means important retrieval or benchmark decisions leave reproducible traces.

Typical records may include:

* query hash
* route decision
* selected evidence hash
* gate decision
* answer hash
* summary metrics
* decision trace

This helps users inspect, reproduce, and challenge the result.

---

### Q17. Does HSRAG require blockchain?

No.

HSRAG does not require blockchain.

Audit chains can be simple local files, such as JSONL, CSV, or structured logs.

A blockchain or public ledger could be used in future scenarios where public timestamping or tamper-evidence is required, but it is not necessary for the current design.

---

## E. HSRAG LAW benchmark

### Q18. What is HSRAG LAW?

HSRAG LAW is a legal-text retrieval demo and benchmark.

It tests whether legal retrieval can be made more bounded and auditable by using:

* CTHC typed legal routing
* salted domain hashes
* bounded retrieval
* evidence gating
* audit chains

It is not legal advice.

It is a retrieval architecture benchmark.

---

### Q19. What does RQ5.5 show?

RQ5.5 is the current strongest live benchmark in the repository.

In the current run, it used:

* 50,000 cases
* 110 rebuilt public legal-text chunks
* 5 corpora
* 5 salted domain hash buckets

The HSRAG result showed:

* target_correct: 1.0
* wrong_corpus_misrouting: 0.0
* wrong_jurisdiction_misrouting: 0.0
* unsupported_query_false_allow: 0.0
* ambiguous_query_false_allow: 0.0
* conflict_query_false_allow: 0.0
* audit_chain_complete: 1.0
* token / cost reduction: approximately 85.76% versus lexical baselines in this benchmark setting

This is a strong benchmark result for the current demo.

It is not a claim that HSRAG is proven across all domains or all production workloads.

---

### Q20. What does RQ5.5 not prove?

RQ5.5 does not prove that:

* HSRAG is production-ready
* HSRAG eliminates all hallucination
* HSRAG fully solves legal reasoning
* HSRAG works equally well on all domains
* HSRAG scales automatically to every corpus size
* HSRAG replaces all vector retrieval systems

It proves that, under the benchmark setup, CTHC typed routing plus salted domain hash retrieval can reduce specific retrieval risks and produce reproducible audit outputs.

---

### Q21. Why can a lexical baseline sometimes be faster?

A lexical baseline can be faster because it may do a simpler lookup without the same routing, gating, and audit constraints.

Raw speed alone is not the only metric.

HSRAG prioritizes:

* bounded retrieval
* zero false allow in benchmark conditions
* zero wrong-domain routing in benchmark conditions
* auditability
* lower token cost

The global lexical baseline may be faster in raw p95 latency, but it may also retrieve for unsupported, ambiguous, or conflict-form queries.

---

### Q22. Is HSRAG LAW legal advice?

No.

HSRAG LAW is not legal advice.

It is not a production legal search engine.

It is not a claim of complete official-law coverage.

It is a benchmark demo for retrieval architecture.

---

## F. Custom corpus template

### Q23. Can users test their own legal text?

Yes.

The repository includes a custom corpus template for clean, legally usable public legal text.

Location:

```
examples/hsrag_law/custom_template/
```

Basic workflow:

1. Put clean public legal text into the input folder.
2. Edit the manifest.
3. Build the custom corpus.
4. Run the custom benchmark.
5. Review output files and audit traces.

This is designed for plaintext or markdown input first.

PDF extraction, browser automation, and official bulk ingestion are future ingestion directions.

---

### Q24. What should users put into the custom template?

Users should only use text they are allowed to process locally.

Suitable input:

* clean public legal text
* properly sourced public documents
* legally usable internal test text
* manually prepared plaintext or markdown
* documents with clear source metadata

Users should not place private, confidential, copyrighted, or unclear-provenance material into the template unless they have the right to do so.

---

### Q25. What does the custom template output?

The custom template can output files such as:

* custom_chunks.csv
* custom_manifest.json
* custom_gate_checks.csv
* custom_audit_chain.jsonl
* custom_build_summary.json
* custom_benchmark_summary.json
* custom_benchmark_cases.csv

The goal is to make custom corpus testing reproducible and inspectable.

---

## G. Potential, scope, and limitations

### Q26. What is the potential of HSRAG?

HSRAG may be useful wherever retrieval needs stronger boundaries, source tracking, and auditability.

Potential areas include:

* legal and regulatory retrieval
* enterprise knowledge retrieval
* compliance workflows
* internal policy search
* AI memory systems
* technical documentation
* safety-critical procedures
* agent tool-use governance
* audit-friendly retrieval pipelines

The core idea is not merely to make the model smarter.

The goal is to make the model work inside a smaller, clearer, more auditable knowledge boundary.

---

### Q27. Can HSRAG reduce token or compute cost?

Potentially, yes.

HSRAG may reduce token usage by narrowing the retrieval space before sending evidence to a language model.

In the HSRAG LAW RQ5.5 benchmark, token and estimated cost reduction were significant under the benchmark setup.

However, this is benchmark-dependent.

More testing is needed across:

* larger corpora
* different domains
* different retrieval backends
* real production workloads
* mixed structured and unstructured data

HSRAG should be treated as a promising cost-reduction direction, not a universal cost guarantee.

---

### Q28. Is HSRAG relevant to AI auditability or AI governance?

Potentially, yes.

HSRAG emphasizes:

* bounded retrieval
* evidence traceability
* domain separation
* no-evidence decisions
* audit-chain outputs
* reproducible benchmark records

This does not automatically make a system legally compliant.

But it may be useful for teams building AI systems that need stronger auditability, traceability, and governance.

Actual compliance still requires legal review, security review, documentation, risk assessment, and domain-specific validation.

---

### Q29. Is HSRAG a white-box AI system?

Not exactly.

HSRAG does not make a language model fully white-box.

Instead, it makes the retrieval boundary, evidence path, routing decision, and gate decision more inspectable.

The language model may still be opaque.

But the retrieval-governance layer can be made more transparent and auditable.

---

### Q30. What kinds of knowledge are suitable for HSRAG?

HSRAG is most suitable for structured or semi-structured knowledge where source boundaries matter.

Examples:

* law and regulation
* enterprise policies
* compliance manuals
* technical standards
* API documentation
* safety procedures
* financial policies
* medical or clinical guidelines, with proper validation
* internal knowledge bases
* game world lore
* personal knowledge libraries

HSRAG is strongest when the domain has stable structure, source boundaries, and audit requirements.

---

### Q31. What kinds of knowledge are less suitable?

HSRAG may be less suitable when:

* the domain boundary is unclear
* source provenance is weak
* the task is open-ended creativity
* the user wants broad brainstorming
* there is no stable document structure
* evidence cannot be verified
* classification would be more expensive than retrieval

HSRAG is not a universal replacement for all forms of search or reasoning.

---

### Q32. What remains unproven?

Open questions include:

* whether HSRAG scales cleanly to much larger corpora
* how much token cost it saves across different domains
* how to automate high-quality CTHC classification
* how to integrate with production vector search systems
* how to handle noisy, incomplete, or conflicting sources
* how to generalize beyond legal-text benchmarks
* how to implement full HSRAG 6.3 × TACL runtime governance

These are research and engineering directions, not completed claims.

---

## H. Community and enterprise exploration directions

### Q33. What are the main research directions beyond HSRAG LAW?

HSRAG LAW is the first reproducible benchmark demo, but HSRAG is not limited to legal text.

Community and enterprise exploration directions include:

* edge-side hash pointers
* layered AI memory stores
* enterprise knowledge routing
* domain-specific CTHC schemas
* audit-friendly retrieval pipelines
* retrieval governance for agents
* source-linked knowledge libraries

The broader direction is hash-addressed knowledge infrastructure.

---

### Q34. What are edge-side hash pointers?

Edge-side hash pointers are lightweight references stored on the client or local device.

Instead of always sending or storing full raw context, the edge device may keep hash pointers or context pointers that refer to larger knowledge objects.

Potential benefits:

* lower edge memory pressure
* lower context transfer cost
* clearer local/cloud retrieval boundary
* more auditable context references
* support for personal AI memory
* support for enterprise internal knowledge systems

This is currently a research direction, not a complete privacy or security guarantee.

---

### Q35. Why might enterprises care about edge hash pointers?

Enterprises often cannot simply place all private context directly into a model prompt.

Edge hash pointers may help separate:

* local context references
* cloud retrieval
* access boundaries
* audit traces
* evidence selection

Potential enterprise value includes:

* less raw data in prompts
* more controlled retrieval paths
* clearer access boundaries
* better audit records
* lower unnecessary token usage

Actual deployment still requires access control, privacy design, security review, and infrastructure integration.

---

### Q36. Can HSRAG be used outside legal retrieval?

Potentially yes.

HSRAG can be explored anywhere knowledge needs structured retrieval and auditability.

Possible areas:

* enterprise search
* AI memory
* compliance systems
* policy retrieval
* engineering documentation
* customer support knowledge bases
* research archives
* agent workflow memory
* education and library-style knowledge systems

The most promising domains are those with stable documents, source boundaries, and clear retrieval rules.

---

## I. AI memory and three-store knowledge classification

### Q37. Why does HSRAG classify knowledge into FHS, EHS, and CHS?

Because not all memory has the same trust level, stability, or purpose.

A typical three-store model is:

* FHS: verified, stable, high-integrity knowledge
* EHS: temporary, pending, user-provided, or unverified knowledge
* CHS: challenge, synthetic, ambiguous, failure-case, or robustness-test material

The goal is to prevent verified facts, temporary inputs, and challenge cases from collapsing into one polluted memory pool.

---

### Q38. How does the three-store model relate to AI memory?

AI memory is not just about remembering more things.

It must answer questions such as:

* What type of memory is this?
* How trustworthy is it?
* Can it be used as evidence?
* Can it override older memory?
* Does it expire?
* Is it only a test case?
* Should it be retrieved for this user or task?

HSRAG treats memory as governed knowledge, not just accumulated context.

---

### Q39. Why not store all AI memory together?

A single undifferentiated memory pool can cause memory pollution.

Examples:

* a temporary user input may override verified knowledge
* a synthetic test case may be retrieved as fact
* a failure case may contaminate normal retrieval
* an unverified document may be treated as authoritative
* a challenge prompt may become part of regular memory

Memory classification makes retrieval safer, more auditable, and easier to correct.

---

### Q40. Can HSRAG support personal AI memory?

Potentially yes.

HSRAG may be useful for personal AI memory systems where different memory types need different trust levels, retention rules, and retrieval permissions.

Examples:

* personal facts
* preferences
* temporary tasks
* long-term projects
* corrected mistakes
* private notes
* reusable templates
* source-linked personal research

However, privacy, encryption, access control, and user-consent design are separate requirements.

---

### Q41. Can HSRAG support enterprise AI memory?

Potentially yes.

HSRAG may be useful for organizations that need source-linked, auditable, role-aware knowledge retrieval.

Possible enterprise memory domains:

* policy manuals
* compliance records
* internal SOPs
* customer support knowledge bases
* engineering docs
* legal references
* regulatory references
* incident postmortems
* institutional knowledge archives

Production use requires engineering hardening, permission systems, security review, and governance policy.

---

## J. Project boundary, forks, and commercialization

### Q42. Is this project production ready?

No.

The current repository is a research and benchmark demo.

It contains reproducible experiments and runnable examples, but it should not be treated as production-ready infrastructure.

---

### Q43. What is HSRAG 6.3 × TACL?

HSRAG 6.3 × TACL is a future integrated architecture target.

It combines typed hash-addressed retrieval with runtime control.

HSRAG focuses on where retrieval is allowed to go.

TACL focuses on whether execution should continue, stop, retry, degrade, or bail out.

The full HSRAG 6.3 × TACL stack is not fully implemented in the current repository.

---

### Q44. Can I fork this project?

Yes.

Forks are welcome.

Community members, researchers, companies, and independent developers may explore their own versions of HSRAG.

Forks should clearly document what they changed and should not misrepresent themselves as the original official project unless explicitly authorized.

---

### Q45. Can I commercialize a fork?

Commercial use is governed by the repository LICENSE.

The author does not oppose commercial exploration or independent implementations, as long as the applicable license is followed and no false affiliation is implied.

Unless there is a separate written agreement, commercial forks, services, products, integrations, or deployments are independent from the original author.

They should not imply:

* endorsement
* certification
* official collaboration
* commercial agency
* shared liability
* formal partnership
* official support

---

### Q46. What are the five core invariants?

The five core invariants are:

1. Bounded retrieval before reasoning.
2. Evidence must remain auditable.
3. Unsupported queries should not be silently answered.
4. Store roles must remain distinguishable.
5. Architecture claims must be honest.

These invariants describe the intended philosophy of HSRAG.

They are not a separate legal license.

---

### Q47. How should people contact or discuss the project?

The preferred communication language is Chinese.

English is the secondary communication language.

Either Chinese or English is acceptable.

The preferred discussion format is concise QA:

```
Q: Main question, issue, proposal, or request.
A: Short answer, context, evidence, or suggested next step.
```

This format helps reduce ambiguity and keeps technical discussion focused.

For private discussion, research collaboration, enterprise exploration, or consulting inquiries, see the project manifesto.

---

# HSRAG 常見問題

本 FAQ 說明 HSRAG 的基本概念、適用範圍、benchmark 意義、未來方向與專案邊界。

它面向開發者、研究者、企業與想快速理解本專案的社群成員。

---

## A. 基本定位

### Q1. HSRAG 是什麼？

HSRAG 是 Hash-Structured Retrieval-Augmented Generation 的縮寫。

它是一種把結構化知識定址放在語義檢索或生成之前的檢索架構。

傳統 RAG 通常先問：

```
哪一段文字在語義上最相似？
```

HSRAG 先問：

```
這個查詢被允許觸碰哪一個有邊界、可審計的知識地址？
```

目標是降低錯誤領域檢索、無支撐回答、不必要 token 使用，以及弱審計性。

---

### Q2. 這個想法從哪裡來？

一個重要靈感來自圖書館式檢索。

圖書館不會把所有書都視為一堆無差別文字。

它會使用分類系統、書架、目錄紀錄、索引與館藏位置，先縮小查找範圍，再閱讀內容。

HSRAG 把類似概念用到 AI 檢索：

* 分類知識
* 分配結構化地址
* 限制檢索邊界
* 保留證據路徑
* 審計決策過程

簡單說，HSRAG 是嘗試為 AI 知識檢索建立一層類圖書館索引的地址系統。

---

### Q3. HSRAG 要取代 RAG 嗎？

不是。

HSRAG 不打算取代所有 RAG 系統。

它更像是一種互補架構：

* HSRAG 提供類型化地址、有邊界檢索、證據守門與審計 trace。
* RAG / vector search 仍然可以在被縮小的搜尋範圍內使用。

簡短說法：

```
HSRAG 先定址。
RAG 在被限定的範圍內檢索。
```

---

### Q4. HSRAG 試圖解決什麼問題？

HSRAG 聚焦在以下 retrieval failure：

* 錯誤領域檢索
* 錯誤法域檢索
* unsupported query false allow
* ambiguous query false allow
* conflict-form query false allow
* 跨領域證據混用
* 過量 token 使用
* 審計軌跡薄弱

它不是解決所有 AI 問題。

它重點是讓檢索更有邊界、更可檢查、更重視 evidence。

---

## B. RAG、幻覺與互補性

### Q5. 為什麼當前 RAG 仍可能幻覺？

RAG 可以降低幻覺，但不會自動保證正確。

如果 retrieval 找到錯誤證據、混合不相容來源，或對 unsupported query 仍召回相似文字，generator 仍可能產生流暢但錯誤的回答。

很多時候，幻覺不只是模型問題。

它也是 retrieval boundary 問題。

---

### Q6. HSRAG 有什麼不同？

HSRAG 在 retrieval 前加入結構。

它不會一開始就搜尋整個 corpus，而是先嘗試把 query 解析成有邊界、類型化、可審計的 route。

簡化流程：

```
query
→ normalize
→ CTHC typed address
→ salted domain hash
→ bounded retrieval
→ evidence gate
→ audit chain
→ output
```

這能降低系統從錯誤 domain 取證的風險。

---

### Q7. HSRAG 能消除幻覺嗎？

不能。

HSRAG 不保證所有場景零幻覺。

它設計上是降低特定 retrieval-induced failure modes，尤其是：

* wrong-domain retrieval
* unsupported answer generation
* ambiguous query false allow
* incompatible corpora evidence mixing
* lack of auditability

語言模型仍可能犯錯。

HSRAG 的目標是讓 retrieval path 更受約束、更容易檢查。

---

### Q8. HSRAG 如何與 vector RAG 互補？

Vector retrieval 對語義相似度很有用。

HSRAG 不否定這點。

HSRAG 可以先縮小搜尋範圍，再允許 vector search 或 fuzzy retrieval 在 bounded subset 內執行。

實用混合模式是：

```
CTHC / hash route
→ domain-pruned subset
→ vector retrieval or reranking
→ evidence gate
→ answer
```

這保留語義搜尋，但降低不受控的全庫檢索。

---

## C. CTHC 與圖書館式分類尋址

### Q9. 什麼是 CTHC？

CTHC 是 Cross-Tag Hash Code。

它是一種結構化分類與定址層。

它可以為 knowledge chunks 分配可追蹤的 semantic address，而不是只把 chunk 當成純文字。

例如法律 chunk 可以有這樣的地址：

```
LEGAL.PUBLIC_LEGAL_TEXT.EU.EU_AI_ACT.GENERAL
```

或：

```
LEGAL.PUBLIC_LEGAL_TEXT.US.US_CDA230.GENERAL
```

---

### Q10. CTHC 跟杜威十進位分類法或圖書館索引有什麼相似？

杜威十進位分類法與圖書館目錄能幫使用者先縮小一本書的位置，再閱讀內容。

CTHC 對 AI retrieval 扮演類似角色。

它先問：

```
這個 query 屬於哪個知識區域？
```

再問：

```
哪段文字語義上最相似？
```

因此 CTHC 更像分類定址層，而不是純搜尋演算法。

---

### Q11. CTHC 只適合法律嗎？

不是。

HSRAG LAW 是第一個可重現 demo，但 CTHC 不限於法律文本。

潛在領域包括：

* 企業政策
* 合規手冊
* 醫療或臨床指南，需正確驗證
* 金融政策文件
* 技術標準
* API 文件
* 遊戲世界觀
* 安全流程
* 個人或企業 AI memory
* 內部知識庫

法律是一個很強的起點，因為法律檢索天然具有法域、來源、條文、權威性邊界。

---

### Q12. CTHC 是手動設計還是自動生成？

目前 demo 偏向簡化與 schema-driven。

未來版本可以探索：

* 人工定義企業 schema
* 半自動分類
* model-assisted tagging
* rule-based validation
* human review workflow

高品質全自動 CTHC classification 仍然是開放工程與研究問題。

---

## D. Hash、Salt 與 Audit

### Q13. 什麼是 salted domain hash？

Salted domain hash 是給 retrieval domain 的可重現 hash bucket。

它可能結合：

* salt
* domain
* source type
* jurisdiction
* corpus ID

目的在於建立穩定、可審計的 retrieval boundary。

除非系統明確允許其他路徑，query 應該只在匹配的 domain bucket 內檢索。

---

### Q14. 為什麼不用 metadata filters 就好？

Metadata filters 很有用。

HSRAG 不否定 metadata filtering。

Salted domain hash 的重點是讓 domain boundary 更明確、可重現、審計友好。

Metadata filter 可能是：

```
jurisdiction = EU
```

Salted domain hash 則把這個邊界變成 traceable retrieval address 的一部分。

目標不是取代所有 metadata。

目標是讓 retrieval boundary 不容易被默默模糊化。

---

### Q15. 什麼是 evidence gating？

Evidence gating 指的是系統在生成答案前，先檢查是否應該允許檢索與回答。

HSRAG 可能拒絕：

* unsupported queries
* ambiguous queries
* conflict-form queries
* unroutable queries
* domain mismatch cases

這讓系統可以在模型生成流暢但無支撐回答之前，先拒答或回傳 no-evidence。

---

### Q16. HSRAG 裡的 audit chain 是什麼？

Audit chain 指重要 retrieval 或 benchmark 決策會留下可重現 trace。

典型紀錄可能包括：

* query hash
* route decision
* selected evidence hash
* gate decision
* answer hash
* summary metrics
* decision trace

這有助於使用者檢查、重現與質疑結果。

---

### Q17. HSRAG 需要區塊鏈嗎？

不需要。

HSRAG 不需要區塊鏈。

Audit chain 可以只是本地 JSONL、CSV 或 structured logs。

未來如果需要公開時間戳或防篡改證明，可以考慮鏈上記錄，但目前設計不需要它。

---

## E. HSRAG LAW benchmark

### Q18. 什麼是 HSRAG LAW？

HSRAG LAW 是法律文本檢索 demo 與 benchmark。

它測試法律檢索是否能透過以下方式變得更有邊界、更可審計：

* CTHC typed legal routing
* salted domain hashes
* bounded retrieval
* evidence gating
* audit chains

它不是法律建議。

它是 retrieval architecture benchmark。

---

### Q19. RQ5.5 顯示了什麼？

RQ5.5 是目前 repository 中最強的 live benchmark。

目前 run 使用：

* 50,000 cases
* 110 rebuilt public legal-text chunks
* 5 corpora
* 5 salted domain hash buckets

HSRAG 結果顯示：

* target_correct: 1.0
* wrong_corpus_misrouting: 0.0
* wrong_jurisdiction_misrouting: 0.0
* unsupported_query_false_allow: 0.0
* ambiguous_query_false_allow: 0.0
* conflict_query_false_allow: 0.0
* audit_chain_complete: 1.0
* token / cost reduction: 在此 benchmark 設定下約 85.76%

這對目前 demo 來說是強 benchmark 結果。

但它不是宣稱 HSRAG 已在所有 domain 或 production workload 上被證明。

---

### Q20. RQ5.5 沒有證明什麼？

RQ5.5 沒有證明：

* HSRAG 已經 production-ready
* HSRAG 消除所有幻覺
* HSRAG 完整解決法律推理
* HSRAG 在所有 domain 都同樣有效
* HSRAG 自動擴展到所有 corpus size
* HSRAG 取代所有 vector retrieval system

它證明的是，在目前 benchmark setup 下，CTHC typed routing 加 salted domain hash retrieval 可以降低特定 retrieval 風險，並產生可重現 audit outputs。

---

### Q21. 為什麼 lexical baseline 有時更快？

Lexical baseline 可能更快，因為它做的是較簡單的 lookup，沒有相同程度的 routing、gating、audit constraints。

Raw speed 不是唯一指標。

HSRAG 優先考慮：

* bounded retrieval
* benchmark 條件下 zero false allow
* benchmark 條件下 zero wrong-domain routing
* auditability
* lower token cost

Global lexical baseline 可能在 raw p95 latency 上更快，但它也可能對 unsupported、ambiguous、conflict-form queries 照樣檢索。

---

### Q22. HSRAG LAW 是法律建議嗎？

不是。

HSRAG LAW 不是法律建議。

它不是生產級法律搜尋引擎。

它也不宣稱完整覆蓋官方法律資料。

它是 retrieval architecture benchmark demo。

---

## F. Custom corpus template

### Q23. 使用者可以測自己的法律文本嗎？

可以。

Repository 包含 custom corpus template，供使用者測試乾淨、合法可用的公開法律文本。

位置：

```
examples/hsrag_law/custom_template/
```

基本流程：

1. 把乾淨公開法律文本放入 input folder。
2. 編輯 manifest。
3. 建立 custom corpus。
4. 執行 custom benchmark。
5. 檢查 output files 與 audit traces。

目前優先支援 plaintext 或 markdown input。

PDF extraction、browser automation、official bulk ingestion 是未來 ingestion 方向。

---

### Q24. 使用者應該放什麼進 custom template？

使用者只應放入自己有權在本地處理的文本。

適合輸入：

* 乾淨公開法律文本
* 來源清楚的公開文件
* 合法可用的內部測試文本
* 手動整理過的 plaintext 或 markdown
* 有明確 source metadata 的文件

除非擁有權利，否則不應放入 private、confidential、copyrighted 或 unclear-provenance material。

---

### Q25. Custom template 會輸出什麼？

Custom template 可以輸出：

* custom_chunks.csv
* custom_manifest.json
* custom_gate_checks.csv
* custom_audit_chain.jsonl
* custom_build_summary.json
* custom_benchmark_summary.json
* custom_benchmark_cases.csv

目標是讓 custom corpus testing 可重現、可檢查。

---

## G. 潛力、範圍與限制

### Q26. HSRAG 的潛力是什麼？

HSRAG 可能適用於需要更強邊界、來源追蹤與審計性的檢索系統。

潛在領域包括：

* 法律與監管檢索
* 企業知識檢索
* 合規流程
* 內部政策搜尋
* AI memory systems
* 技術文件
* 安全關鍵流程
* agent tool-use governance
* audit-friendly retrieval pipelines

核心不是單純讓模型更聰明。

而是讓模型在更小、更清楚、更可審計的知識邊界內工作。

---

### Q27. HSRAG 可以降低 token 或算力成本嗎？

有可能。

HSRAG 可能透過在送入語言模型前縮小檢索範圍，降低 token 使用量。

在 HSRAG LAW RQ5.5 benchmark 中，在該 benchmark 設定下 token 與估算成本下降明顯。

但這取決於 benchmark 與使用場景。

仍需要更多測試，包括：

* 更大 corpus
* 不同 domain
* 不同 retrieval backend
* 真實 production workload
* 混合 structured / unstructured data

HSRAG 應被視為有潛力的 cost-reduction direction，而不是 universal cost guarantee。

---

### Q28. HSRAG 跟 AI 可審計性或 AI governance 有關嗎？

有潛力。

HSRAG 強調：

* bounded retrieval
* evidence traceability
* domain separation
* no-evidence decisions
* audit-chain outputs
* reproducible benchmark records

這不會自動讓系統 legal compliant。

但對於需要更強 auditability、traceability、governance 的 AI 系統，這種設計方向可能有用。

真正合規仍需要法律審查、安全審查、文件、風險評估與 domain-specific validation。

---

### Q29. HSRAG 是白箱 AI 系統嗎？

不完全是。

HSRAG 不會讓 language model 變成 fully white-box。

它讓 retrieval boundary、evidence path、routing decision、gate decision 更可檢查。

語言模型本身仍可能是 opaque。

但 retrieval-governance layer 可以更透明、更可審計。

---

### Q30. 哪些知識適合 HSRAG？

HSRAG 最適合具有穩定結構、來源邊界與審計需求的 structured 或 semi-structured knowledge。

例如：

* 法律與監管
* 企業政策
* 合規手冊
* 技術標準
* API 文件
* 安全流程
* 金融政策
* 醫療或臨床指南，需正確驗證
* 內部知識庫
* 遊戲世界觀
* 個人知識庫

HSRAG 在 domain 有穩定結構、source boundaries、audit requirements 時最強。

---

### Q31. 哪些知識不太適合 HSRAG？

HSRAG 可能不適合：

* domain boundary 不清楚
* source provenance 薄弱
* 任務是開放式創意
* 使用者想要廣泛 brainstorming
* 沒有穩定文件結構
* evidence 無法驗證
* classification 成本高於 retrieval 收益

HSRAG 不是所有 search 或 reasoning 的通用替代品。

---

### Q32. 目前還有哪些未證明問題？

開放問題包括：

* HSRAG 是否能乾淨擴展到更大 corpus
* 不同 domain 下能節省多少 token cost
* 如何自動化高品質 CTHC classification
* 如何整合 production vector search systems
* 如何處理 noisy、incomplete、conflicting sources
* 如何泛化到法律文本 benchmark 以外
* 如何實作完整 HSRAG 6.3 × TACL runtime governance

這些是研究與工程方向，不是已完成宣稱。

---

## H. 社群與企業探索方向

### Q33. HSRAG LAW 之外有哪些主要研究方向？

HSRAG LAW 是第一個可重現 benchmark demo，但 HSRAG 不限於法律文本。

社群與企業可以探索：

* edge-side hash pointers
* layered AI memory stores
* enterprise knowledge routing
* domain-specific CTHC schemas
* audit-friendly retrieval pipelines
* retrieval governance for agents
* source-linked knowledge libraries

更大的方向是 hash-addressed knowledge infrastructure。

---

### Q34. 什麼是端側 hash pointer？

端側 hash pointer 是儲存在 client 或 local device 的輕量引用。

不必總是傳輸或保存完整 raw context，端側可以保存指向較大 knowledge objects 的 hash pointers 或 context pointers。

潛在好處：

* 降低端側 memory pressure
* 降低 context transfer cost
* 更清楚的 local / cloud retrieval boundary
* 更可審計的 context reference
* 支援 personal AI memory
* 支援 enterprise internal knowledge systems

這目前是研究方向，不是完整 privacy 或 security guarantee。

---

### Q35. 為什麼企業可能關心端側 hash pointer？

企業通常不能把所有 private context 直接塞進 model prompt。

Edge hash pointer 可能幫助區分：

* local context references
* cloud retrieval
* access boundaries
* audit traces
* evidence selection

潛在企業價值包括：

* prompt 中放入更少 raw data
* 更受控的 retrieval path
* 更清楚的 access boundary
* 更好的 audit records
* 更低的不必要 token usage

實際部署仍需要 access control、privacy design、security review 與 infrastructure integration。

---

### Q36. HSRAG 可以用在法律以外嗎？

有潛力。

HSRAG 可以探索於任何需要 structured retrieval 與 auditability 的地方。

可能場景：

* enterprise search
* AI memory
* compliance systems
* policy retrieval
* engineering documentation
* customer support knowledge bases
* research archives
* agent workflow memory
* education and library-style knowledge systems

最有潛力的 domain 是有穩定文件、source boundaries、clear retrieval rules 的地方。

---

## I. AI memory 與三庫知識分類

### Q37. 為什麼 HSRAG 要把知識分成 FHS、EHS、CHS？

因為不是所有 memory 都有相同 trust level、stability 或 purpose。

典型三庫模型是：

* FHS: verified, stable, high-integrity knowledge
* EHS: temporary, pending, user-provided, or unverified knowledge
* CHS: challenge, synthetic, ambiguous, failure-case, or robustness-test material

目標是防止 verified facts、temporary inputs、challenge cases 全部坍縮成一個被污染的 memory pool。

---

### Q38. 三庫模型跟 AI memory 有什麼關係？

AI memory 不只是記住更多東西。

它必須回答：

* 這是什麼類型的 memory？
* 它可信嗎？
* 可以作為 evidence 嗎？
* 能覆蓋舊記憶嗎？
* 它會失效嗎？
* 它只是測試案例嗎？
* 這個 user 或 task 可以檢索它嗎？

HSRAG 把 memory 視為需要治理的知識，而不是單純累積的 context。

---

### Q39. 為什麼不把所有 AI memory 存在一起？

單一無差別 memory pool 可能造成 memory pollution。

例子：

* temporary user input 覆蓋 verified knowledge
* synthetic test case 被當成 fact retrieved
* failure case 污染 normal retrieval
* unverified document 被當作 authoritative
* challenge prompt 變成 regular memory

Memory classification 讓 retrieval 更安全、更可審計、更容易修正。

---

### Q40. HSRAG 可以支援個人 AI memory 嗎？

有潛力。

HSRAG 可能適合 personal AI memory systems，因為不同 memory type 需要不同 trust level、retention rule、retrieval permission。

例子：

* personal facts
* preferences
* temporary tasks
* long-term projects
* corrected mistakes
* private notes
* reusable templates
* source-linked personal research

但 privacy、encryption、access control、user-consent design 是另外的必要要求。

---

### Q41. HSRAG 可以支援企業 AI memory 嗎？

有潛力。

HSRAG 可能適合需要 source-linked、auditable、role-aware knowledge retrieval 的組織。

可能企業 memory domain：

* policy manuals
* compliance records
* internal SOPs
* customer support knowledge bases
* engineering docs
* legal references
* regulatory references
* incident postmortems
* institutional knowledge archives

Production use 需要 engineering hardening、permission systems、security review、governance policy。

---

## J. 專案邊界、Fork 與商業化

### Q42. 這個專案 production ready 嗎？

不是。

目前 repository 是 research and benchmark demo。

它包含可重現實驗與可跑 examples，但不應被視為 production-ready infrastructure。

---

### Q43. 什麼是 HSRAG 6.3 × TACL？

HSRAG 6.3 × TACL 是 future integrated architecture target。

它把 typed hash-addressed retrieval 與 runtime control 結合。

HSRAG 關注 retrieval 被允許去哪裡。

TACL 關注 execution 是否應該 continue、stop、retry、degrade 或 bail out。

完整 HSRAG 6.3 × TACL stack 尚未在目前 repository 中完整實作。

---

### Q44. 我可以 fork 這個專案嗎？

可以。

歡迎 fork。

社群成員、研究者、企業、獨立開發者都可以探索自己的 HSRAG 版本。

Fork 應清楚記錄改了什麼，也不應在未經授權下誤稱自己是 original official project。

---

### Q45. 我可以商業化 fork 嗎？

商業使用由 repository LICENSE 決定。

作者不反對商業探索或獨立實作，只要遵守適用 license，且不暗示虛假關聯。

除非另有書面協議，任何 commercial fork、service、product、integration 或 deployment 都與原作者獨立。

不得暗示：

* endorsement
* certification
* official collaboration
* commercial agency
* shared liability
* formal partnership
* official support

---

### Q46. 五條核心不變量是什麼？

五條核心不變量是：

1. Bounded retrieval before reasoning.
2. Evidence must remain auditable.
3. Unsupported queries should not be silently answered.
4. Store roles must remain distinguishable.
5. Architecture claims must be honest.

這些不變量描述 HSRAG 的設計哲學。

它們不是額外法律 license。

---

### Q47. 應該如何聯絡或討論專案？

最佳溝通語言是中文。

英文是次要溝通語言。

中文或英文皆可。

建議討論格式是精簡 QA：

```
Q: 主要問題、需求、提案或疑問。
A: 簡短回答、背景、證據或建議下一步。
```

這種格式可以降低歧義，讓技術討論更聚焦。

私人討論、研究合作、企業探索或顧問諮詢，請參考 project manifesto。

