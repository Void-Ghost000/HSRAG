"""
HSRAG LAW — RQ2.2 Verification Script
=====================================

RQ2.2 = Real EU Law + Four Baselines + 10k Monte Carlo benchmark.

This verifier checks the frozen RQ2.2 benchmark result for HSRAG LAW:

- uploaded EU AI Act + DMA legal PDFs with official references
- 188 chunks
- 424 base queries
- 24 MC seeds
- 10,176 mutation cases
- 4 lexical baseline modes
- HSRAG acceptance gates
- baseline comparison summary
- audit hash chain
- consistency matrix

This script does NOT re-run the full original benchmark. It verifies the frozen
benchmark summary and produces auditable result artifacts for the public repo.

QSVCS annotations:
- CTHC: classify benchmark evidence by corpus / mutation / baseline mode.
- QOIM: enforce acceptance gates and benchmark feasibility boundaries.
- SGF: execute verification in fixed forward-only order.
- VPSM: represent RQ2.2 state as structured metric vectors.
- Audit-S: write append-only hash chain for verification events.

Run from repository root:

    python examples/hsrag_law/scripts/verify_rq2_2.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


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
# Frozen RQ2.2 benchmark result
# =============================================================================

RQ2_2_FROZEN_RESULT: Dict[str, Any] = {
    "name": "HSRAG-RQ2.2-RealEU-Law-FourBaselines-10kMC-v0.1",
    "parent_baseline": "HSRAG-RQ2.1-Provenance-UnifiedTable-v0.1",
    "semantic_label": "REAL_UPLOADED_PDF_WITH_OFFICIAL_REFERENCE",
    "real_primary_verified": False,
    "purpose": (
        "Extend HSRAG LAW on real uploaded EU AI Act + DMA PDFs with official "
        "references to four lexical baselines and 10k+ MC mutation cases."
    ),
    "decision": "RQ2_2_FOUR_BASELINES_10KMC_PASS",
    "fail_count": 0,
    "artifact_content_hash": (
        "sha256:f56269a35fb300c48b3a5da620f8e2ac3b1e1729323514b18380252619fc8680"
    ),
    "zip_sha256": (
        "sha256:8bbe1400e8e619331c6de2e74cfdb13e5205db3af5176aa804bcc6e01e511ca2"
    ),
    "chunks": 188,
    "base_queries": 424,
    "mc_seeds": 24,
    "mc_cases": 10176,
    "mutation_modes": [
        "case_punctuation_noise",
        "jurisdiction_distractor",
        "pointer_injection",
        "legalese_paraphrase",
        "typo_light",
        "irrelevant_tail",
        "polite_prefix",
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
        "wrong_collision": 0.0,
        "no_evidence_false_allow": 0.0,
        "ambiguous_false_allow": 0.0,
        "mismatch_escape": 0.0,
        "audit_chain_complete": 1.0,
        "p95_latency_ms": 4.03891924997879,
    },
    "best_baseline_metrics": {
        "target_correct": 0.9391705974842768,
        "wrong_collision": 0.0376375786163522,
        "no_evidence_false_allow": 1.0,
        "ambiguous_false_allow": 1.0,
        "mismatch_escape": 1.0,
        "token_reduction_pct_max": 78.26886681010008,
        "cost_reduction_pct_max": 73.33315332219127,
        "p95_latency_ms": 6.851546500001859,
        "latency_ratio_max": 2.6526404925955656,
    },
    "baseline_details": [
        {
            "mode": "bm25_domain_hint_topk",
            "target_correct": 0.9391705974842768,
            "wrong_collision": 0.0376375786163522,
            "p95_latency_ms": 6.851546500001859,
        },
        {
            "mode": "bm25_global_topk",
            "target_correct": 0.9300314465408805,
            "wrong_collision": 0.5593553459119497,
            "p95_latency_ms": 10.713801,
        },
        {
            "mode": "tfidf_domain_hint_topk",
            "target_correct": 0.9387775157232704,
            "wrong_collision": 0.03803066037735849,
            "p95_latency_ms": 6.419456,
        },
        {
            "mode": "tfidf_global_topk",
            "target_correct": 0.9216776729559748,
            "wrong_collision": 0.5677083333333334,
            "p95_latency_ms": 6.708151,
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
    wrong_collision: float
    p95_latency_ms: float
    target_correct_gap_vs_hsrag: float
    wrong_collision_gap_vs_hsrag: float
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

def build_rq2_2_gate_checks(result: Dict[str, Any]) -> List[GateCheck]:
    hsrag = result["hsrag_metrics"]
    best_baseline = result["best_baseline_metrics"]

    checks = [
        GateCheck(
            gate_id="RQ2_2_DECISION",
            description="Frozen RQ2.2 decision must be pass.",
            expected="RQ2_2_FOUR_BASELINES_10KMC_PASS",
            actual=result.get("decision"),
            passed=result.get("decision") == "RQ2_2_FOUR_BASELINES_10KMC_PASS",
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
            description="RQ2.2 must include at least 10,000 MC mutation cases.",
            expected=">= 10000",
            actual=result.get("mc_cases"),
            passed=int(result.get("mc_cases", 0)) >= 10000,
            severity="HARD",
        ),
        GateCheck(
            gate_id="BASELINE_MODES_MINIMUM",
            description="RQ2.2 must include at least four baseline modes.",
            expected=">= 4",
            actual=len(result.get("baseline_modes", [])),
            passed=len(result.get("baseline_modes", [])) >= 4,
            severity="HARD",
        ),
        GateCheck(
            gate_id="MUTATION_MODES_PRESENT",
            description="Mutation modes must be present for MC robustness scope.",
            expected=">= 1",
            actual=len(result.get("mutation_modes", [])),
            passed=len(result.get("mutation_modes", [])) >= 1,
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
            gate_id="HSRAG_WRONG_COLLISION_ZERO",
            description="HSRAG wrong collision rate must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("wrong_collision"),
            passed=float(hsrag.get("wrong_collision", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_NO_EVIDENCE_FALSE_ALLOW_ZERO",
            description="HSRAG no-evidence false allow rate must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("no_evidence_false_allow"),
            passed=float(hsrag.get("no_evidence_false_allow", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AMBIGUOUS_FALSE_ALLOW_ZERO",
            description="HSRAG ambiguous false allow rate must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("ambiguous_false_allow"),
            passed=float(hsrag.get("ambiguous_false_allow", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_MISMATCH_ESCAPE_ZERO",
            description="HSRAG mismatch escape rate must equal 0.0.",
            expected=0.0,
            actual=hsrag.get("mismatch_escape"),
            passed=float(hsrag.get("mismatch_escape", 1.0)) == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AUDIT_CHAIN_COMPLETE",
            description="HSRAG audit-chain completion rate must equal 1.0.",
            expected=1.0,
            actual=hsrag.get("audit_chain_complete"),
            passed=float(hsrag.get("audit_chain_complete", 0.0)) == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_P95_LATENCY_LT_10MS",
            description="HSRAG p95 latency must be below 10ms.",
            expected="< 10ms",
            actual=hsrag.get("p95_latency_ms"),
            passed=float(hsrag.get("p95_latency_ms", 999.0)) < 10.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="BASELINE_HAS_NONZERO_WRONG_COLLISION",
            description=(
                "Best lexical baseline should expose nonzero wrong-collision risk "
                "in this benchmark comparison."
            ),
            expected="> 0.0",
            actual=best_baseline.get("wrong_collision"),
            passed=float(best_baseline.get("wrong_collision", 0.0)) > 0.0,
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
        return "RQ2_2_VERIFICATION_FAIL", hard_failures

    return "RQ2_2_VERIFICATION_PASS", []


# =============================================================================
# VPSM: baseline comparison vectors
# =============================================================================

def build_baseline_rows(result: Dict[str, Any]) -> List[BaselineRow]:
    hsrag = result["hsrag_metrics"]
    rows: List[BaselineRow] = []

    for item in result["baseline_details"]:
        rows.append(
            BaselineRow(
                mode=str(item["mode"]),
                target_correct=float(item["target_correct"]),
                wrong_collision=float(item["wrong_collision"]),
                p95_latency_ms=float(item["p95_latency_ms"]),
                target_correct_gap_vs_hsrag=(
                    float(hsrag["target_correct"]) - float(item["target_correct"])
                ),
                wrong_collision_gap_vs_hsrag=(
                    float(item["wrong_collision"]) - float(hsrag["wrong_collision"])
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
    result = RQ2_2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best_baseline = result["best_baseline_metrics"]

    return [
        {
            "rq": "RQ2.2",
            "benchmark_role": "real_eu_law_retrieval_robustness",
            "corpora": "EU_AI_ACT|EU_DMA",
            "requires_mc": True,
            "mc_cases": result["mc_cases"],
            "baseline_modes": len(result["baseline_modes"]),
            "source_status": result["semantic_label"],
            "real_primary_verified": result["real_primary_verified"],
            "core_decision": core_decision,
            "hsrag_target_correct": hsrag["target_correct"],
            "hsrag_wrong_collision": hsrag["wrong_collision"],
            "hsrag_no_evidence_false_allow": hsrag["no_evidence_false_allow"],
            "hsrag_ambiguous_false_allow": hsrag["ambiguous_false_allow"],
            "hsrag_mismatch_escape": hsrag["mismatch_escape"],
            "hsrag_audit_chain_complete": hsrag["audit_chain_complete"],
            "local_verifier_audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
            "best_baseline_target_correct": best_baseline["target_correct"],
            "best_baseline_wrong_collision": best_baseline["wrong_collision"],
            "token_reduction_pct_max": best_baseline["token_reduction_pct_max"],
            "cost_reduction_pct_max": best_baseline["cost_reduction_pct_max"],
            "notes": (
                "RQ2.2 is an adversarial retrieval benchmark with 10k+ MC cases. "
                "It uses real uploaded EU legal PDFs with official references, "
                "but does not claim official URL fetch reproduction as a hard gate."
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
        ("RQ2_2_FROZEN_RESULT", RQ2_2_FROZEN_RESULT),
        ("RQ2_2_GATE_CHECKS", {"checks": [asdict(check) for check in checks]}),
        ("RQ2_2_BASELINE_ROWS", {"rows": [asdict(row) for row in baseline_rows]}),
        ("RQ2_2_CONSISTENCY_MATRIX", {"rows": list(consistency_matrix)}),
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
    result = RQ2_2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]
    passed_count = sum(1 for check in checks if check.passed)
    total_count = len(checks)

    lines = [
        "# RQ2.2 Verification Summary",
        "",
        f"Core decision: `{core_decision}`",
        f"Audit chain complete: `{1.0 if audit_chain_complete else 0.0}`",
        "",
        "## RQ2.2 Purpose",
        "",
        (
            "RQ2.2 verifies the HSRAG LAW Real EU Law benchmark with four lexical "
            "baselines and 10k+ Monte Carlo mutation cases."
        ),
        "",
        "## Benchmark Scope",
        "",
        f"- semantic label: `{result['semantic_label']}`",
        f"- chunks: `{result['chunks']}`",
        f"- base queries: `{result['base_queries']}`",
        f"- MC seeds: `{result['mc_seeds']}`",
        f"- MC cases: `{result['mc_cases']}`",
        f"- baseline modes: `{len(result['baseline_modes'])}`",
        f"- fail_count: `{result['fail_count']}`",
        "",
        "## HSRAG Metrics",
        "",
        f"- target_correct: `{hsrag['target_correct']}`",
        f"- wrong_collision: `{hsrag['wrong_collision']}`",
        f"- no_evidence_false_allow: `{hsrag['no_evidence_false_allow']}`",
        f"- ambiguous_false_allow: `{hsrag['ambiguous_false_allow']}`",
        f"- mismatch_escape: `{hsrag['mismatch_escape']}`",
        f"- audit_chain_complete: `{hsrag['audit_chain_complete']}`",
        f"- p95_latency_ms: `{hsrag['p95_latency_ms']}`",
        "",
        "## Best Baseline Comparison",
        "",
        f"- target_correct: `{best['target_correct']}`",
        f"- wrong_collision: `{best['wrong_collision']}`",
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
        "| mode | target_correct | wrong_collision | p95_latency_ms |",
        "|---|---:|---:|---:|",
    ]

    for row in baseline_rows:
        lines.append(
            f"| {row.mode} | {row.target_correct} | "
            f"{row.wrong_collision} | {row.p95_latency_ms} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This verifier checks the frozen RQ2.2 benchmark summary.",
            "- It does not re-run the full original MC benchmark package.",
            "- RQ2.2 uses real uploaded EU legal PDFs with official references.",
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
    result = RQ2_2_FROZEN_RESULT
    hsrag = result["hsrag_metrics"]
    best = result["best_baseline_metrics"]

    print("=" * 80)
    print("HSRAG LAW — RQ2.2 VERIFICATION")
    print("=" * 80)
    print(f"core_decision: {core_decision}")
    print(f"audit_chain_complete: {1.0 if audit_chain_complete else 0.0}")
    print("")
    print("Scope:")
    print(f"  decision: {result['decision']}")
    print(f"  semantic_label: {result['semantic_label']}")
    print(f"  chunks: {result['chunks']}")
    print(f"  base_queries: {result['base_queries']}")
    print(f"  mc_seeds: {result['mc_seeds']}")
    print(f"  mc_cases: {result['mc_cases']}")
    print(f"  baseline_modes: {len(result['baseline_modes'])}")
    print(f"  fail_count: {result['fail_count']}")
    print("")
    print("HSRAG:")
    print(f"  target_correct: {hsrag['target_correct']}")
    print(f"  wrong_collision: {hsrag['wrong_collision']}")
    print(f"  no_evidence_false_allow: {hsrag['no_evidence_false_allow']}")
    print(f"  ambiguous_false_allow: {hsrag['ambiguous_false_allow']}")
    print(f"  mismatch_escape: {hsrag['mismatch_escape']}")
    print(f"  audit_chain_complete: {hsrag['audit_chain_complete']}")
    print(f"  p95_latency_ms: {hsrag['p95_latency_ms']}")
    print("")
    print("Best baseline:")
    print(f"  target_correct: {best['target_correct']}")
    print(f"  wrong_collision: {best['wrong_collision']}")
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

    checks = build_rq2_2_gate_checks(RQ2_2_FROZEN_RESULT)
    core_decision, failures = summarize_gate_checks(checks)

    baseline_rows = build_baseline_rows(RQ2_2_FROZEN_RESULT)

    # First build a provisional consistency row, then audit it.
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
        "name": "HSRAG-LAW-RQ2.2-Verifier",
        "core_decision": core_decision,
        "failures": list(failures),
        "rq2_2_frozen_result": RQ2_2_FROZEN_RESULT,
        "gate_checks": [asdict(check) for check in checks],
        "baseline_comparison": [asdict(row) for row in baseline_rows],
        "audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
        "consistency_matrix": consistency_matrix,
        "outputs": {
            "summary_json": "rq2_2_verification_summary.json",
            "summary_md": "rq2_2_verification_summary.md",
            "gate_checks_csv": "rq2_2_gate_checks.csv",
            "baseline_comparison_csv": "rq2_2_baseline_comparison.csv",
            "audit_chain_jsonl": "rq2_2_audit_chain.jsonl",
            "consistency_matrix_csv": "rq2_2_consistency_matrix.csv",
        },
    }

    write_json(RESULTS_DIR / "rq2_2_verification_summary.json", summary_payload)
    write_dataclass_csv(RESULTS_DIR / "rq2_2_gate_checks.csv", checks)
    write_dataclass_csv(RESULTS_DIR / "rq2_2_baseline_comparison.csv", baseline_rows)
    write_audit_chain(RESULTS_DIR / "rq2_2_audit_chain.jsonl", audit_chain)
    write_dict_csv(RESULTS_DIR / "rq2_2_consistency_matrix.csv", consistency_matrix)
    write_markdown_summary(
        RESULTS_DIR / "rq2_2_verification_summary.md",
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

    if core_decision != "RQ2_2_VERIFICATION_PASS":
        return 1

    if not audit_chain_complete:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())