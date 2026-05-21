from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.full_queries.json")
    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent

    build_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "build_rq7_full_query_seed.py"),
        ]
    )

    runner_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7.py"),
            "--config",
            str(config_path),
        ]
    )

    raw_results_path = Path(runner_summary["raw_results"])
    gates_path = Path(runner_summary["acceptance_gates"])
    metrics_by_query_class_path = Path(runner_summary["metrics_by_query_class"])

    raw_rows = read_jsonl(raw_results_path)
    gates = load_json(gates_path)
    query_class_rows = read_csv_rows(metrics_by_query_class_path)

    by_query_class: dict[str, Counter] = defaultdict(Counter)
    by_mode: dict[str, Counter] = defaultdict(Counter)
    reason_codes = Counter()

    for row in raw_rows:
        query_class = str(row.get("query_class", "UNKNOWN"))
        mode = str(row.get("mode", "UNKNOWN"))
        status = str(row.get("status", "UNKNOWN"))
        reason_code = str(row.get("reason_code", "UNKNOWN"))

        by_query_class[query_class][status] += 1
        by_mode[mode][status] += 1
        reason_codes[reason_code] += 1

    query_class_summary = {
        query_class: dict(counter)
        for query_class, counter in sorted(by_query_class.items())
    }

    mode_summary = {
        mode: dict(counter)
        for mode, counter in sorted(by_mode.items())
    }

    diagnostic_status = "PASS" if runner_summary.get("passed") is True else "DIAGNOSTIC_WARN"

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    diagnostic_id = "rq7_full_query_diagnostics_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    diagnostic_dir = base_dir / "04_runs" / diagnostic_id
    diagnostic_dir.mkdir(parents=True, exist_ok=False)

    summary = {
        "schema": "HSRAG_RQ7_FULL_QUERY_DIAGNOSTICS_V0_1",
        "status": "OK",
        "diagnostic_status": diagnostic_status,
        "diagnostic_id": diagnostic_id,
        "run_started_at_utc": run_started_at_utc,
        "build_summary": build_summary,
        "runner": runner_summary,
        "acceptance_passed": gates.get("passed"),
        "gate_results": gates.get("gate_results", {}),
        "raw_result_count": len(raw_rows),
        "query_class_count": len(query_class_summary),
        "query_class_summary": query_class_summary,
        "mode_summary": mode_summary,
        "reason_code_summary": dict(reason_codes),
        "metrics_by_query_class_rows": len(query_class_rows),
        "claim_boundary": {
            "diagnostic_only": True,
            "full_query_expansion": True,
            "acceptance_failure_allowed_for_diagnostics": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
        },
    }

    summary_json = diagnostic_dir / "rq7_full_query_diagnostics.json"
    summary_md = diagnostic_dir / "rq7_full_query_diagnostics.md"

    write_json(summary_json, summary)

    lines = [
        "# RQ7 Full Query Diagnostics",
        "",
        f"- status: {summary['status']}",
        f"- diagnostic_status: {diagnostic_status}",
        f"- acceptance_passed: {summary['acceptance_passed']}",
        f"- raw_result_count: {summary['raw_result_count']}",
        f"- query_class_count: {summary['query_class_count']}",
        "",
        "## Query Class Summary",
        "",
    ]

    for query_class, counter in query_class_summary.items():
        lines.append(f"- {query_class}: {counter}")

    lines.extend(
        [
            "",
            "## Reason Code Summary",
            "",
        ]
    )

    for reason, count in sorted(reason_codes.items()):
        lines.append(f"- {reason}: {count}")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- diagnostic_only: true",
            "- full_query_expansion: true",
            "- acceptance_failure_allowed_for_diagnostics: true",
            "- full_scale_benchmark: false",
            "- vector_hybrid_baselines: false",
            "",
        ]
    )

    summary_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
