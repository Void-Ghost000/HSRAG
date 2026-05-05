"""
HSRAG LAW — Run All Verifiers
=============================

This script runs the public HSRAG LAW verifier set:

- RQ1: Publication-grade real corpus gate
- RQ2.2: Real EU Law + four baselines + 10k MC verifier
- RQ3 FIX2: EU × US real-law collision verifier

It produces a unified verification index for reviewers.

QSVCS annotations:
- CTHC: classify verification outputs by RQ / corpus / benchmark role.
- QOIM: enforce verifier exit-code and acceptance-gate feasibility.
- SGF: execute verifiers in fixed forward-only order.
- VPSM: represent each RQ as a structured verification vector.
- Audit-S: write an append-only hash chain over the unified index.

Run from repository root:

    python examples/hsrag_law/scripts/run_all_verifiers.py

Optional:

    python examples/hsrag_law/scripts/run_all_verifiers.py --rq1-fetch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


# =============================================================================
# Path resolution
# =============================================================================

THIS_FILE = Path(__file__).resolve()

if THIS_FILE.parent.name == "scripts":
    EXAMPLE_ROOT = THIS_FILE.parent.parent
    SCRIPTS_DIR = THIS_FILE.parent
else:
    EXAMPLE_ROOT = THIS_FILE.parent
    SCRIPTS_DIR = EXAMPLE_ROOT / "scripts"

REPO_ROOT = EXAMPLE_ROOT.parents[1] if len(EXAMPLE_ROOT.parents) >= 2 else EXAMPLE_ROOT
RESULTS_DIR = EXAMPLE_ROOT / "results"


# =============================================================================
# Data models
# =============================================================================

@dataclass
class VerifierSpec:
    rq_id: str
    title: str
    script_name: str
    summary_json_name: str
    default_args: List[str]


@dataclass
class VerifierRun:
    rq_id: str
    title: str
    script_path: str
    command: List[str]
    return_code: int
    elapsed_ms: float
    stdout: str
    stderr: str
    summary_json_path: str
    summary_loaded: bool
    core_decision: Optional[str]
    audit_chain_complete: Optional[float]
    key_metrics: Dict[str, Any]


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


# =============================================================================
# Static verifier specs
# =============================================================================

def build_verifier_specs(rq1_fetch: bool) -> List[VerifierSpec]:
    rq1_args = [] if rq1_fetch else ["--skip-fetch"]

    return [
        VerifierSpec(
            rq_id="RQ1",
            title="Publication-grade real corpus gate",
            script_name="verify_rq1.py",
            summary_json_name="rq1_verification_summary.json",
            default_args=rq1_args,
        ),
        VerifierSpec(
            rq_id="RQ2.2",
            title="Real EU Law + four baselines + 10k MC",
            script_name="verify_rq2_2.py",
            summary_json_name="rq2_2_verification_summary.json",
            default_args=[],
        ),
        VerifierSpec(
            rq_id="RQ3_FIX2",
            title="EU × US real-law collision benchmark",
            script_name="verify_rq3_fix2.py",
            summary_json_name="rq3_fix2_verification_summary.json",
            default_args=[],
        ),
    ]


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


def load_json_if_exists(path: Path) -> Tuple[bool, Optional[Dict[str, Any]]]:
    if not path.exists():
        return False, None

    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, None


def safe_get(payload: Optional[Dict[str, Any]], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


# =============================================================================
# QOIM: Extract normalized verifier vectors
# =============================================================================

def extract_key_metrics(rq_id: str, summary: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[float], Dict[str, Any]]:
    if not summary:
        return None, None, {}

    if rq_id == "RQ1":
        core_decision = summary.get("core_decision")
        audit_chain_complete = summary.get("audit_chain_complete")
        frozen = summary.get("rq1_frozen_result", {})
        mc_scope = summary.get("mc_scope", {})
        fetch_summary = summary.get("fetch_summary", {})

        key_metrics = {
            "decision": frozen.get("decision"),
            "real_primary_corpus_rate": frozen.get("real_primary_corpus_rate"),
            "real_primary_chunk_rate": frozen.get("real_primary_chunk_rate"),
            "source_hash_final_present_rate": frozen.get("source_hash_final_present_rate"),
            "primary_real_rows": frozen.get("primary_real_rows"),
            "primary_real_target_correct_rate": frozen.get("primary_real_target_correct_rate"),
            "primary_real_wrong_collision_rate": frozen.get("primary_real_wrong_collision_rate"),
            "fail_count": frozen.get("fail_count"),
            "warn_count": frozen.get("warn_count"),
            "mc_scope_decision": mc_scope.get("decision"),
            "url_fetch_decision": fetch_summary.get("decision"),
        }
        return core_decision, audit_chain_complete, key_metrics

    if rq_id == "RQ2.2":
        core_decision = summary.get("core_decision")
        audit_chain_complete = summary.get("audit_chain_complete")
        frozen = summary.get("rq2_2_frozen_result", {})
        hsrag = frozen.get("hsrag_metrics", {})
        best = frozen.get("best_baseline_metrics", {})

        key_metrics = {
            "decision": frozen.get("decision"),
            "chunks": frozen.get("chunks"),
            "base_queries": frozen.get("base_queries"),
            "mc_cases": frozen.get("mc_cases"),
            "baseline_modes": len(frozen.get("baseline_modes", [])),
            "hsrag_target_correct": hsrag.get("target_correct"),
            "hsrag_wrong_collision": hsrag.get("wrong_collision"),
            "hsrag_no_evidence_false_allow": hsrag.get("no_evidence_false_allow"),
            "hsrag_ambiguous_false_allow": hsrag.get("ambiguous_false_allow"),
            "hsrag_mismatch_escape": hsrag.get("mismatch_escape"),
            "hsrag_p95_latency_ms": hsrag.get("p95_latency_ms"),
            "best_baseline_target_correct": best.get("target_correct"),
            "best_baseline_wrong_collision": best.get("wrong_collision"),
            "token_reduction_pct_max": best.get("token_reduction_pct_max"),
            "cost_reduction_pct_max": best.get("cost_reduction_pct_max"),
        }
        return core_decision, audit_chain_complete, key_metrics

    if rq_id == "RQ3_FIX2":
        core_decision = summary.get("core_decision")
        audit_chain_complete = summary.get("audit_chain_complete")
        frozen = summary.get("rq3_fix2_frozen_result", {})
        hsrag = frozen.get("hsrag_metrics", {})
        best = frozen.get("best_baseline_metrics", {})

        key_metrics = {
            "decision": frozen.get("decision"),
            "chunks": frozen.get("chunks"),
            "base_queries": frozen.get("base_queries"),
            "mc_cases": frozen.get("mc_cases"),
            "corpora": len(frozen.get("corpora", [])),
            "jurisdictions": len(frozen.get("jurisdictions", [])),
            "baseline_modes": len(frozen.get("baseline_modes", [])),
            "raw_fix1_wrong_jurisdiction_escape": frozen.get("raw_fix1_hsrag_wrong_jurisdiction_escape"),
            "fix2_normalized_wrong_jurisdiction_escape": frozen.get("fix2_normalized_hsrag_wrong_jurisdiction_escape"),
            "hsrag_target_correct": hsrag.get("target_correct"),
            "hsrag_wrong_corpus_collision": hsrag.get("wrong_corpus_collision"),
            "hsrag_wrong_jurisdiction_escape": hsrag.get("wrong_jurisdiction_escape"),
            "hsrag_no_evidence_false_allow": hsrag.get("no_evidence_false_allow"),
            "hsrag_ambiguous_false_allow": hsrag.get("ambiguous_false_allow"),
            "hsrag_mismatch_escape": hsrag.get("mismatch_escape"),
            "hsrag_p95_latency_ms": hsrag.get("p95_latency_ms"),
            "best_baseline_target_correct": best.get("target_correct"),
            "best_baseline_wrong_corpus_collision": best.get("wrong_corpus_collision"),
            "best_baseline_wrong_jurisdiction_escape": best.get("wrong_jurisdiction_escape"),
            "token_reduction_pct_max": best.get("token_reduction_pct_max"),
            "cost_reduction_pct_max": best.get("cost_reduction_pct_max"),
        }
        return core_decision, audit_chain_complete, key_metrics

    return None, None, {}


# =============================================================================
# SGF: Forward-only execution
# =============================================================================

def run_verifier(spec: VerifierSpec) -> VerifierRun:
    script_path = SCRIPTS_DIR / spec.script_name
    command = [sys.executable, str(script_path), *spec.default_args]

    started = time.perf_counter()

    if not script_path.exists():
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return VerifierRun(
            rq_id=spec.rq_id,
            title=spec.title,
            script_path=str(script_path),
            command=command,
            return_code=127,
            elapsed_ms=elapsed_ms,
            stdout="",
            stderr=f"Script not found: {script_path}",
            summary_json_path=str(RESULTS_DIR / spec.summary_json_name),
            summary_loaded=False,
            core_decision=None,
            audit_chain_complete=None,
            key_metrics={},
        )

    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    elapsed_ms = (time.perf_counter() - started) * 1000.0

    summary_path = RESULTS_DIR / spec.summary_json_name
    summary_loaded, summary_payload = load_json_if_exists(summary_path)
    core_decision, audit_chain_complete, key_metrics = extract_key_metrics(
        spec.rq_id,
        summary_payload,
    )

    return VerifierRun(
        rq_id=spec.rq_id,
        title=spec.title,
        script_path=str(script_path),
        command=command,
        return_code=completed.returncode,
        elapsed_ms=elapsed_ms,
        stdout=completed.stdout,
        stderr=completed.stderr,
        summary_json_path=str(summary_path),
        summary_loaded=summary_loaded,
        core_decision=core_decision,
        audit_chain_complete=audit_chain_complete,
        key_metrics=key_metrics,
    )


# =============================================================================
# Audit-S: unified audit chain
# =============================================================================

def build_unified_audit_chain(runs: Sequence[VerifierRun], final_decision: str) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous_hash = "GENESIS"

    payloads: List[Tuple[str, Dict[str, Any]]] = [
        (
            "RUN_ALL_VERIFIERS_START",
            {
                "repo_root": str(REPO_ROOT),
                "example_root": str(EXAMPLE_ROOT),
                "results_dir": str(RESULTS_DIR),
            },
        )
    ]

    for run in runs:
        payloads.append(
            (
                f"{run.rq_id}_RUN_RESULT",
                {
                    "rq_id": run.rq_id,
                    "title": run.title,
                    "script_path": run.script_path,
                    "command": run.command,
                    "return_code": run.return_code,
                    "elapsed_ms": run.elapsed_ms,
                    "summary_loaded": run.summary_loaded,
                    "core_decision": run.core_decision,
                    "audit_chain_complete": run.audit_chain_complete,
                    "key_metrics": run.key_metrics,
                },
            )
        )

    payloads.append(
        (
            "RUN_ALL_VERIFIERS_FINAL_DECISION",
            {
                "final_decision": final_decision,
                "rq_count": len(runs),
                "passed_count": sum(1 for run in runs if run.return_code == 0),
            },
        )
    )

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

        if stable_json_hash(recompute_payload) != event.event_hash:
            return False

        expected_previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


# =============================================================================
# Final decision
# =============================================================================

def compute_final_decision(runs: Sequence[VerifierRun]) -> Tuple[str, List[str]]:
    failures: List[str] = []

    expected_core_decisions = {
        "RQ1": "RQ1_VERIFICATION_PASS",
        "RQ2.2": "RQ2_2_VERIFICATION_PASS",
        "RQ3_FIX2": "RQ3_FIX2_VERIFICATION_PASS",
    }

    for run in runs:
        if run.return_code != 0:
            failures.append(f"{run.rq_id}: return_code={run.return_code}")

        expected_decision = expected_core_decisions.get(run.rq_id)
        if expected_decision and run.core_decision != expected_decision:
            failures.append(
                f"{run.rq_id}: expected core_decision={expected_decision}, actual={run.core_decision}"
            )

        if run.audit_chain_complete != 1.0:
            failures.append(
                f"{run.rq_id}: audit_chain_complete must equal 1.0, actual={run.audit_chain_complete}"
            )

        if not run.summary_loaded:
            failures.append(f"{run.rq_id}: summary JSON was not loaded.")

    if failures:
        return "HSRAG_LAW_VERIFICATION_INDEX_FAIL", failures

    return "HSRAG_LAW_VERIFICATION_INDEX_PASS", []


# =============================================================================
# Output writers
# =============================================================================

def build_index_payload(
    runs: Sequence[VerifierRun],
    final_decision: str,
    failures: Sequence[str],
    unified_audit_chain_complete: bool,
) -> Dict[str, Any]:
    return {
        "name": "HSRAG-LAW-Unified-Verification-Index",
        "final_decision": final_decision,
        "failures": list(failures),
        "rq_count": len(runs),
        "unified_audit_chain_complete": 1.0 if unified_audit_chain_complete else 0.0,
        "runs": [
            {
                "rq_id": run.rq_id,
                "title": run.title,
                "return_code": run.return_code,
                "elapsed_ms": run.elapsed_ms,
                "summary_loaded": run.summary_loaded,
                "core_decision": run.core_decision,
                "audit_chain_complete": run.audit_chain_complete,
                "summary_json_path": run.summary_json_path,
                "key_metrics": run.key_metrics,
            }
            for run in runs
        ],
        "outputs": {
            "index_json": "hsrag_law_verification_index.json",
            "index_md": "hsrag_law_verification_index.md",
            "audit_chain_jsonl": "hsrag_law_verification_audit_chain.jsonl",
            "terminal_output_txt": "hsrag_law_verification_terminal_output.txt",
        },
    }


def write_terminal_output(path: Path, runs: Sequence[VerifierRun]) -> None:
    sections: List[str] = []

    for run in runs:
        sections.append("=" * 80)
        sections.append(f"{run.rq_id} — {run.title}")
        sections.append("=" * 80)
        sections.append("$ " + " ".join(run.command))
        sections.append("")
        sections.append("[STDOUT]")
        sections.append(run.stdout.strip())
        sections.append("")
        sections.append("[STDERR]")
        sections.append(run.stderr.strip())
        sections.append("")
        sections.append(f"return_code: {run.return_code}")
        sections.append(f"elapsed_ms: {run.elapsed_ms:.3f}")
        sections.append("")

    path.write_text("\n".join(sections) + "\n", encoding="utf-8")


def write_markdown_index(
    path: Path,
    runs: Sequence[VerifierRun],
    final_decision: str,
    failures: Sequence[str],
    unified_audit_chain_complete: bool,
) -> None:
    lines = [
        "# HSRAG LAW Unified Verification Index",
        "",
        f"Final decision: `{final_decision}`",
        f"Unified audit chain complete: `{1.0 if unified_audit_chain_complete else 0.0}`",
        "",
        "## Included Verifiers",
        "",
        "| RQ | Role | Core decision | Audit chain | Return code |",
        "|---|---|---|---:|---:|",
    ]

    for run in runs:
        lines.append(
            f"| {run.rq_id} | {run.title} | `{run.core_decision}` | "
            f"`{run.audit_chain_complete}` | `{run.return_code}` |"
        )

    lines.extend(
        [
            "",
            "## Key Metrics",
            "",
        ]
    )

    for run in runs:
        lines.append(f"### {run.rq_id} — {run.title}")
        lines.append("")
        if not run.key_metrics:
            lines.append("- No key metrics loaded.")
        else:
            for key, value in run.key_metrics.items():
                lines.append(f"- {key}: `{value}`")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- This index runs the public frozen-result verifiers for RQ1, RQ2.2, and RQ3 FIX2.",
            "- It does not re-run the full original MC benchmark packages.",
            "- RQ1 URL fetch is skipped by default for deterministic verification.",
            "- Official-source rebuilding is planned as a separate RQ4 pipeline.",
            "- MC mutation reproduction is planned as a separate RQ5 pipeline.",
        ]
    )

    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    runs: Sequence[VerifierRun],
    final_decision: str,
    failures: Sequence[str],
    unified_audit_chain_complete: bool,
) -> None:
    print("=" * 80)
    print("HSRAG LAW — UNIFIED VERIFICATION INDEX")
    print("=" * 80)
    print(f"final_decision: {final_decision}")
    print(f"unified_audit_chain_complete: {1.0 if unified_audit_chain_complete else 0.0}")
    print("")

    for run in runs:
        print(f"{run.rq_id}:")
        print(f"  title: {run.title}")
        print(f"  return_code: {run.return_code}")
        print(f"  core_decision: {run.core_decision}")
        print(f"  audit_chain_complete: {run.audit_chain_complete}")
        print(f"  summary_loaded: {run.summary_loaded}")
        print(f"  elapsed_ms: {run.elapsed_ms:.3f}")
        print("")

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
        print("")

    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 80)


# =============================================================================
# CLI / main
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all HSRAG LAW public verifiers."
    )
    parser.add_argument(
        "--rq1-fetch",
        action="store_true",
        help="Run RQ1 URL fetch smoke instead of default --skip-fetch.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    ensure_dirs()

    specs = build_verifier_specs(rq1_fetch=args.rq1_fetch)
    runs = [run_verifier(spec) for spec in specs]

    final_decision, failures = compute_final_decision(runs)

    audit_chain = build_unified_audit_chain(runs, final_decision)
    unified_audit_chain_complete = verify_audit_chain(audit_chain)

    if not unified_audit_chain_complete:
        final_decision = "HSRAG_LAW_VERIFICATION_INDEX_FAIL"
        failures = list(failures) + ["Unified audit chain verification failed."]

    index_payload = build_index_payload(
        runs=runs,
        final_decision=final_decision,
        failures=failures,
        unified_audit_chain_complete=unified_audit_chain_complete,
    )

    write_json(RESULTS_DIR / "hsrag_law_verification_index.json", index_payload)
    write_markdown_index(
        RESULTS_DIR / "hsrag_law_verification_index.md",
        runs=runs,
        final_decision=final_decision,
        failures=failures,
        unified_audit_chain_complete=unified_audit_chain_complete,
    )
    write_audit_chain(
        RESULTS_DIR / "hsrag_law_verification_audit_chain.jsonl",
        audit_chain,
    )
    write_terminal_output(
        RESULTS_DIR / "hsrag_law_verification_terminal_output.txt",
        runs,
    )

    print_summary(
        runs=runs,
        final_decision=final_decision,
        failures=failures,
        unified_audit_chain_complete=unified_audit_chain_complete,
    )

    return 0 if final_decision == "HSRAG_LAW_VERIFICATION_INDEX_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())