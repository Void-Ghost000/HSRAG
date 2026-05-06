# HSRAG Project Manifesto

This document explains the positioning, boundaries, maintenance expectations, communication preference, fork policy, commercialization stance, and core invariants of the HSRAG project.

HSRAG is an independent research direction, not a commercial product promise.

It is a personal, AI-assisted research project exploring:

- hash-structured retrieval
- bounded evidence routing
- CTHC typed addressing
- salted domain-hash retrieval
- evidence gating
- audit-chain traceability
- future AI memory / retrieval governance

The current repository contains reproducible demos and benchmark artifacts, especially through HSRAG LAW.

However, this project does not promise that every proposed architecture, module, roadmap item, or future design will be fully implemented by the original author.

Some parts are implemented.

Some parts are experimental.

Some parts are architectural direction.

Some parts are long-term research targets.

---

## 1. Project positioning

HSRAG is currently a research / benchmark project.

It is intended to explore whether AI retrieval systems can become more:

- bounded
- auditable
- domain-aware
- token-efficient
- resistant to unsupported evidence mixing
- less prone to wrong-domain retrieval

The current core result is the reproducible HSRAG LAW benchmark demo.

This project is not:

- a finished product
- a legal advice engine
- a production-ready enterprise system
- a universal RAG replacement
- a zero-hallucination guarantee system
- a commercial service that the original author promises to maintain

---

## 2. Personal research disclaimer

This project is maintained as an independent personal research effort.

The original author is an AI-assisted amateur developer, not a professional software engineering team.

Many parts of the project began as architectural ideas and were then implemented with the help of AI tools.

Because of this, the repository may contain:

- bugs
- rough code
- incomplete modules
- naming inconsistencies
- experimental scripts
- documentation gaps
- engineering choices that can be improved

Issues, forks, corrections, criticism, refactoring, and independent re-implementations are welcome.

The project should be evaluated as an open research prototype, not as production-ready infrastructure.

---

## 3. No implementation promise

HSRAG contains:

- current runnable code
- reproducible benchmarks
- experimental prototypes
- future architecture documents
- conceptual research directions

A roadmap item does not mean guaranteed delivery.

An architecture diagram does not mean full implementation.

A benchmark demo does not mean production readiness.

A research direction does not mean commercial support.

The project may evolve based on:

- author availability
- research progress
- benchmark results
- implementation feasibility
- community forks
- contributor interest
- independent implementation

The author may prioritize research clarity and benchmark evidence over full production engineering.

---

## 4. Update cadence

This project is maintained on a best-effort basis.

The expected update rhythm is approximately:

    once every 2 weeks to 1 month

When time and research progress allow, updates may happen faster, sometimes within a week.

However, this is not a guaranteed release schedule.

The original author does not promise:

- continuous maintenance
- fixed release cadence
- fixed bug-fix timeline
- fixed roadmap delivery
- long-term commercial support

---

## 5. Communication language and format

The preferred communication language is Chinese.

English is the secondary communication language.

You may contact the author in either Chinese or English.

To reduce misunderstanding and keep discussion efficient, the preferred communication style is concise QA format.

Recommended format:

    Q: What is the main question, issue, proposal, or request?
    A: Short answer, context, evidence, or suggested next step.

The author may also respond in QA format to keep both sides aligned, focused, and professionally precise.

This communication style is especially preferred for:

- technical discussion
- research collaboration
- enterprise exploration
- grant discussion
- benchmark review
- issue clarification
- fork coordination
- consulting inquiry

The goal is not excessive formality.

The goal is to make the main topic clear, reduce ambiguity, and avoid long unfocused discussion.

---

## 6. Contact and private discussion

For private discussion, research collaboration, enterprise exploration, or consulting inquiries, the author may be contacted by email:

    hamitozzz79@gmail.com

Email contact is intended for initial discussion only.

It does not imply:

- guaranteed response
- guaranteed support
- guaranteed maintenance
- commercial service availability
- formal partnership
- legal, financial, or professional advice
- responsibility for third-party use or deployment outcomes

Any formal collaboration, consulting, enterprise support, commercial licensing, or joint development requires separate written agreement.

---

## 7. Fork policy

Forks are welcome.

