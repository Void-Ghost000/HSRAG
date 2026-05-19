from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    start = time.perf_counter()

    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )

    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_ms": elapsed_ms,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "passed": completed.returncode == 0,
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "details": details or {},
    }


def build_acceptance_gates(
    pytest_result: dict[str, Any],
    demo_report: dict[str, Any] | None,
    benchmark_report: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []

    gates.append(
        gate(
            "pytest_passed",
            pytest_result["passed"],
            {
                "returncode": pytest_result["returncode"],
                "elapsed_ms": pytest_result["elapsed_ms"],
            },
        )
    )

    if demo_report is None:
        gates.append(gate("demo_report_generated", False))
    else:
        gates.append(gate("demo_report_generated", True))
        gates.append(
            gate(
                "demo_scope_local_only_zero_secret_zero_network",
                demo_report["scope"]["local_only"] is True
                and demo_report["scope"]["zero_secret"] is True
                and demo_report["scope"]["zero_network"] is True,
                demo_report["scope"],
            )
        )
        gates.append(
            gate(
                "demo_ingest_and_revision_passed",
                demo_report["steps"]["first_ingest"]["status"] == "ok"
                and demo_report["steps"]["second_ingest_revision"]["reason_code"]
                == "NEW_SPEC_REVISION_CREATED",
            )
        )
        gates.append(
            gate(
                "demo_pointer_lookup_passed",
                demo_report["steps"]["query_by_cthc_hash"]["status"] == "found"
                and demo_report["steps"]["query_by_cthc_hash"]["reason_code"]
                == "CANONICAL_SPEC_FOUND_BY_CTHC_HASH",
            )
        )
        gates.append(
            gate(
                "demo_semantic_discovery_is_candidates_only",
                demo_report["steps"]["semantic_discovery"]["status"] == "found_with_warning"
                and demo_report["steps"]["semantic_discovery"]["reason_code"]
                == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION",
            )
        )

    if benchmark_report is None:
        gates.append(gate("benchmark_report_generated", False))
    else:
        gates.append(gate("benchmark_report_generated", True))
        gates.append(
            gate(
                "benchmark_scope_local_only_zero_secret_zero_network",
                benchmark_report["scope"]["local_only"] is True
                and benchmark_report["scope"]["zero_secret"] is True
                and benchmark_report["scope"]["zero_network"] is True,
                benchmark_report["scope"],
            )
        )
        gates.append(
            gate(
                "benchmark_no_external_cost_or_key",
                benchmark_report["cost_profile"]["api_key_required"] is False
                and benchmark_report["cost_profile"]["network_calls"] == 0
                and benchmark_report["cost_profile"]["llm_calls_required"] == 0
                and benchmark_report["cost_profile"]["tokens_sent_to_llm"] == 0,
                benchmark_report["cost_profile"],
            )
        )
        gates.append(
            gate(
                "benchmark_p99_reported",
                "p99_ms" in benchmark_report["results"]["cthc_hash_lookup"]
                and "p99_ms" in benchmark_report["results"]["method_path_lookup"]
                and "p99_ms" in benchmark_report["results"]["semantic_discovery_like_lookup"],
            )
        )

    return gates


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser(
        description="One-command local verifier for HSRAG API SQLite demo."
    )
    parser.add_argument("--benchmark-runs", type=int, default=1000)
    parser.add_argument("--benchmark-dataset-size", type=int, default=100)
    parser.add_argument(
        "--report",
        type=Path,
        default=project_root / "data" / "verify_report.json",
    )
    args = parser.parse_args()

    verify_started_at = utc_now_z()

    demo_report_path = project_root / "data" / "verify_demo_report.json"
    demo_db_path = project_root / "data" / "verify_demo_api_specs.sqlite3"
    benchmark_report_path = project_root / "data" / "verify_benchmark_report.json"

    commands: list[dict[str, Any]] = []

    pytest_result = run_command(
        [sys.executable, "-m", "pytest"],
        cwd=project_root,
    )
    commands.append({"name": "pytest", **pytest_result})

    demo_result = run_command(
        [
            sys.executable,
            str(project_root / "src" / "hsrag_api_sqlite" / "demo.py"),
            "--db",
            str(demo_db_path),
            "--report",
            str(demo_report_path),
        ],
        cwd=project_root,
    )
    commands.append({"name": "demo", **demo_result})

    benchmark_result = run_command(
        [
            sys.executable,
            str(project_root / "scripts" / "benchmark_local_lookup.py"),
            "--runs",
            str(args.benchmark_runs),
            "--dataset-size",
            str(args.benchmark_dataset_size),
            "--output",
            str(benchmark_report_path),
        ],
        cwd=project_root,
    )
    commands.append({"name": "benchmark", **benchmark_result})

    demo_report = read_json(demo_report_path) if demo_report_path.exists() else None
    benchmark_report = (
        read_json(benchmark_report_path) if benchmark_report_path.exists() else None
    )

    acceptance_gates = build_acceptance_gates(
        pytest_result=pytest_result,
        demo_report=demo_report,
        benchmark_report=benchmark_report,
    )

    passed = all(item["passed"] for item in acceptance_gates)

    verify_report = {
        "verify_name": "hsrag_api_sqlite_local_verify_v0_1",
        "generated_at_utc": utc_now_z(),
        "verify_started_at_utc": verify_started_at,
        "status": "passed" if passed else "failed",
        "scope": {
            "local_only": True,
            "zero_secret": True,
            "zero_network": True,
            "note": "This verifier runs local pytest, demo, and SQLite benchmark only.",
        },
        "commands": commands,
        "acceptance_gates": acceptance_gates,
        "artifacts": {
            "verify_report": str(args.report),
            "demo_report": str(demo_report_path),
            "demo_db": str(demo_db_path),
            "benchmark_report": str(benchmark_report_path),
        },
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(verify_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(verify_report, indent=2, ensure_ascii=False))
    print("")
    print(f"Verify report written to: {args.report}")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
