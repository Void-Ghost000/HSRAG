from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCK_EXPECTED_CLASSES = {"no_evidence", "ambiguous_cross_domain", "mismatch_trap"}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def classify_row(row: dict[str, Any]) -> str:
    query_class = str(row.get("query_class", "UNKNOWN"))
    status = str(row.get("status", "UNKNOWN"))
    target = row.get("target")
    result = row.get("result")

    if query_class in BLOCK_EXPECTED_CLASSES and status == "BLOCK":
        return "EXPECTED_GUARD_BLOCK"

    if query_class in BLOCK_EXPECTED_CLASSES and status == "ALLOW":
        return "FALSE_ALLOW_RISK"

    if target and status == "BLOCK":
        return "TARGET_BLOCKED"

    if target and status == "ALLOW" and result:
        if (
            str(target.get("corpus")) == str(result.get("corpus"))
            and str(target.get("unit")) == str(result.get("unit"))
        ):
            return "ALLOW_MATCHED_TARGET"
        return "TARGET_MISMATCH"

    if not target and status == "ALLOW":
        return "ALLOW_NO_TARGET"

    return "OTHER"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.full_queries.json")
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent

    diagnostics = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "analyze_rq7_full_query_diagnostics.py"),
            "--config",
            str(config_path),
        ]
    )

    raw_results_path = Path(diagnostics["runner"]["raw_results"])
    if not raw_results_path.exists():
        raise SystemExit(f"RAW_RESULTS_NOT_FOUND:{raw_results_path}")

    rows = read_jsonl(raw_results_path)

    triage_counter = Counter()
    reason_by_triage: dict[str, Counter] = {}
    examples: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        triage = classify_row(row)
        reason = str(row.get("reason_code", "UNKNOWN"))

        triage_counter[triage] += 1
        reason_by_triage.setdefault(triage, Counter())[reason] += 1

        examples.setdefault(triage, [])
        if len(examples[triage]) < 5:
            examples[triage].append(
                {
                    "mode": row.get("mode"),
                    "query_class": row.get("query_class"),
                    "status": row.get("status"),
                    "reason_code": row.get("reason_code"),
                    "query_id": row.get("query_id") or row.get("case_id") or row.get("id"),
                    "target": row.get("target"),
                    "result": row.get("result"),
                }
            )

    published_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    summary = {
        "schema": "HSRAG_RQ7_FULL_QUERY_TRIAGE_V0_1",
        "status": "OK",
        "published_at_utc": published_at_utc,
        "diagnostic_id": diagnostics.get("diagnostic_id"),
        "diagnostic_status": diagnostics.get("diagnostic_status"),
        "acceptance_passed": diagnostics.get("acceptance_passed"),
        "raw_result_count": len(rows),
        "triage_summary": dict(sorted(triage_counter.items())),
        "reason_by_triage": {
            key: dict(counter)
            for key, counter in sorted(reason_by_triage.items())
        },
        "examples": examples,
        "claim_boundary": {
            "triage_only": True,
            "acceptance_failure_allowed_for_diagnostics": True,
            "full_query_expansion": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "RQ7_FULL_QUERY_TRIAGE.json"
    output_md = output_dir / "RQ7_FULL_QUERY_TRIAGE.md"

    write_json(output_json, summary)

    lines = [
        "# RQ7 Full Query Triage",
        "",
        f"- status: {summary['status']}",
        f"- diagnostic_status: {summary['diagnostic_status']}",
        f"- acceptance_passed: {summary['acceptance_passed']}",
        f"- raw_result_count: {summary['raw_result_count']}",
        "",
        "## Triage Summary",
        "",
    ]

    for key, count in summary["triage_summary"].items():
        lines.append(f"- {key}: {count}")

    lines.extend(["", "## Reason by Triage", ""])

    for triage, counter in summary["reason_by_triage"].items():
        lines.append(f"### {triage}")
        for reason, count in counter.items():
            lines.append(f"- {reason}: {count}")
        lines.append("")

    lines.extend(
        [
            "## Claim Boundary",
            "",
            "- triage_only: true",
            "- acceptance_failure_allowed_for_diagnostics: true",
            "- full_query_expansion: true",
            "- full_scale_benchmark: false",
            "- vector_hybrid_baselines: false",
            "- legal_advice: false",
            "",
        ]
    )

    output_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
