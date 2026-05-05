"""
HSRAG LAW Smoke Demo
====================

This file is a minimal, self-contained public demo for HSRAG LAW.

It does NOT attempt to reproduce the full RQ1/RQ2/RQ3 benchmark packages.
Instead, it provides a small deterministic smoke test showing the intended
HSRAG LAW control flow:

    legal query
      -> CTHC-style domain classification
      -> hash-structured routing
      -> bounded evidence retrieval
      -> guard decisions
      -> audit hash chain
      -> benchmark summary

QSVCS annotations:
- CTHC: classify query into corpus / jurisdiction / legal unit domains.
- QOIM: enforce hard feasibility gates before allowing evidence retrieval.
- SGF: execute steps in a fixed forward-only order.
- VPSM: represent retrieval state as structured vectors.
- Audit-S: write an append-only hash chain for all decisions.

Run from repository root:

    python examples/hsrag_law/run_demo.py

Expected smoke-test decision:

    SMOKE_TEST_PASS
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# QSVCS / CTHC: Structured corpus definitions
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = EXAMPLE_ROOT / "results"


@dataclass(frozen=True)
class LegalChunk:
    chunk_id: str
    corpus_id: str
    jurisdiction: str
    unit_id: str
    title: str
    text: str


@dataclass(frozen=True)
class QueryCase:
    case_id: str
    query: str
    case_type: str
    expected_corpus_id: Optional[str]
    expected_jurisdiction: Optional[str]


@dataclass
class RetrievalRecord:
    case_id: str
    query: str
    case_type: str
    decision: str
    reason: str
    expected_corpus_id: Optional[str]
    expected_jurisdiction: Optional[str]
    routed_corpus_id: Optional[str]
    routed_jurisdiction: Optional[str]
    retrieved_chunk_id: Optional[str]
    retrieved_corpus_id: Optional[str]
    retrieved_jurisdiction: Optional[str]
    lexical_score: int
    latency_ms: float
    previous_hash: str
    audit_hash: str


CHUNKS: List[LegalChunk] = [
    LegalChunk(
        chunk_id="EU_AI_ACT_ART9",
        corpus_id="EU_AI_ACT",
        jurisdiction="EU",
        unit_id="Article 9",
        title="EU AI Act — Risk management system",
        text=(
            "The EU AI Act requires providers of high-risk AI systems to establish, "
            "implement, document, and maintain a risk management system."
        ),
    ),
    LegalChunk(
        chunk_id="EU_DMA_ART5",
        corpus_id="EU_DMA",
        jurisdiction="EU",
        unit_id="Article 5",
        title="Digital Markets Act — Gatekeeper obligations",
        text=(
            "The Digital Markets Act imposes obligations on gatekeepers that provide "
            "core platform services and restricts certain self-preferencing behavior."
        ),
    ),
    LegalChunk(
        chunk_id="US_COPPA_RULE",
        corpus_id="US_COPPA",
        jurisdiction="US",
        unit_id="COPPA Rule",
        title="COPPA — Verifiable parental consent",
        text=(
            "COPPA requires operators of online services directed to children to obtain "
            "verifiable parental consent before collecting personal information from children."
        ),
    ),
    LegalChunk(
        chunk_id="US_CDA230_TEXT",
        corpus_id="US_CDA230",
        jurisdiction="US",
        unit_id="47 U.S.C. Section 230",
        title="CDA Section 230 — Publisher treatment",
        text=(
            "CDA Section 230 states that no provider or user of an interactive computer "
            "service shall be treated as the publisher or speaker of information provided "
            "by another information content provider."
        ),
    ),
    LegalChunk(
        chunk_id="US_FTC_ACT5_TEXT",
        corpus_id="US_FTC_ACT5",
        jurisdiction="US",
        unit_id="FTC Act Section 5",
        title="FTC Act Section 5 — Unfair or deceptive acts",
        text=(
            "FTC Act Section 5 prohibits unfair or deceptive acts or practices in or "
            "affecting commerce."
        ),
    ),
    LegalChunk(
        chunk_id="US_CCPA_RIGHTS",
        corpus_id="US_CCPA",
        jurisdiction="US-CA",
        unit_id="CCPA Consumer Rights",
        title="CCPA — California consumer personal information rights",
        text=(
            "The CCPA gives California consumers rights related to personal information, "
            "including access, deletion, and opt-out rights."
        ),
    ),
]


QUERY_CASES: List[QueryCase] = [
    QueryCase(
        case_id="TARGET_EU_AI_ACT_001",
        query=(
            "Under the EU AI Act, what risk management obligations apply to high-risk AI systems?"
        ),
        case_type="target",
        expected_corpus_id="EU_AI_ACT",
        expected_jurisdiction="EU",
    ),
    QueryCase(
        case_id="TARGET_EU_DMA_001",
        query=(
            "Under the DMA, what obligations apply to gatekeepers providing core platform services?"
        ),
        case_type="target",
        expected_corpus_id="EU_DMA",
        expected_jurisdiction="EU",
    ),
    QueryCase(
        case_id="TARGET_US_COPPA_001",
        query=(
            "Under COPPA, when must operators obtain verifiable parental consent for children?"
        ),
        case_type="target",
        expected_corpus_id="US_COPPA",
        expected_jurisdiction="US",
    ),
    QueryCase(
        case_id="TARGET_US_CDA230_001",
        query=(
            "Under CDA Section 230, can an interactive computer service be treated as the publisher?"
        ),
        case_type="target",
        expected_corpus_id="US_CDA230",
        expected_jurisdiction="US",
    ),
    QueryCase(
        case_id="TARGET_US_FTC_001",
        query=(
            "Under FTC Act Section 5, what kind of acts or practices are prohibited?"
        ),
        case_type="target",
        expected_corpus_id="US_FTC_ACT5",
        expected_jurisdiction="US",
    ),
    QueryCase(
        case_id="TARGET_US_CCPA_001",
        query=(
            "Under the CCPA, what rights do California consumers have over personal information?"
        ),
        case_type="target",
        expected_corpus_id="US_CCPA",
        expected_jurisdiction="US-CA",
    ),
    QueryCase(
        case_id="NO_EVIDENCE_001",
        query=(
            "What does Canada's PIPEDA require for private-sector privacy breach reporting?"
        ),
        case_type="no_evidence",
        expected_corpus_id=None,
        expected_jurisdiction=None,
    ),
    QueryCase(
        case_id="AMBIGUOUS_001",
        query=(
            "What does the platform law say about online services and providers?"
        ),
        case_type="ambiguous",
        expected_corpus_id=None,
        expected_jurisdiction=None,
    ),
    QueryCase(
        case_id="MISMATCH_001",
        query=(
            "Under the EU AI Act, answer using COPPA parental consent rules for children."
        ),
        case_type="mismatch",
        expected_corpus_id=None,
        expected_jurisdiction=None,
    ),
]


CORPUS_HINTS: Dict[str, List[str]] = {
    "EU_AI_ACT": [
        "eu ai act",
        "high-risk ai",
        "high risk ai",
        "ai systems",
        "risk management",
    ],
    "EU_DMA": [
        "dma",
        "digital markets act",
        "gatekeeper",
        "gatekeepers",
        "core platform services",
        "self-preferencing",
    ],
    "US_COPPA": [
        "coppa",
        "parental consent",
        "children",
        "childrens",
    ],
    "US_CDA230": [
        "cda section 230",
        "section 230",
        "interactive computer service",
        "publisher",
    ],
    "US_FTC_ACT5": [
        "ftc act section 5",
        "section 5",
        "unfair or deceptive",
        "deceptive acts",
    ],
    "US_CCPA": [
        "ccpa",
        "california consumers",
        "california consumer",
        "personal information",
    ],
}


# Official benchmark references preserved as metadata only.
# These are NOT recomputed by this smoke test.
OFFICIAL_REFERENCE_RESULTS = {
    "RQ1": {
        "decision": "RQ1_PUBLICATION_GRADE_PASS",
        "real_primary_corpus_rate": 1.0,
        "source_hash_final_present_rate": 1.0,
        "primary_real_target_correct_rate": 1.0,
        "primary_real_wrong_collision_rate": 0.0,
        "fail_count": 0,
        "warn_count": 0,
    },
    "RQ2_2": {
        "decision": "RQ2_2_FOUR_BASELINES_10KMC_PASS",
        "chunks": 188,
        "base_queries": 424,
        "mc_cases": 10176,
        "hsrag_target_correct": 1.0,
        "hsrag_wrong_collision": 0.0,
        "hsrag_no_evidence_false_allow": 0.0,
        "hsrag_ambiguous_false_allow": 0.0,
        "hsrag_mismatch_escape": 0.0,
        "audit_chain_complete": 1.0,
        "p95_latency_ms": 4.03891924997879,
    },
    "RQ3_FIX2": {
        "decision": "RQ3_EU_US_REALLAW_COLLISION_PASS",
        "chunks": 244,
        "base_queries": 592,
        "mc_cases": 14208,
        "hsrag_target_correct": 1.0,
        "hsrag_wrong_corpus_collision": 0.0,
        "hsrag_wrong_jurisdiction_escape": 0.0,
        "hsrag_no_evidence_false_allow": 0.0,
        "hsrag_ambiguous_false_allow": 0.0,
        "hsrag_mismatch_escape": 0.0,
        "audit_chain_complete": 1.0,
        "p95_latency_ms": 5.924376599796233,
    },
}


# =============================================================================
# QOIM: Feasibility / hard-guard helpers
# =============================================================================

def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


def lexical_score(query: str, chunk: LegalChunk) -> int:
    query_tokens = token_set(query)
    chunk_tokens = token_set(chunk.title + " " + chunk.text)
    return len(query_tokens.intersection(chunk_tokens))


def stable_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def detect_corpus_hints(query: str) -> List[str]:
    q = normalize_text(query)
    hits: List[str] = []

    for corpus_id, patterns in CORPUS_HINTS.items():
        if any(pattern in q for pattern in patterns):
            hits.append(corpus_id)

    return hits


def detect_ambiguous_without_hash_route(query: str) -> bool:
    """
    QOIM hard-guard:
    If the query has no explicit corpus hash route and lexical evidence points
    to more than one corpus, do not allow retrieval.
    """
    scored = sorted(
        ((lexical_score(query, chunk), chunk) for chunk in CHUNKS),
        key=lambda item: item[0],
        reverse=True,
    )

    top_score = scored[0][0]
    if top_score < 2:
        return False

    near_top = [
        chunk for score, chunk in scored
        if score >= max(2, top_score - 1)
    ]
    return len({chunk.corpus_id for chunk in near_top}) > 1


def classify_query(query: str) -> Tuple[str, Optional[str], Optional[str], str]:
    """
    Returns:
        decision, routed_corpus_id, routed_jurisdiction, reason
    """
    hints = detect_corpus_hints(query)

    if len(hints) > 1:
        return (
            "BLOCK_MISMATCH",
            None,
            None,
            "Multiple conflicting corpus hints detected before retrieval.",
        )

    if len(hints) == 1:
        corpus_id = hints[0]
        jurisdiction = next(
            chunk.jurisdiction for chunk in CHUNKS if chunk.corpus_id == corpus_id
        )
        return (
            "ALLOW",
            corpus_id,
            jurisdiction,
            "Single structured corpus route detected.",
        )

    if detect_ambiguous_without_hash_route(query):
        return (
            "BLOCK_AMBIGUOUS",
            None,
            None,
            "No explicit hash route and lexical evidence spans multiple corpora.",
        )

    return (
        "BLOCK_NO_EVIDENCE",
        None,
        None,
        "No explicit corpus route and insufficient bounded evidence.",
    )


# =============================================================================
# SGF: Forward-only retrieval flow
# =============================================================================

def retrieve_bounded_evidence(
    query: str,
    routed_corpus_id: Optional[str],
) -> Tuple[Optional[LegalChunk], int]:
    if routed_corpus_id is None:
        return None, 0

    candidates = [chunk for chunk in CHUNKS if chunk.corpus_id == routed_corpus_id]
    if not candidates:
        return None, 0

    scored = sorted(
        ((lexical_score(query, chunk), chunk) for chunk in candidates),
        key=lambda item: item[0],
        reverse=True,
    )
    score, chunk = scored[0]
    return chunk, score


def make_audit_hash(record_payload: Dict[str, object]) -> str:
    return stable_hash(record_payload)


def run_hsrag_smoke_test(cases: Sequence[QueryCase]) -> List[RetrievalRecord]:
    records: List[RetrievalRecord] = []
    previous_hash = "GENESIS"

    for case in cases:
        started = time.perf_counter()

        decision, routed_corpus_id, routed_jurisdiction, reason = classify_query(case.query)
        chunk, score = retrieve_bounded_evidence(case.query, routed_corpus_id)

        elapsed_ms = (time.perf_counter() - started) * 1000.0

        record_payload = {
            "case_id": case.case_id,
            "query": case.query,
            "case_type": case.case_type,
            "decision": decision,
            "reason": reason,
            "expected_corpus_id": case.expected_corpus_id,
            "expected_jurisdiction": case.expected_jurisdiction,
            "routed_corpus_id": routed_corpus_id,
            "routed_jurisdiction": routed_jurisdiction,
            "retrieved_chunk_id": chunk.chunk_id if chunk else None,
            "retrieved_corpus_id": chunk.corpus_id if chunk else None,
            "retrieved_jurisdiction": chunk.jurisdiction if chunk else None,
            "lexical_score": score,
            "previous_hash": previous_hash,
        }

        audit_hash = make_audit_hash(record_payload)

        records.append(
            RetrievalRecord(
                case_id=case.case_id,
                query=case.query,
                case_type=case.case_type,
                decision=decision,
                reason=reason,
                expected_corpus_id=case.expected_corpus_id,
                expected_jurisdiction=case.expected_jurisdiction,
                routed_corpus_id=routed_corpus_id,
                routed_jurisdiction=routed_jurisdiction,
                retrieved_chunk_id=chunk.chunk_id if chunk else None,
                retrieved_corpus_id=chunk.corpus_id if chunk else None,
                retrieved_jurisdiction=chunk.jurisdiction if chunk else None,
                lexical_score=score,
                latency_ms=elapsed_ms,
                previous_hash=previous_hash,
                audit_hash=audit_hash,
            )
        )

        previous_hash = audit_hash

    return records


# =============================================================================
# Baseline: simple lexical global top-1 comparison
# =============================================================================

def run_lexical_baseline(cases: Sequence[QueryCase]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for case in cases:
        started = time.perf_counter()
        scored = sorted(
            ((lexical_score(case.query, chunk), chunk) for chunk in CHUNKS),
            key=lambda item: item[0],
            reverse=True,
        )

        score, chunk = scored[0]
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        rows.append(
            {
                "case_id": case.case_id,
                "case_type": case.case_type,
                "query": case.query,
                "expected_corpus_id": case.expected_corpus_id,
                "expected_jurisdiction": case.expected_jurisdiction,
                "retrieved_chunk_id": chunk.chunk_id,
                "retrieved_corpus_id": chunk.corpus_id,
                "retrieved_jurisdiction": chunk.jurisdiction,
                "lexical_score": score,
                "latency_ms": elapsed_ms,
            }
        )

    return rows


# =============================================================================
# VPSM / Audit-S: Metrics, gates, and output artifacts
# =============================================================================

def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    rank = (len(ordered) - 1) * p
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def verify_audit_chain(records: Sequence[RetrievalRecord]) -> bool:
    expected_previous = "GENESIS"

    for record in records:
        if record.previous_hash != expected_previous:
            return False

        payload = {
            "case_id": record.case_id,
            "query": record.query,
            "case_type": record.case_type,
            "decision": record.decision,
            "reason": record.reason,
            "expected_corpus_id": record.expected_corpus_id,
            "expected_jurisdiction": record.expected_jurisdiction,
            "routed_corpus_id": record.routed_corpus_id,
            "routed_jurisdiction": record.routed_jurisdiction,
            "retrieved_chunk_id": record.retrieved_chunk_id,
            "retrieved_corpus_id": record.retrieved_corpus_id,
            "retrieved_jurisdiction": record.retrieved_jurisdiction,
            "lexical_score": record.lexical_score,
            "previous_hash": record.previous_hash,
        }

        recomputed = make_audit_hash(payload)
        if recomputed != record.audit_hash:
            return False

        expected_previous = record.audit_hash

    return True


def compute_hsrag_metrics(records: Sequence[RetrievalRecord]) -> Dict[str, float]:
    target_records = [r for r in records if r.case_type == "target"]
    no_evidence_records = [r for r in records if r.case_type == "no_evidence"]
    ambiguous_records = [r for r in records if r.case_type == "ambiguous"]
    mismatch_records = [r for r in records if r.case_type == "mismatch"]

    target_correct_count = sum(
        1
        for r in target_records
        if r.decision == "ALLOW" and r.retrieved_corpus_id == r.expected_corpus_id
    )

    wrong_corpus_collision_count = sum(
        1
        for r in target_records
        if r.decision == "ALLOW" and r.retrieved_corpus_id != r.expected_corpus_id
    )

    wrong_jurisdiction_escape_count = sum(
        1
        for r in target_records
        if r.decision == "ALLOW" and r.retrieved_jurisdiction != r.expected_jurisdiction
    )

    no_evidence_false_allow_count = sum(
        1 for r in no_evidence_records if r.decision == "ALLOW"
    )
    ambiguous_false_allow_count = sum(
        1 for r in ambiguous_records if r.decision == "ALLOW"
    )
    mismatch_escape_count = sum(
        1 for r in mismatch_records if r.decision == "ALLOW"
    )

    latency_values = [r.latency_ms for r in records]

    return {
        "target_cases": float(len(target_records)),
        "total_cases": float(len(records)),
        "target_correct": ratio(target_correct_count, len(target_records)),
        "wrong_corpus_collision": ratio(
            wrong_corpus_collision_count, len(target_records)
        ),
        "wrong_jurisdiction_escape": ratio(
            wrong_jurisdiction_escape_count, len(target_records)
        ),
        "no_evidence_false_allow": ratio(
            no_evidence_false_allow_count, len(no_evidence_records)
        ),
        "ambiguous_false_allow": ratio(
            ambiguous_false_allow_count, len(ambiguous_records)
        ),
        "mismatch_escape": ratio(
            mismatch_escape_count, len(mismatch_records)
        ),
        "audit_chain_complete": 1.0 if verify_audit_chain(records) else 0.0,
        "p50_latency_ms": median(latency_values) if latency_values else 0.0,
        "p95_latency_ms": percentile(latency_values, 0.95),
    }


def compute_baseline_metrics(rows: Sequence[Dict[str, object]]) -> Dict[str, float]:
    target_rows = [r for r in rows if r["case_type"] == "target"]
    no_evidence_rows = [r for r in rows if r["case_type"] == "no_evidence"]
    ambiguous_rows = [r for r in rows if r["case_type"] == "ambiguous"]
    mismatch_rows = [r for r in rows if r["case_type"] == "mismatch"]

    target_correct_count = sum(
        1
        for r in target_rows
        if r["retrieved_corpus_id"] == r["expected_corpus_id"]
    )
    wrong_corpus_collision_count = sum(
        1
        for r in target_rows
        if r["retrieved_corpus_id"] != r["expected_corpus_id"]
    )

    # A plain global lexical baseline always retrieves something here,
    # so false-allow style metrics are measured as retrieval escape.
    no_evidence_false_allow_count = len(no_evidence_rows)
    ambiguous_false_allow_count = len(ambiguous_rows)
    mismatch_escape_count = len(mismatch_rows)

    latency_values = [float(r["latency_ms"]) for r in rows]

    return {
        "target_correct": ratio(target_correct_count, len(target_rows)),
        "wrong_corpus_collision": ratio(
            wrong_corpus_collision_count, len(target_rows)
        ),
        "no_evidence_false_allow": ratio(
            no_evidence_false_allow_count, len(no_evidence_rows)
        ),
        "ambiguous_false_allow": ratio(
            ambiguous_false_allow_count, len(ambiguous_rows)
        ),
        "mismatch_escape": ratio(
            mismatch_escape_count, len(mismatch_rows)
        ),
        "p50_latency_ms": median(latency_values) if latency_values else 0.0,
        "p95_latency_ms": percentile(latency_values, 0.95),
    }


def acceptance_decision(metrics: Dict[str, float]) -> Tuple[str, List[str]]:
    failures: List[str] = []

    expected_zero_metrics = [
        "wrong_corpus_collision",
        "wrong_jurisdiction_escape",
        "no_evidence_false_allow",
        "ambiguous_false_allow",
        "mismatch_escape",
    ]

    if metrics["target_correct"] != 1.0:
        failures.append("target_correct must equal 1.0")

    for key in expected_zero_metrics:
        if metrics[key] != 0.0:
            failures.append(f"{key} must equal 0.0")

    if metrics["audit_chain_complete"] != 1.0:
        failures.append("audit_chain_complete must equal 1.0")

    if metrics["p95_latency_ms"] >= 20.0:
        failures.append("p95_latency_ms must be below 20ms for this smoke test")

    if failures:
        return "SMOKE_TEST_FAIL", failures

    return "SMOKE_TEST_PASS", []


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_records_csv(path: Path, records: Sequence[RetrievalRecord]) -> None:
    if not records:
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_markdown_summary(
    path: Path,
    decision: str,
    metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    failures: Sequence[str],
) -> None:
    lines = [
        "# HSRAG LAW Smoke Test Summary",
        "",
        f"Decision: `{decision}`",
        "",
        "## HSRAG Smoke Metrics",
        "",
        f"- target_correct: `{metrics['target_correct']}`",
        f"- wrong_corpus_collision: `{metrics['wrong_corpus_collision']}`",
        f"- wrong_jurisdiction_escape: `{metrics['wrong_jurisdiction_escape']}`",
        f"- no_evidence_false_allow: `{metrics['no_evidence_false_allow']}`",
        f"- ambiguous_false_allow: `{metrics['ambiguous_false_allow']}`",
        f"- mismatch_escape: `{metrics['mismatch_escape']}`",
        f"- audit_chain_complete: `{metrics['audit_chain_complete']}`",
        f"- p95_latency_ms: `{metrics['p95_latency_ms']:.6f}`",
        "",
        "## Lexical Baseline Reference",
        "",
        f"- target_correct: `{baseline_metrics['target_correct']}`",
        f"- wrong_corpus_collision: `{baseline_metrics['wrong_corpus_collision']}`",
        f"- no_evidence_false_allow: `{baseline_metrics['no_evidence_false_allow']}`",
        f"- ambiguous_false_allow: `{baseline_metrics['ambiguous_false_allow']}`",
        f"- mismatch_escape: `{baseline_metrics['mismatch_escape']}`",
        f"- p95_latency_ms: `{baseline_metrics['p95_latency_ms']:.6f}`",
        "",
        "## Notes",
        "",
        "This is a deterministic smoke test, not the full RQ1/RQ2/RQ3 benchmark reproduction.",
    ]

    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    decision: str,
    metrics: Dict[str, float],
    baseline_metrics: Dict[str, float],
    failures: Sequence[str],
) -> None:
    print("=" * 72)
    print("HSRAG LAW SMOKE TEST")
    print("=" * 72)
    print(f"decision: {decision}")
    print("")
    print("HSRAG:")
    print(f"  target_correct: {metrics['target_correct']}")
    print(f"  wrong_corpus_collision: {metrics['wrong_corpus_collision']}")
    print(f"  wrong_jurisdiction_escape: {metrics['wrong_jurisdiction_escape']}")
    print(f"  no_evidence_false_allow: {metrics['no_evidence_false_allow']}")
    print(f"  ambiguous_false_allow: {metrics['ambiguous_false_allow']}")
    print(f"  mismatch_escape: {metrics['mismatch_escape']}")
    print(f"  audit_chain_complete: {metrics['audit_chain_complete']}")
    print(f"  p95_latency_ms: {metrics['p95_latency_ms']:.6f}")
    print("")
    print("Lexical baseline reference:")
    print(f"  target_correct: {baseline_metrics['target_correct']}")
    print(f"  wrong_corpus_collision: {baseline_metrics['wrong_corpus_collision']}")
    print(f"  no_evidence_false_allow: {baseline_metrics['no_evidence_false_allow']}")
    print(f"  ambiguous_false_allow: {baseline_metrics['ambiguous_false_allow']}")
    print(f"  mismatch_escape: {baseline_metrics['mismatch_escape']}")
    print(f"  p95_latency_ms: {baseline_metrics['p95_latency_ms']:.6f}")

    if failures:
        print("")
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")

    print("")
    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 72)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    hsrag_records = run_hsrag_smoke_test(QUERY_CASES)
    baseline_rows = run_lexical_baseline(QUERY_CASES)

    hsrag_metrics = compute_hsrag_metrics(hsrag_records)
    baseline_metrics = compute_baseline_metrics(baseline_rows)

    decision, failures = acceptance_decision(hsrag_metrics)

    summary_payload = {
        "name": "HSRAG-LAW-Smoke-Demo",
        "decision": decision,
        "failures": list(failures),
        "hsrag_metrics": hsrag_metrics,
        "lexical_baseline_metrics": baseline_metrics,
        "official_reference_results_not_recomputed": OFFICIAL_REFERENCE_RESULTS,
        "notes": [
            "This smoke test is deterministic and self-contained.",
            "It does not reproduce the full RQ1/RQ2/RQ3 benchmark packages.",
            "It is intended to validate repository wiring and HSRAG LAW control flow.",
        ],
    }

    write_json(RESULTS_DIR / "smoke_test_summary.json", summary_payload)
    write_records_csv(RESULTS_DIR / "smoke_test_records.csv", hsrag_records)
    write_markdown_summary(
        RESULTS_DIR / "smoke_test_summary.md",
        decision,
        hsrag_metrics,
        baseline_metrics,
        failures,
    )

    print_summary(decision, hsrag_metrics, baseline_metrics, failures)

    if decision != "SMOKE_TEST_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()