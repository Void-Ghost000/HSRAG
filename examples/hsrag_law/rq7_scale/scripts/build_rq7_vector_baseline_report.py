from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VECTOR_MODES = {"VECTOR_GLOBAL", "CTHC_PRUNED_VECTOR"}


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.vector.json")
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent
    generated_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    runner = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7.py"),
            "--config",
            str(config_path),
        ]
    )

    metrics_rows = read_csv_rows(Path(runner["metrics_summary"]))
    query_class_rows = read_csv_rows(Path(runner["metrics_by_query_class"]))

    vector_metric_rows = [
        row for row in metrics_rows
        if row.get("mode") in VECTOR_MODES
    ]

    vector_query_class_rows = [
        row for row in query_class_rows
        if row.get("mode") in VECTOR_MODES
    ]

    found_modes = sorted({row["mode"] for row in vector_metric_rows})

    passed = (
        runner.get("status") == "OK"
        and VECTOR_MODES.issubset(set(found_modes))
        and len(vector_query_class_rows) > 0
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    report_md = output_dir / "RQ7_VECTOR_BASELINE_REPORT.md"
    report_json = output_dir / "RQ7_VECTOR_BASELINE_REPORT_SUMMARY.json"
    report_csv = output_dir / "RQ7_VECTOR_BASELINE_REPORT.csv"

    csv_rows = []
    for row in vector_metric_rows:
        csv_rows.append(
            {
                "mode": row["mode"],
                "corpus_size": row["corpus_size"],
                "target_correct_rate": row["target_correct_rate"],
                "candidate_reduction_ratio": row["candidate_reduction_ratio"],
                "latency_p99_ms": row["latency_p99_ms"],
                "actual_elapsed_p99_ms": row.get("actual_elapsed_p99_ms", "0.0"),
                "estimated_token_cost_usd_per_1k_queries": row["estimated_token_cost_usd_per_1k_queries"],
                "esi_mean": row["esi_mean"],
                "returned_domain_salt_valid_rate": row.get("returned_domain_salt_valid_rate", "0.0"),
            }
        )

    write_csv(report_csv, csv_rows)

    summary = {
        "schema": "HSRAG_RQ7_VECTOR_BASELINE_REPORT_V0_1",
        "status": "OK" if passed else "FAILED",
        "generated_at_utc": generated_at_utc,
        "runner_status": runner.get("status"),
        "runner_passed": runner.get("passed"),
        "config": str(config_path),
        "report_md": str(report_md),
        "report_json": str(report_json),
        "report_csv": str(report_csv),
        "vector_modes": found_modes,
        "vector_metric_row_count": len(vector_metric_rows),
        "vector_query_class_row_count": len(vector_query_class_rows),
        "claim_boundary": {
            "local_deterministic_vector_baseline": True,
            "external_embedding_api": False,
            "network_required": False,
            "secret_required": False,
            "state_of_the_art_vector_search": False,
            "production_vector_database": False,
            "legal_advice": False,
        },
    }

    write_json(report_json, summary)

    lines = [
        "# RQ7 Vector Baseline Report",
        "",
        f"- status: {summary['status']}",
        f"- generated_at_utc: {generated_at_utc}",
        f"- runner_status: {summary['runner_status']}",
        f"- runner_passed: {summary['runner_passed']}",
        "",
        "## Claim Boundary",
        "",
        "- local_deterministic_vector_baseline: true",
        "- external_embedding_api: false",
        "- network_required: false",
        "- secret_required: false",
        "- state_of_the_art_vector_search: false",
        "- production_vector_database: false",
        "- legal_advice: false",
        "",
        "This is a local deterministic vector-style baseline.",
        "",
        "It is not a neural embedding baseline, not a production vector database benchmark, and not a state-of-the-art semantic search comparison.",
        "",
        "## Vector Modes",
        "",
    ]

    for mode in found_modes:
        lines.append(f"- {mode}")

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            table_row(
                [
                    "mode",
                    "corpus_size",
                    "target_correct",
                    "candidate_reduction",
                    "estimated_p99_ms",
                    "actual_elapsed_p99_ms",
                    "token_cost_per_1k",
                    "esi",
                    "salt_valid",
                ]
            ),
            table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
        ]
    )

    for row in csv_rows:
        lines.append(
            table_row(
                [
                    row["mode"],
                    row["corpus_size"],
                    row["target_correct_rate"],
                    row["candidate_reduction_ratio"],
                    row["latency_p99_ms"],
                    row["actual_elapsed_p99_ms"],
                    row["estimated_token_cost_usd_per_1k_queries"],
                    row["esi_mean"],
                    row["returned_domain_salt_valid_rate"],
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Verify",
            "",
            "    python -m pytest tests -k rq7",
            "    python examples/hsrag_law/rq7_scale/scripts/build_rq7_vector_baseline_report.py",
            "",
            "## Known Limits",
            "",
            "- This does not use external embeddings.",
            "- This does not call any embedding API.",
            "- This does not benchmark ANN/vector databases.",
            "- Hybrid ranking is not included yet.",
            "- This is not legal advice.",
            "",
        ]
    )

    report_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
