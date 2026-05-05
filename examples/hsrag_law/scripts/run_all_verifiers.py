"""
HSRAG LAW — Unified Verification Index Runner
=============================================

Runs the HSRAG LAW verification chain:

- RQ1      Publication-grade real corpus gate
- RQ2.2    Real EU law + four baselines + 10k MC
- RQ3_FIX2 EU × US real-law collision benchmark
- RQ4.1    Official/public source fetch and rebuild
- RQ5.5    CTHC-typed salted-domain routing robustness

Outputs:

- unified_verification_index.json
- unified_verification_index.md
- unified_verification_audit_chain.jsonl
- unified_verification_terminal_output.txt

Design notes:
- This runner is an orchestration layer.
- It does not modify the individual verifier logic.
- It treats each verifier as an auditable subprocess.
- It records return code, parsed decision, elapsed time, and output hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


THIS_FILE = Path(__file__).resolve()
SCRIPTS_DIR = THIS_FILE.parent
EXAMPLE_ROOT = SCRIPTS_DIR.parent
REPO_ROOT = EXAMPLE_ROOT.parent.parent
RESULTS_DIR = EXAMPLE_ROOT / "results"


@dataclass
class VerificationStep:
    key: str
    title: str
    script: str
    args: List[str]


@dataclass
class StepResult:
    key: str
    title: str
    script: str
    args: List[str]
    command: List[str]
    return_code: int
    core_decision: str
    audit_chain_complete: float
    summary_loaded: bool
    elapsed_ms: float
    stdout_hash: str
    stderr_hash: str
    stdout_tail: str
    stderr_tail: str


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def tail_text(text: str, max_lines: int = 80) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def parse_decision(stdout: str, stderr: str) -> str:
    combined = stdout + "\n" + stderr

    patterns = [
        r"final_decision:\s*([A-Z0-9_\.]+)",
        r"core_decision:\s*([A-Z0-9_\.]+)",
        r"\bdecision:\s*([A-Z0-9_\.]+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, combined)
        if matches:
            return matches[-1]

    return "UNKNOWN"


def parse_audit_chain_complete(stdout: str, stderr: str) -> float:
    combined = stdout + "\n" + stderr

    values: List[float] = []
    patterns = [
        r"unified_audit_chain_complete:\s*([0-9.]+)",
        r"case_audit_chain_complete:\s*([0-9.]+)",
        r"summary_audit_chain_complete:\s*([0-9.]+)",
        r"audit_chain_complete:\s*([0-9.]+)",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, combined):
            try:
                values.append(float(match))
            except ValueError:
                pass

    if not values:
        return 0.0

    return min(values)


def likely_summary_loaded(step_key: str) -> bool:
    """
    Lightweight summary presence check.

    This runner does not require exact individual summary filenames.
    It only checks whether result JSON/MD files for the step appear to exist.
    """
    if not RESULTS_DIR.exists():
        return False

    key = step_key.lower().replace("_fix2", "").replace(".", "_")
    candidates = list(RESULTS_DIR.glob("*.json")) + list(RESULTS_DIR.glob("*.md"))

    if step_key == "RQ5.5":
        return (RESULTS_DIR / "rq5_mc_reproduction_summary.json").exists()

    if step_key == "RQ4.1":
        return (RESULTS_DIR / "rq4_source_rebuild_summary.json").exists()

    for path in candidates:
        name = path.name.lower()
        if key.replace(".", "_") in name:
            return True

    return False


def run_subprocess_stream(command: List[str], cwd: Path) -> tuple[int, str, str, float]:
    started = time.perf_counter()

    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    assert process.stdout is not None
    assert process.stderr is not None

    # Stream stdout first; most scripts print to stdout.
    for line in process.stdout:
        print(line, end="")
        stdout_lines.append(line)

    stderr = process.stderr.read()
    if stderr:
        print(stderr, end="", file=sys.stderr)
        stderr_lines.append(stderr)

    return_code = process.wait()
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    return return_code, "".join(stdout_lines), "".join(stderr_lines), elapsed_ms


def run_step(step: VerificationStep) -> StepResult:
    script_path = SCRIPTS_DIR / step.script

    command = [sys.executable, str(script_path), *step.args]

    print("")
    print("=" * 88)
    print(f"RUNNING {step.key} — {step.title}")
    print("=" * 88)
    print("command:", " ".join(command))
    print("")

    if not script_path.exists():
        stderr = f"Missing script: {script_path}"
        print(stderr, file=sys.stderr)
        return StepResult(
            key=step.key,
            title=step.title,
            script=step.script,
            args=step.args,
            command=command,
            return_code=127,
            core_decision="SCRIPT_MISSING",
            audit_chain_complete=0.0,
            summary_loaded=False,
            elapsed_ms=0.0,
            stdout_hash=text_hash(""),
            stderr_hash=text_hash(stderr),
            stdout_tail="",
            stderr_tail=stderr,
        )

    return_code, stdout, stderr, elapsed_ms = run_subprocess_stream(command, REPO_ROOT)

    decision = parse_decision(stdout, stderr)
    audit_complete = parse_audit_chain_complete(stdout, stderr)
    summary_loaded = likely_summary_loaded(step.key)

    return StepResult(
        key=step.key,
        title=step.title,
        script=step.script,
        args=step.args,
        command=command,
        return_code=return_code,
        core_decision=decision,
        audit_chain_complete=audit_complete,
        summary_loaded=summary_loaded,
        elapsed_ms=elapsed_ms,
        stdout_hash=text_hash(stdout),
        stderr_hash=text_hash(stderr),
        stdout_tail=tail_text(stdout),
        stderr_tail=tail_text(stderr),
    )


def build_steps(args: argparse.Namespace) -> List[VerificationStep]:
    return [
        VerificationStep(
            key="RQ1",
            title="Publication-grade real corpus gate",
            script="verify_rq1.py",
            args=[],
        ),
        VerificationStep(
            key="RQ2.2",
            title="Real EU law + four baselines + 10k MC",
            script="verify_rq2_2.py",
            args=[],
        ),
        VerificationStep(
            key="RQ3_FIX2",
            title="EU × US real-law collision benchmark",
            script="verify_rq3_fix2.py",
            args=[],
        ),
        VerificationStep(
            key="RQ4.1",
            title="Official/public source fetch and rebuild",
            script="verify_rq4_official_fetch.py",
            args=["--min-ok", str(args.rq4_min_ok)],
        ),
        VerificationStep(
            key="RQ5.5",
            title="CTHC-typed salted-domain routing robustness",
            script="verify_rq5_mc_reproduction.py",
            args=[
                "--cases",
                str(args.rq5_cases),
                "--seed",
                str(args.seed),
            ],
        ),
    ]


def summarize_final_decision(results: Sequence[StepResult]) -> tuple[str, List[str]]:
    failures: List[str] = []

    for result in results:
        if result.return_code != 0:
            failures.append(
                f"{result.key}: return_code={result.return_code}, decision={result.core_decision}"
            )

        if not result.core_decision.endswith("PASS"):
            failures.append(
                f"{result.key}: non-pass decision={result.core_decision}"
            )

        if result.audit_chain_complete < 1.0:
            failures.append(
                f"{result.key}: audit_chain_complete={result.audit_chain_complete}"
            )

    if failures:
        return "HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_FAIL", failures

    return "HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_PASS", []


def build_audit_chain(
    config: Dict[str, Any],
    results: Sequence[StepResult],
    final_decision: str,
    failures: Sequence[str],
) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous = "GENESIS"

    payloads: List[tuple[str, Dict[str, Any]]] = [
        ("UNIFIED_CONFIG", config),
    ]

    for result in results:
        payloads.append((f"STEP_{result.key}", asdict(result)))

    payloads.append(
        (
            "UNIFIED_FINAL_DECISION",
            {
                "final_decision": final_decision,
                "failures": list(failures),
            },
        )
    )

    for index, (event_type, payload) in enumerate(payloads):
        event_payload = {
            "index": index,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous,
        }
        event_hash = stable_json_hash(event_payload)
        events.append(AuditEvent(index, event_type, payload, previous, event_hash))
        previous = event_hash

    return events


def verify_audit_chain(events: Sequence[AuditEvent]) -> bool:
    previous = "GENESIS"

    for event in events:
        if event.previous_hash != previous:
            return False

        payload = {
            "index": event.index,
            "event_type": event.event_type,
            "payload": event.payload,
            "previous_hash": event.previous_hash,
        }

        if stable_json_hash(payload) != event.event_hash:
            return False

        previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), sort_keys=True, ensure_ascii=False) + "\n")


def write_markdown_index(
    path: Path,
    final_decision: str,
    failures: Sequence[str],
    config: Dict[str, Any],
    results: Sequence[StepResult],
    audit_ok: bool,
) -> None:
    lines: List[str] = [
        "# HSRAG LAW Unified Verification Index",
        "",
        f"Final decision: `{final_decision}`",
        f"Unified audit chain complete: `{1.0 if audit_ok else 0.0}`",
        "",
        "## Config",
        "",
    ]

    for key, value in config.items():
        lines.append(f"- {key}: `{value}`")

    lines += [
        "",
        "## Verification stages",
        "",
        "| Stage | Title | Return code | Decision | Audit chain | Elapsed ms | Summary loaded |",
        "|---|---|---:|---|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            f"| {result.key} | {result.title} | {result.return_code} | "
            f"`{result.core_decision}` | {result.audit_chain_complete} | "
            f"{result.elapsed_ms:.3f} | `{result.summary_loaded}` |"
        )

    if failures:
        lines += [
            "",
            "## Failures",
            "",
        ]
        for failure in failures:
            lines.append(f"- {failure}")

    lines += [
        "",
        "## Notes",
        "",
        "- This index is generated by `examples/hsrag_law/scripts/run_all_verifiers.py`.",
        "- Each verifier is executed as a subprocess.",
        "- The runner records return code, parsed decision, audit-chain completeness, output hashes, and elapsed time.",
        "- RQ5.5 uses CTHC-typed salted-domain routing.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def write_terminal_output(path: Path, results: Sequence[StepResult], final_decision: str, failures: Sequence[str]) -> None:
    lines: List[str] = []
    lines.append("=" * 88)
    lines.append("HSRAG LAW — UNIFIED VERIFICATION INDEX")
    lines.append("=" * 88)
    lines.append(f"final_decision: {final_decision}")
    lines.append("")

    for result in results:
        lines.append(f"{result.key}:")
        lines.append(f"  title: {result.title}")
        lines.append(f"  return_code: {result.return_code}")
        lines.append(f"  core_decision: {result.core_decision}")
        lines.append(f"  audit_chain_complete: {result.audit_chain_complete}")
        lines.append(f"  summary_loaded: {result.summary_loaded}")
        lines.append(f"  elapsed_ms: {result.elapsed_ms:.3f}")
        lines.append("")

    if failures:
        lines.append("Failures:")
        for failure in failures:
            lines.append(f"  - {failure}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full HSRAG LAW verification chain.")
    parser.add_argument("--rq5-cases", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--rq4-min-ok", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ensure_dirs()
    args = parse_args(argv)

    run_started_utc = datetime.now(timezone.utc).isoformat()

    config = {
        "name": "HSRAG-LAW-Unified-Verification-Index",
        "run_started_utc": run_started_utc,
        "repo_root": str(REPO_ROOT),
        "example_root": str(EXAMPLE_ROOT),
        "results_dir": str(RESULTS_DIR),
        "rq5_cases": args.rq5_cases,
        "seed": args.seed,
        "rq4_min_ok": args.rq4_min_ok,
        "python": sys.executable,
    }

    steps = build_steps(args)

    results: List[StepResult] = []
    for step in steps:
        results.append(run_step(step))

    final_decision, failures = summarize_final_decision(results)

    audit_chain = build_audit_chain(config, results, final_decision, failures)
    audit_ok = verify_audit_chain(audit_chain)

    if not audit_ok:
        final_decision = "HSRAG_LAW_UNIFIED_VERIFICATION_INDEX_FAIL"
        failures = list(failures) + ["Unified audit chain verification failed."]

    payload = {
        "name": "HSRAG-LAW-Unified-Verification-Index",
        "final_decision": final_decision,
        "unified_audit_chain_complete": 1.0 if audit_ok else 0.0,
        "failures": list(failures),
        "config": config,
        "steps": [asdict(result) for result in results],
        "outputs": {
            "json": "unified_verification_index.json",
            "markdown": "unified_verification_index.md",
            "audit_chain": "unified_verification_audit_chain.jsonl",
            "terminal_output": "unified_verification_terminal_output.txt",
        },
    }

    write_json_path = RESULTS_DIR / "unified_verification_index.json"
    write_md_path = RESULTS_DIR / "unified_verification_index.md"
    write_audit_path = RESULTS_DIR / "unified_verification_audit_chain.jsonl"
    write_terminal_path = RESULTS_DIR / "unified_verification_terminal_output.txt"

    write_json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown_index(write_md_path, final_decision, failures, config, results, audit_ok)
    write_audit_chain(write_audit_path, audit_chain)
    write_terminal_output(write_terminal_path, results, final_decision, failures)

    print("")
    print("=" * 88)
    print("HSRAG LAW — UNIFIED VERIFICATION INDEX")
    print("=" * 88)
    print(f"final_decision: {final_decision}")
    print(f"unified_audit_chain_complete: {1.0 if audit_ok else 0.0}")
    print("")
    for result in results:
        print(f"{result.key}:")
        print(f"  title: {result.title}")
        print(f"  return_code: {result.return_code}")
        print(f"  core_decision: {result.core_decision}")
        print(f"  audit_chain_complete: {result.audit_chain_complete}")
        print(f"  summary_loaded: {result.summary_loaded}")
        print(f"  elapsed_ms: {result.elapsed_ms:.3f}")
        print("")

    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
        print("")

    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 88)

    return 0 if final_decision.endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())