Different communities, research groups, companies, or independent developers may explore their own versions of HSRAG.

Forks may modify:

- CTHC schemas
- store schemas
- guard thresholds
- retrieval backends
- audit formats
- benchmark scopes
- implementation language
- runtime integration patterns
- UI / API / service layers

However, forks should not misrepresent themselves as the original official project unless explicitly authorized.

Forks are encouraged to clearly document:

- what was changed
- what was preserved
- which parts remain experimental
- whether the HSRAG core invariants are preserved
- whether there is any formal relationship with the original author

---

## 8. Commercialization and independent implementations

Subject to the repository LICENSE, the author does not oppose commercial exploration, commercial forks, services, products, integrations, or independent implementations of HSRAG.

Legal permission for commercial use is governed by the repository LICENSE.

The five core invariants in this manifesto describe the intended design philosophy of HSRAG.

They are not a separate legal license.

Unless there is a separate written agreement, any commercial fork, service, product, integration, or deployment is independent from the original author.

It should not imply:

- endorsement
- certification
- official collaboration
- commercial agency
- shared liability
- formal partnership
- official support

In short:

    Forking is welcome.
    Independent implementation is welcome.
    Commercialization is not opposed.
    Misrepresentation is not acceptable.

---

## 9. Five core invariants

The following five invariants define the core spirit of HSRAG.

They are not meant to block experimentation, but if a fork removes these principles, it should clearly state that it has changed the core philosophy of HSRAG.

---

### Invariant 1 — Bounded retrieval before reasoning

HSRAG should attempt to bound the retrieval space before semantic reasoning or generation.

The system should ask:

    Which knowledge address is this query allowed to touch?

before asking:

    Which text is semantically similar?

This is the core separation between addressing and reasoning.

---

### Invariant 2 — Evidence must remain auditable

Retrieval and generation should leave inspectable, reproducible traces.

At minimum, important benchmark or runtime decisions should preserve:

- query identity
- selected evidence
- decision reason
- relevant hashes
- summary output
- audit chain or reproducible trace

Auditability should not be treated as optional decoration.

It is part of the architecture.

---

### Invariant 3 — Unsupported queries should not be silently answered

If a query cannot be grounded in matched evidence, the system should reject, warn, or return a no-evidence result.

It should not generate unsupported answers merely because the language model can produce a fluent response.

In high-risk domains, refusal is a valid system output.

---

### Invariant 4 — Store roles must remain distinguishable

HSRAG should distinguish between different kinds of knowledge or memory.

A typical three-store model is:

- FHS: verified / factual / high-integrity store
- EHS: temporary / pending / unverified store
- CHS: challenge / synthetic / failure-case store

FHS, EHS, and CHS should not be silently collapsed into one undifferentiated memory pool.

Especially in legal or regulatory retrieval, verified evidence should not be overridden by temporary or challenge material.

---

### Invariant 5 — Architecture claims must be honest

The project should clearly distinguish between:

- implemented code
- reproducible benchmarks
- experimental prototypes
- future architecture
- conceptual research direction

This distinction is necessary for trust.

HSRAG should not present future architecture as already completed implementation.

---

## 10. What HSRAG invites

HSRAG invites:

- independent verification
- benchmark reproduction
- forks
- criticism
- simplified implementations
- alternative retrieval backends
- better engineering
- better documentation
- domain-specific adaptations
- community-led implementations

The strongest version of HSRAG may come from many forks, not from one person maintaining everything alone.

That is expected, not a failure.

---

## 11. Practical expectation

If this project becomes useful to others, the preferred path is not centralized pressure on the original author.

The preferred path is:

- fork it
- test it
- simplify it
- improve it
- document changes
- preserve auditability
- publish results

HSRAG is best understood as a seed architecture.

It is allowed to grow through independent branches.

---

## 12. One-line manifesto

HSRAG is an AI-assisted, independent research project exploring bounded, auditable, hash-addressed retrieval; it welcomes forks, criticism, reproduction, and improvements, while making no promise that every roadmap item or future architecture component will be implemented by the original author.

---

# HSRAG 專案宣言

本文件說明 HSRAG 專案的定位、邊界、維護方式、溝通偏好、Fork 態度、商業化態度，以及核心不變量。

