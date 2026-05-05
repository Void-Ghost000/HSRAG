"""
HSRAG LAW — RQ3 FIX2 Verification Script
========================================

RQ3 = EU × US Real-Law Collision Benchmark
FIX2 = Jurisdiction Hierarchy Normalization

This verifier checks the frozen RQ3 FIX2 benchmark result for HSRAG LAW:

- EU AI Act
- EU DMA
- US COPPA
- CDA Section 230
- FTC Act Section 5
- CCPA
- 244 chunks
- 592 base queries
- 14,208 MC mutation cases
- 4 lexical baseline modes
- wrong-corpus collision gate
- wrong-jurisdiction escape gate after hierarchy normalization
- audit hash chain
- consistency matrix

This script does NOT re-run the full original MC benchmark package.
It verifies the frozen benchmark summary and produces auditable result artifacts
for the public repository.

QSVCS annotations:
- CTHC: classify benchmark evidence by corpus / jurisdiction / baseline mode.
- QOIM: enforce acceptance gates and legal-domain feasibility boundaries.
- SGF: execute verification in fixed forward-only order.
- VPSM: represent RQ3 state as structured metric vectors.
- Audit-S: write append-only hash chain for verification events.

Run from repository root:

    python examples/hsrag_law/scripts/verify_rq3_fix2.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


# =============================================================================
# Path resolution
# =============================================================================

THIS_FILE = Path(__file__).resolve()

if THIS_FILE.parent.name == "scripts":
    EXAMPLE_ROOT = THIS_FILE.parent.parent
else:
    EXAMPLE_ROOT = THIS_FILE.parent

REPO_ROOT = EXAMPLE_ROOT.parents[1] if len(EXAMPLE_ROOT.parents) >= 2 else EXAMPLE_ROOT
RESULTS_DIR = EXAMPLE_ROOT / "results"


# =============================================================================
# Frozen RQ3 FIX2 benchmark result
# =============================================================================

RQ3_FIX2_FROZEN_RESULT: Dict[str, Any] = {
    "name": "HSRAG-RQ3-EU-US-RealLaw-Collision-10kMC-v0.1-FIX2-JurisdictionNormalization",
    "parent_baseline": "HSRAG-RQ2.2-RealEU-Law-FourBaselines-10kMC-v0.1",
    "semantic_label": "REAL_EU_US_PUBLIC_LEGAL_REFERENCE_WITH_OFFICIAL_URLS",
    "real_primary_verified": False,
    "purpose": (
        "Extend HSRAG LAW from EU-only legal retrieval to EU × US real-law "
        "collision testing across AI Act, DMA, COPPA, CDA Section 230, "
        "FTC Act Section 5, and CCPA."
    ),
    "decision": "RQ3_EU_US_REALLAW_COLLISION_PASS",
    "fail_count": 0,
    "fix_label": "FIX2_JURISDICTION_HIERARCHY_NORMALIZATION",
    "fix_description": (
        "Expected US jurisdiction accepts US-* subjurisdictions such as US-CA. "
        "This patch does not change retrieval output; it only corrects the "
        "jurisdiction hierarchy metric."
    ),
    "raw_fix1_hsrag_wrong_jurisdiction_escape": 0.0033783783783783786,
    "fix2_normalized_hsrag_wrong_jurisdiction_escape": 0.0,
    "artifact_content_hash": (
        "sha256:4433e52b30e445b5fb9cea0ad1dcdd9e965362680a5068312589bb20981be7ab"
    ),
    "zip_sha256": (
        "sha256:8a71378a56fdf4a8824e4057a5bd22e678b475081afe58a9dd6812fe18abf858"
    ),
    "chunks": 244,
    "corpus_distribution": {
        "EU_AI_ACT": 130,
        "EU_DMA": 58,
        "US_CCPA": 21,
        "US_CDA230": 6,
        "US_COPPA": 5,
        "US_FTC_ACT5": 24,
    },
    "base_queries": 592,
    "mc_cases": 14208,
    "corpora": [
        "EU_AI_ACT",
        "EU_DMA",
        "US_CCPA",
        "US_CDA230",
        "US_COPPA",
        "US_FTC_ACT5",
    ],
    "jurisdictions": [
        "EU",
        "US",
        "US-CA",
    ],
    "mutation_modes": [
        "pointer_injection",
        "jurisdiction_distractor",
        "case_punctuation_noise",
        "legalese_paraphrase",
        "polite_prefix",
        "irrelevant_tail",
        "typo_light",
        "order_shuffle",
    ],
    "baseline_modes": [
        "bm25_domain_hint_topk",
        "bm25_global_topk",
        "tfidf_domain_hint_topk",
        "tfidf_global_topk",
    ],
    "hsrag_metrics": {
        "target_correct": 1.0,
        "wrong_corpus_collision": 0.0,
        "wrong_jurisdiction_escape": 0.0,
        "no_evidence_false_allow": 0.0,
        "ambiguous_false_allow": 0.0,
        "mismatch_escape": 0.0,
        "audit_chain_complete": 1.0,
        "p95_latency_ms": 5.924376599796233,
    },
    "best_baseline_metrics": {
        "target_correct": 0.9079391891891891,
        "wrong_corpus_collision": 0.019566441441441443,
        "wrong_jurisdiction_escape": 0.01097972972972973,
        "no_evidence_false_allow": 0.9666666666666667,
        "ambiguous_false_allow": 1.0,
        "mismatch_escape": 1.0,
        "token_reduction_pct_max": 78.70881065021146,
        "cost_reduction_pct_max": 73.55123408683025,
        "p95_latency_ms": 6.7050616002234165,
        "latency_ratio_max": 1.242680580221719,
    },
    "baseline_details": [
        {
            "mode": "bm25_domain_hint_topk",
            "target_correct": 0.9079391891891891,
            "wrong_corpus_collision": 0.019566441441441443,
            "wrong_jurisdiction_escape": 0.01097972972972973,
            "p95_latency_ms": 6.7050616002234165,
        },
        {
            "mode": "bm25_global_topk",
            "target_correct": 0.8760557432432432,
            "wrong_corpus_collision": 0.47740709459459457,
            "wrong_jurisdiction_escape": 0.03265765765765766,
            "p95_latency_ms": 7.362108,
        },
        {
            "mode": "tfidf_domain_hint_topk",
            "target_correct": 0.9066019144144144,
            "wrong_corpus_collision": 0.02005855855855856,
            "wrong_jurisdiction_escape": 0.011050112612612612,
            "p95_latency_ms": 6.127217,
        },
        {
            "mode": "tfidf_global_topk",
            "target_correct": 0.8669763513513513,
            "wrong_corpus_collision": 0.5244228603603603,
            "wrong_jurisdiction_escape": 0.04490427927927928,
            "p95_latency_ms": 6.699384,
        },
    ],
}


# =============================================================================
# Data models
# =============================================================================

@dataclass
class GateCheck:
    gate_id: str
    description: str
    expected: Any
    actual: Any
    passed: bool
    severity: str


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


@dataclass
class BaselineRow:
    mode: str
    target_correct: float
    wrong_corpus_collision: float
    wrong_jurisdiction_escape: float
    p95_latency_ms: float
    target_correct_gap_vs_hsrag: float
    wrong_corpus_collision_gap_vs_hsrag: float
    wrong_jurisdiction_escape_gap_vs_hsrag: float
    latency_gap_vs_hsrag_ms: float


# =============================================================================
# Utility functions
# =============================================================================

def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_dataclass_csv(path: Path, rows: Sequence[Any]) -> None:
    if not rows:
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_dict_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# =============================================================================
# QOIM: acceptance gate checks
# =============================================================================

def build_rq3_gate_checks(result: Dict[str, Any]) -> List[GateCheck]:
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]

    checks = [
        GateCheck(
            gate_id="RQ3_DECISION",
            description="Frozen RQ3 FIX2 decision must be pass.",
            expected="RQ3_EU_US_REALLAW_COLLISION_PASS",
            actual=result.get("decision"),
            passed=result.get("decision") == "RQ3_EU_US_REALLAW_COLLISION_PASS",
            severity="HARD",
        ),
        GateCheck(
            gate_id="FAIL_COUNT_ZERO",
            description="fail_count must equal 0.",
            expected=0,
            actual=result.get("fail_count"),
            passed=result.get("fail_count") == 0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="MC_CASES_MINIMUM",
            description="RQ3 must include at least 10,000 MC mutation cases.",
            expected=">= 10000",
            actual=result.get("mc_cases"),
            passed=int(result.get("mc_cases", 0)) >= 10000,
            severity="HARD",
        ),
        GateCheck(
            gate_id="CORPORA_MINIMUM",
            description="RQ3 must include at least 6 corpora.",
            expected=">= 6",
            actual=len(result.get("corpora", [])),
            passed=len(result.get("corpora", [])) >= 6,
            severity="HARD",
        ),
        GateCheck(
            gate_id="BASELINE_MODES_MINIMUM",
            description="RQ3 must include at least 4 baseline modes.",
            expected=">= 4",
            actual=len(result.get("baseline_modes", [])),
            passed=len(result.get("baseline_modes", [])) >= 4,
            severity="HARD",
        ),
        GateCheck(
            gate_id="MUTATION_MODES_PRESENT",
            description="Mutation modes must be present for adversarial scope.",
            expected=">= 1",
            actual=len(result.get("mutation_modes", [])),
            passed=len(result.get("mutation_modes", [])) >= 1,
            severity="HARD",
        ),
        GateCheck(
            gate_id="FIX2_JURISDICTION_NORMALIZATION_APPLIED",
            description="FIX2 normalized jurisdiction escape must equal 0.0.",
            expected=0.0,
            actual=result.get("fix2_normalized_hsrag_wrong_jurisdiction_escape"),
            passed=float(result.get("fix2_normalized_hsrag_wrong_jurisdiction_escape", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="FIX1_RAW_JURISDICTION_ESCAPE_RECORDED",
            description="FIX1 raw jurisdiction escape should be recorded for audit traceability.",
            expected="present",
            actual=result.get("raw_fix1_hsrag_wrong_jurisdiction_escape"),
            passed=result.get("raw_fix1_hsrag_wrong_jurisdiction_escape") is not None,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_TARGET_CORRECT",
            description="HSRAG target correctness must be at least 0.995.",
            expected=">= 0.995",
            actual=hsrag.get("target_correct"),
            passed=float(hsrag.get("target_correct", 0.0)) >= 0.995,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_WRONG_CORPUS_COLLISION_ZERO",
            description="HSRAG wrong corpus collision must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("wrong_corpus_collision"),
            passed=float(hsrag.get("wrong_corpus_collision", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_WRONG_JURISDICTION_ESCAPE_ZERO",
            description="HSRAG wrong jurisdiction escape must equal 0.0 after hierarchy normalization.",
            expected=0.0,
            actual=hsrag.get("wrong_jurisdiction_escape"),
            passed=float(hsrag.get("wrong_jurisdiction_escape", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_NO_EVIDENCE_FALSE_ALLOW_ZERO",
            description="HSRAG no-evidence false allow must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("no_evidence_false_allow"),
            passed=float(hsrag.get("no_evidence_false_allow", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AMBIGUOUS_FALSE_ALLOW_ZERO",
            description="HSRAG ambiguous false allow must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("ambiguous_false_allow"),
            passed=float(hsrag.get("ambiguous_false_allow", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_MISMATCH_ESCAPE_ZERO",
            description="HSRAG mismatch escape must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("mismatch_escape"),
            passed=float(hsrag.get("mismatch_escape", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AUDIT_CHAIN_COMPLETE",
            description="HSRAG audit chain completion must equal 1.0.",
            expected=1.0,
            actual=hsrag.get("audit_chain_complete"),
            passed=float(hsrag.get("audit_chain_complete", 0.0)) == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_P95_LATENCY_LT_15MS",
            description="HSRAG p95 latency must be below 15ms.",
            expected="< 15ms",
            actual=hsrag.get("p95_latency_ms"),
            passed=float(hsrag.get("p95_latency_ms", 999.0)) < 15.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="BEST_BASELINE_NONZERO_WRONG_CORPUS",
            description="Best baseline should expose nonzero wrong-corpus collision risk.",
            expected="> 0.0",
            actual=best.get("wrong_corpus_collision"),
            passed=float(best.get("wrong_corpus_collision", 0.0)) > 0.0,
            severity="SOFT",
        ),
        GateCheck(
            gate_id="BEST_BASELINE_NONZERO_WRONG_JURISDICTION",
            description="Best baseline should expose nonzero wrong-jurisdiction escape risk.",
            expected="> 0.0",
            actual=best.get("wrong_jurisdiction_escape"),
            passed=float(best.get("wrong_jurisdiction_escape", 0.0)) > 0.0,
            severity="SOFT",
        ),
        GateCheck(
            gate_id="ARTIFACT_HASH_PRESENT",
            description="artifact_content_hash must be present.",
            expected="present sha256",
            actual=result.get("artifact_content_hash"),
            passed=str(result.get("artifact_content_hash", "")).startswith("sha256:"),
            severity="HARD",
        ),
        GateCheck(
            gate_id="ZIP_HASH_PRESENT",
            description="zip_sha256 must be present.",
            expected="present sha256",
            actual=result.get("zip_sha256"),
            passed=str(result.get("zip_sha256", "")).startswith("sha256:"),
            severity="HARD",
        ),
    ]

    return checks


def summarize_gate_checks(checks: Sequence[GateCheck]) -> Tuple[str, List[str]]:
    hard_failures = [
        f"{check.gate_id}: expected={check.expected}, actual={check.actual}"
        for check in checks
        if check.severity == "HARD" and not check.passed
    ]

    if hard_failures:
        return "RQ3_FIX2_VERIFICATION_FAIL", hard_failures

    return "RQ3_FIX2_VERIFICATION_PASS", []


# =============================================================================
# VPSM: comparison vectors
# =============================================================================

def build_baseline_rows(result: Dict[str, Any]) -> List[BaselineRow]:
    hsrag = result["hsrag_metrics"]
    rows: List[BaselineRow] = []

    for item in result["baseline_details"]:
        rows.append(
            BaselineRow(
                mode=str(item["mode"]),
                target_correct=float(item["target_correct"]),
                wrong_corpus_collision=float(item["wrong_corpus_collision"]),
                wrong_jurisdiction_escape=float(item["wrong_jurisdiction_escape"]),
                p95_latency_ms=float(item["p95_latency_ms"]),
                target_correct_gap_vs_hsrag=(
                    float(hsrag["target_correct"]) - float(item["target_correct"])
                ),
                wrong_corpus_collision_gap_vs_hsrag=(
                    float(item["wrong_corpus_collision"])
                    - float(hsrag["wrong_corpus_collision"])
                ),
                wrong_jurisdiction_escape_gap_vs_hsrag=(
                    float(item["wrong_jurisdiction_escape"])
                    - float(hsrag["wrong_jurisdiction_escape"])
                ),
                latency_gap_vs_hsrag_ms=(
                    float(item["p95_latency_ms"]) - float(hsrag["p95_latency_ms"])
                ),
            )
        )

    return rows


def build_consistency_matrix(
    core_decision: str,
    audit_chain_complete: bool,
) -> List[Dict[str, Any]]:
    result = RQ3_FIX2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]

    return [
        {
            "rq": "RQ3_FIX2",
            "benchmark_role": "eu_us_real_law_collision_control",
            "corpora": "|".join(result["corpora"]),
            "jurisdictions": "|".join(result["jurisdictions"]),
            "requires_mc": True,
            "mc_cases": result["mc_cases"],
            "baseline_modes": len(result["baseline_modes"]),
            "source_status": result["semantic_label"],
            "real_primary_verified": result["real_primary_verified"],
            "core_decision": core_decision,
            "fix_label": result["fix_label"],
            "raw_fix1_wrong_jurisdiction_escape": result[
                "raw_fix1_hsrag_wrong_jurisdiction_escape"
            ],
            "fix2_normalized_wrong_jurisdiction_escape": result[
                "fix2_normalized_hsrag_wrong_jurisdiction_escape"
            ],
            "hsrag_target_correct": hsrag["target_correct"],
            "hsrag_wrong_corpus_collision": hsrag["wrong_corpus_collision"],
            "hsrag_wrong_jurisdiction_escape": hsrag["wrong_jurisdiction_escape"],
            "hsrag_no_evidence_false_allow": hsrag["no_evidence_false_allow"],
            "hsrag_ambiguous_false_allow": hsrag["ambiguous_false_allow"],
            "hsrag_mismatch_escape": hsrag["mismatch_escape"],
            "hsrag_audit_chain_complete": hsrag["audit_chain_complete"],
            "local_verifier_audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
            "best_baseline_target_correct": best["target_correct"],
            "best_baseline_wrong_corpus_collision": best["wrong_corpus_collision"],
            "best_baseline_wrong_jurisdiction_escape": best["wrong_jurisdiction_escape"],
            "token_reduction_pct_max": best["token_reduction_pct_max"],
            "cost_reduction_pct_max": best["cost_reduction_pct_max"],
            "notes": (
                "RQ3 FIX2 is an EU x US collision benchmark. Jurisdiction hierarchy "
                "normalization accepts US-* subjurisdictions for expected US labels. "
                "This fixes metric semantics without changing retrieval outputs."
            ),
        }
    ]


# =============================================================================
# Audit-S: hash chain
# =============================================================================

def build_audit_chain(
    checks: Sequence[GateCheck],
    baseline_rows: Sequence[BaselineRow],
    consistency_matrix: Sequence[Dict[str, Any]],
) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous_hash = "GENESIS"

    payloads: List[Tuple[str, Dict[str, Any]]] = [
        ("RQ3_FIX2_FROZEN_RESULT", RQ3_FIX2_FROZEN_RESULT),
        ("RQ3_FIX2_GATE_CHECKS", {"checks": [asdict(check) for check in checks]}),
        ("RQ3_FIX2_BASELINE_ROWS", {"rows": [asdict(row) for row in baseline_rows]}),
        ("RQ3_FIX2_CONSISTENCY_MATRIX", {"rows": list(consistency_matrix)}),
    ]

    for index, (event_type, payload) in enumerate(payloads):
        event_payload = {
            "index": index,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        event_hash = stable_json_hash(event_payload)

        events.append(
            AuditEvent(
                index=index,
                event_type=event_type,
                payload=payload,
                previous_hash=previous_hash,
                event_hash=event_hash,
            )
        )

        previous_hash = event_hash

    return events


def verify_audit_chain(events: Sequence[AuditEvent]) -> bool:
    expected_previous = "GENESIS"

    for event in events:
        if event.previous_hash != expected_previous:
            return False

        recompute_payload = {
            "index": event.index,
            "event_type": event.event_type,
            "payload": event.payload,
            "previous_hash": event.previous_hash,
        }
        recomputed = stable_json_hash(recompute_payload)

        if recomputed != event.event_hash:
            return False

        expected_previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


# =============================================================================
# Markdown / print outputs
# =============================================================================

def write_markdown_summary(
    path: Path,
    core_decision: str,
    failures: Sequence[str],
    checks: Sequence[GateCheck],
    baseline_rows: Sequence[BaselineRow],
    audit_chain_complete: bool,
) -> None:
    result = RQ3_FIX2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]
    passed_count = sum(1 for check in checks if check.passed)
    total_count = len(checks)

    lines = [
        "# RQ3 FIX2 Verification Summary",
        "",
        f"Core decision: `{core_decision}`",
        f"Audit chain complete: `{1.0 if audit_chain_complete else 0.0}`",
        "",
        "## RQ3 Purpose",
        "",
        (
            "RQ3 verifies the HSRAG LAW EU × US real-law collision benchmark, "
            "testing wrong-corpus collision and wrong-jurisdiction escape across "
            "multiple legal corpora and jurisdictions."
        ),
        "",
        "## FIX2 Jurisdiction Normalization",
        "",
        f"- fix_label: `{result['fix_label']}`",
        f"- raw FIX1 wrong_jurisdiction_escape: `{result['raw_fix1_hsrag_wrong_jurisdiction_escape']}`",
        f"- FIX2 normalized wrong_jurisdiction_escape: `{result['fix2_normalized_hsrag_wrong_jurisdiction_escape']}`",
        "",
        "## Benchmark Scope",
        "",
        f"- semantic label: `{result['semantic_label']}`",
        f"- chunks: `{result['chunks']}`",
        f"- base queries: `{result['base_queries']}`",
        f"- MC cases: `{result['mc_cases']}`",
        f"- corpora: `{len(result['corpora'])}`",
        f"- jurisdictions: `{len(result['jurisdictions'])}`",
        f"- baseline modes: `{len(result['baseline_modes'])}`",
        f"- fail_count: `{result['fail_count']}`",
        "",
        "## HSRAG Metrics",
        "",
        f"- target_correct: `{hsrag['target_correct']}`",
        f"- wrong_corpus_collision: `{hsrag['wrong_corpus_collision']}`",
        f"- wrong_jurisdiction_escape: `{hsrag['wrong_jurisdiction_escape']}`",
        f"- no_evidence_false_allow: `{hsrag['no_evidence_false_allow']}`",
        f"- ambiguous_false_allow: `{hsrag['ambiguous_false_allow']}`",
        f"- mismatch_escape: `{hsrag['mismatch_escape']}`",
        f"- audit_chain_complete: `{hsrag['audit_chain_complete']}`",
        f"- p95_latency_ms: `{hsrag['p95_latency_ms']}`",
        "",
        "## Best Baseline Comparison",
        "",
        f"- target_correct: `{best['target_correct']}`",
        f"- wrong_corpus_collision: `{best['wrong_corpus_collision']}`",
        f"- wrong_jurisdiction_escape: `{best['wrong_jurisdiction_escape']}`",
        f"- no_evidence_false_allow: `{best['no_evidence_false_allow']}`",
        f"- ambiguous_false_allow: `{best['ambiguous_false_allow']}`",
        f"- mismatch_escape: `{best['mismatch_escape']}`",
        f"- token_reduction_pct_max: `{best['token_reduction_pct_max']}`",
        f"- cost_reduction_pct_max: `{best['cost_reduction_pct_max']}`",
        f"- p95_latency_ms: `{best['p95_latency_ms']}`",
        "",
        "## Gate Summary",
        "",
        f"- passed gates: `{passed_count}/{total_count}`",
        "",
        "## Baseline Details",
        "",
        "| mode | target_correct | wrong_corpus_collision | wrong_jurisdiction_escape | p95_latency_ms |",
        "|---|---:|---:|---:|---:|",
    ]

    for row in baseline_rows:
        lines.append(
            f"| {row.mode} | {row.target_correct} | "
            f"{row.wrong_corpus_collision} | "
            f"{row.wrong_jurisdiction_escape} | "
            f"{row.p95_latency_ms} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This verifier checks the frozen RQ3 FIX2 benchmark summary.",
            "- It does not re-run the full original MC benchmark package.",
            "- RQ3 FIX2 corrects jurisdiction hierarchy metric semantics.",
            "- Official URL fetch reproducibility should be handled in a separate RQ4 pipeline.",
        ]
    )

    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    core_decision: str,
    failures: Sequence[str],
    audit_chain_complete: bool,
) -> None:
    result = RQ3_FIX2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]

    print("=" * 80)
    print("HSRAG LAW — RQ3 FIX2 VERIFICATION")
    print("=" * 80)
    print(f"core_decision: {core_decision}")
    print(f"audit_chain_complete: {1.0 if audit_chain_complete else 0.0}")
    print("")
    print("Scope:")
    print(f"  decision: {result['decision']}")
    print(f"  semantic_label: {result['semantic_label']}")
    print(f"  chunks: {result['chunks']}")
    print(f"  base_queries: {result['base_queries']}")
    print(f"  mc_cases: {result['mc_cases']}")
    print(f"  corpora: {len(result['corpora'])}")
    print(f"  jurisdictions: {len(result['jurisdictions'])}")
    print(f"  baseline_modes: {len(result['baseline_modes'])}")
    print(f"  fail_count: {result['fail_count']}")
    print("")
    print("FIX2:")
    print(f"  raw_fix1_wrong_jurisdiction_escape: {result['raw_fix1_hsrag_wrong_jurisdiction_escape']}")
    print(f"  fix2_normalized_wrong_jurisdiction_escape: {result['fix2_normalized_hsrag_wrong_jurisdiction_escape']}")
    print("")
    print("HSRAG:")
    print(f"  target_correct: {hsrag['target_correct']}")
    print(f"  wrong_corpus_collision: {hsrag['wrong_corpus_collision']}")
    print(f"  wrong_jurisdiction_escape: {hsrag['wrong_jurisdiction_escape']}")
    print(f"  no_evidence_false_allow: {hsrag['no_evidence_false_allow']}")
    print(f"  ambiguous_false_allow: {hsrag['ambiguous_false_allow']}")
    print(f"  mismatch_escape: {hsrag['mismatch_escape']}")
    print(f"  audit_chain_complete: {hsrag['audit_chain_complete']}")
    print(f"  p95_latency_ms: {hsrag['p95_latency_ms']}")
    print("")
    print("Best baseline:")
    print(f"  target_correct: {best['target_correct']}")
    print(f"  wrong_corpus_collision: {best['wrong_corpus_collision']}")
    print(f"  wrong_jurisdiction_escape: {best['wrong_jurisdiction_escape']}")
    print(f"  no_evidence_false_allow: {best['no_evidence_false_allow']}")
    print(f"  ambiguous_false_allow: {best['ambiguous_false_allow']}")
    print(f"  mismatch_escape: {best['mismatch_escape']}")
    print(f"  token_reduction_pct_max: {best['token_reduction_pct_max']}")
    print(f"  cost_reduction_pct_max: {best['cost_reduction_pct_max']}")
    print(f"  p95_latency_ms: {best['p95_latency_ms']}")

    if failures:
        print("")
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")

    print("")
    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 80)


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    ensure_dirs()

    checks = build_rq3_gate_checks(RQ3_FIX2_FROZEN_RESULT)
    core_decision, failures = summarize_gate_checks(checks)

    baseline_rows = build_baseline_rows(RQ3_FIX2_FROZEN_RESULT)

    consistency_matrix = build_consistency_matrix(
        core_decision=core_decision,
        audit_chain_complete=True,
    )

    audit_chain = build_audit_chain(
        checks=checks,
        baseline_rows=baseline_rows,
        consistency_matrix=consistency_matrix,
    )
    audit_chain_complete = verify_audit_chain(audit_chain)

    consistency_matrix = build_consistency_matrix(
        core_decision=core_decision,
        audit_chain_complete=audit_chain_complete,
    )

    summary_payload = {
        "name": "HSRAG-LAW-RQ3-FIX2-Verifier",
        "core_decision": core_decision,
        "failures": list(failures),
        "rq3_fix2_frozen_result": RQ3_FIX2_FROZEN_RESULT,
        "gate_checks": [asdict(check) for check in checks],
        "baseline_comparison": [asdict(row) for row in baseline_rows],
        "audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
        "consistency_matrix": consistency_matrix,
        "outputs": {
            "summary_json": "rq3_fix2_verification_summary.json",
            "summary_md": "rq3_fix2_verification_summary.md",
            "gate_checks_csv": "rq3_fix2_gate_checks.csv",
            "baseline_comparison_csv": "rq3_fix2_baseline_comparison.csv",
            "audit_chain_jsonl": "rq3_fix2_audit_chain.jsonl",
            "consistency_matrix_csv": "rq3_fix2_consistency_matrix.csv",
        },
    }

    write_json(RESULTS_DIR / "rq3_fix2_verification_summary.json", summary_payload)
    write_dataclass_csv(RESULTS_DIR / "rq3_fix2_gate_checks.csv", checks)
    write_dataclass_csv(RESULTS_DIR / "rq3_fix2_baseline_comparison.csv", baseline_rows)
    write_audit_chain(RESULTS_DIR / "rq3_fix2_audit_chain.jsonl", audit_chain)
    write_dict_csv(RESULTS_DIR / "rq3_fix2_consistency_matrix.csv", consistency_matrix)
    write_markdown_summary(
        RESULTS_DIR / "rq3_fix2_verification_summary.md",
        core_decision=core_decision,
        failures=failures,
        checks=checks,
        baseline_rows=baseline_rows,
        audit_chain_complete=audit_chain_complete,
    )

    print_summary(
        core_decision=core_decision,
        failures=failures,
        audit_chain_complete=audit_chain_complete,
    )

    if core_decision != "RQ3_FIX2_VERIFICATION_PASS":
        return 1

    if not audit_chain_complete:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())