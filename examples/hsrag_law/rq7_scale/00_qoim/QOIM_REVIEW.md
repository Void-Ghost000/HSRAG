# RQ7 QOIM Review

Intent:
Compare mainstream global search, CTHC-pruned search, and unique address lookup under corpus scale growth.

Scope:
LAW corpus scale benchmark.
Initial scale tiers: 1k, 5k, 10k, 50k chunks.

Forbidden Zones:
- Do not claim HSRAG replaces all RAG systems.
- Do not use unique address lookup for open-ended queries.
- Do not lower gates to make results look better.

Invariants:
- source_hash must be deterministic.
- cthc_address must be deterministic.
- result contract must be stable.
- audit hash fields must be complete.
- route determinism must be measured.

Risk Class:
Medium.

Delivery Level:
Level 1 — QSVCS Designed.