HSRAG 是一個個人研究方向，不是商業產品承諾。

它是一個由個人提出、並透過 AI 輔助逐步實作的研究型開源專案，主要探索：

- hash-structured retrieval
- bounded evidence routing
- CTHC typed addressing
- salted domain-hash retrieval
- evidence gating
- audit-chain traceability
- future AI memory / retrieval governance

目前 repository 包含可重現的 demo 與 benchmark，尤其是 HSRAG LAW。

但本專案不承諾所有架構、模組、roadmap 項目、未來設計都會由原作者完整實作。

有些部分已經實作。

有些部分是實驗。

有些部分是架構方向。

有些部分是長期研究目標。

---

## 1. 專案定位

HSRAG 目前是研究 / benchmark 專案。

它的目標是探索 AI 檢索系統是否能變得更：

- 有邊界
- 可審計
- 具備領域感知
- 節省 token
- 抵抗 unsupported evidence mixing
- 降低錯誤領域檢索風險

目前的核心成果是可重現的 HSRAG LAW benchmark demo。

本專案不是：

- 完整產品
- 法律建議引擎
- 生產級企業系統
- 通用 RAG 替代品
- 零幻覺保證系統
- 原作者承諾長期維護的商業服務

---

## 2. 個人研究聲明

本專案由個人維護。

原作者是一名 AI 輔助型業餘開發者，不是專業軟體工程團隊。

許多內容先來自架構構想，然後透過 AI 工具輔助實作。

因此，本 repo 可能存在：

- bug
- rough code
- incomplete modules
- naming inconsistencies
- experimental scripts
- documentation gaps
- engineering choices that can be improved

歡迎 issue、fork、修正、批評、重構與獨立實作。

本專案應該被視為開放研究原型，而不是 production-ready infrastructure。

---

## 3. 不承諾完整實作

HSRAG 同時包含：

- current runnable code
- reproducible benchmarks
- experimental prototypes
- future architecture documents
- conceptual research directions

Roadmap 不代表保證交付。

Architecture diagram 不代表已完整實作。

Benchmark demo 不代表 production readiness。

Research direction 不代表 commercial support。

專案演進會取決於：

- 原作者時間
- 研究進度
- benchmark 結果
- 實作可行性
- 社群 fork
- contributor interest
- independent implementation

原作者可能優先追求研究清晰度與 benchmark evidence，而不是完整 production engineering。

---

## 4. 更新頻率

本專案採 best-effort 維護。

預期更新節奏大約是：

    2 週到 1 個月一次

如果研究進度或時間允許，更新可能更快，例如一週內更新。

但這不是固定 release schedule。

原作者不承諾：

- 持續維護
- 固定版本發布
- 固定 bug 修復時間
- 固定 roadmap 交付時間
- 長期 commercial support

---

## 5. 溝通語言與格式

本專案的最佳溝通語言是中文。

英文是次要溝通語言。

你可以選擇使用中文或英文聯絡。

為了降低誤解並提高溝通效率，建議使用濃縮、精簡、切入主要問題的 QA 形式。

建議格式：

    Q: 主要問題、需求、提案或疑問是什麼？
    A: 簡短回答、背景、證據或建議下一步。

原作者也可能使用 QA 形式回覆，以確保雙方溝通無誤、聚焦且專業。

這種溝通方式尤其適合：

- 技術討論
- 研究合作
- 企業探索
- Grant 討論
- Benchmark review
- Issue clarification
- Fork coordination
- Consulting inquiry

這不是為了過度形式化。

目標是讓主題清楚、降低歧義、避免過長且失焦的討論。

---

## 6. 聯絡與私人討論

私人討論、研究合作、企業探索、顧問諮詢，可以透過 email 做初步來往：

    hamitozzz79@gmail.com

Email 聯絡只代表可以進行初步討論。

它不代表：

- 保證回覆
- 保證支援
- 保證維護
- 保證商業服務
- 正式合作關係
- 法律、財務或專業建議
- 原作者對任何第三方使用結果承擔責任

任何正式合作、顧問、企業支援、商業授權或共同開發，都需要另外書面協議。

---

## 7. Fork policy

歡迎 fork。

不同社群、研究機構、企業、獨立開發者，都可以探索自己的 HSRAG 分支。

Fork 可以修改：

- CTHC schema
- Store schema
- Guard threshold
- Retrieval backend
- Audit format
- Benchmark scope
- Implementation language
- Runtime integration pattern
- UI / API / service layer

但 fork 不應該誤稱自己是原始官方專案，除非獲得明確授權。

Fork 應該清楚說明：

- 改了什麼
- 保留了什麼
- 哪些部分仍是實驗
- 是否保持 HSRAG core invariants
- 是否與原作者有正式關係

---

## 8. 商業化與獨立實作

在遵守 repository LICENSE 的前提下，原作者不反對各方探索 HSRAG 的商業化、fork、服務化、產品化或獨立實作。

但商業使用的法律權利由 LICENSE 決定。

本文件中的五條不變量是設計哲學，不是額外法律授權條款。

除非有另外書面協議，任何商業 fork、服務、產品、整合或部署，都與原作者無從屬關係。

不得暗示：

- 原作者背書
- 原作者認證
- 官方合作
- 商業代理
- 共同責任
- shared liability
- formal partnership
- official support

簡單說：

    Fork is welcome.
    Independent implementation is welcome.
    Commercialization is not opposed.
    Misrepresentation is not acceptable.

---

## 9. Five core invariants

以下五條不變量代表 HSRAG 的核心精神。

它們不阻止實驗，但如果 fork 移除了這些原則，應清楚聲明該 fork 已經改變了 HSRAG 的核心哲學。

---

### Invariant 1 — Bounded retrieval before reasoning

HSRAG 應該在語義推理或生成之前，先嘗試縮小檢索範圍。

系統應該先問：

    Which knowledge address is this query allowed to touch?

再問：

    Which text is semantically similar?

這是 addressing 與 reasoning 的核心分離。

---

### Invariant 2 — Evidence must remain auditable

檢索與生成應該留下可檢查、可重現的 trace。

重要 benchmark 或 runtime 決策至少應保留：

- query identity
- selected evidence
- decision reason
- relevant hashes
- summary output
- audit chain or reproducible trace

可審計性不是裝飾。

它是 HSRAG 的核心架構特徵。

---

### Invariant 3 — Unsupported queries should not be silently answered

如果 query 無法被匹配 evidence 支撐，系統應該 reject、warn 或 return no-evidence result。

不應該因為 language model 能產生流暢文字，就生成 unsupported answer。

在高風險領域中，拒答是一種有效輸出。

---

### Invariant 4 — Store roles must remain distinguishable

HSRAG 應該區分不同種類的知識與記憶。

典型三庫模型是：

- FHS: verified / factual / high-integrity store
- EHS: temporary / pending / unverified store
- CHS: challenge / synthetic / failure-case store

FHS、EHS、CHS 不應被默默合併成一個無差別 memory pool。

尤其在法律或監管檢索中，verified evidence 不應被 temporary 或 challenge material 覆蓋。

---

### Invariant 5 — Architecture claims must be honest

本專案應清楚區分：

- implemented code
- reproducible benchmarks
- experimental prototypes
- future architecture
- conceptual research direction

這種區分是信任的基礎。

HSRAG 不應把 future architecture 包裝成已完成 implementation。

---

## 10. What HSRAG invites

HSRAG 歡迎：

- independent verification
- benchmark reproduction
- forks
- criticism
- simplified implementation
- alternative retrieval backend
- better engineering
- better documentation
- domain-specific adaptation
- community-led implementation

HSRAG 最強版本可能來自許多 fork，而不是原作者一個人維護所有東西。

這是預期結果，不是失敗。

---

## 11. Practical expectation

如果本專案對其他人有用，理想路徑不是把壓力集中在原作者身上。

理想路徑是：

- fork it
- test it
- simplify it
- improve it
- document changes
- preserve auditability
- publish results

HSRAG 最適合被理解為 seed architecture。

它可以透過不同社群、研究者與工程團隊長出不同分支。

---

## 12. One-line manifesto

HSRAG 是一個 AI 輔助的個人研究專案，探索 bounded、auditable、hash-addressed retrieval；它歡迎 fork、批評、重現與改進，但不承諾所有 roadmap 或 future architecture 都會由原作者完整實作。