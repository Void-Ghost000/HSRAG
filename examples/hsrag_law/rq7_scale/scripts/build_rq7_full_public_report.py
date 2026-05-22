from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)

    required = {
        "full_branch_status": reports_dir / "RQ7_FULL_BRANCH_STATUS.json",
        "diagnostics": reports_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.json",
        "triage": reports_dir / "RQ7_FULL_QUERY_TRIAGE.json",
        "corpus_inventory": reports_dir / "RQ7_CORPUS_EXPANSION_INVENTORY.json",
        "synthetic_scale": reports_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.json",
        "synthetic_scale_csv": reports_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.csv",
    }

    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise SystemExit("MISSING_REQUIRED_REPORTS:" + ",".join(missing))

    full_status = load_json(required["full_branch_status"])
    diagnostics = load_json(required["diagnostics"])
    triage = load_json(required["triage"])
    inventory = load_json(required["corpus_inventory"])
    synthetic = load_json(required["synthetic_scale"])
    scale_rows = read_csv_rows(required["synthetic_scale_csv"])

    generated_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    passed = (
        full_status.get("status") == "OK"
        and diagnostics.get("claim_boundary", {}).get("diagnostic_only") is True
        and triage.get("claim_boundary", {}).get("triage_only") is True
        and inventory.get("claim_boundary", {}).get("inventory_only") is True
        and synthetic.get("claim_boundary", {}).get("synthetic_expansion") is True
        and synthetic.get("claim_boundary", {}).get("synthetic_expansion_is_not_new_legal_corpus") is True
        and synthetic.get("claim_boundary", {}).get("full_scale_real_corpus_benchmark") is False
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    report_md = output_dir / "RQ7_FULL_PUBLIC_REPORT.md"
    report_json = output_dir / "RQ7_FULL_PUBLIC_REPORT_SUMMARY.json"

    summary = {
        "schema": "HSRAG_RQ7_FULL_PUBLIC_REPORT_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "generated_at_utc": generated_at_utc,
        "report": str(report_md),
        "full_branch_status": {
            "status": full_status.get("status"),
            "query_count": full_status.get("full_query_seed", {}).get("query_count"),
            "added_query_count": full_status.get("full_query_seed", {}).get("added_query_count"),
        },
        "diagnostics": {
            "diagnostic_status": diagnostics.get("diagnostic_status"),
            "acceptance_passed": diagnostics.get("acceptance_passed"),
            "raw_result_count": diagnostics.get("raw_result_count"),
            "query_class_count": diagnostics.get("query_class_count"),
        },
        "triage": {
            "raw_result_count": triage.get("raw_result_count"),
            "triage_summary": triage.get("triage_summary", {}),
        },
        "corpus_inventory": {
            "artifact_count": inventory.get("artifact_count"),
            "text_corpus_candidate_count": inventory.get("text_corpus_candidate_count"),
            "kind_summary": inventory.get("kind_summary", {}),
        },
        "synthetic_scale": {
            "status": synthetic.get("status"),
            "target_sizes": synthetic.get("target_sizes"),
            "metric_csv": str(required["synthetic_scale_csv"]),
        },
        "claim_boundary": {
            "full_query_expansion": True,
            "diagnostic_only": True,
            "triage_only": True,
            "synthetic_expansion": True,
            "synthetic_scale_stress_only": True,
            "synthetic_expansion_is_not_new_legal_corpus": True,
            "full_scale_real_corpus_benchmark": False,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
    }

    write_json(report_json, summary)

    lines = [
        "# RQ7 Full Public Report",
        "",
        "## Status",
        "",
        f"- status: {summary['status']}",
        f"- generated_at_utc: {generated_at_utc}",
        "- branch_scope: rq7-full-benchmark",
        "",
        "## What This Report Covers",
        "",
        "- full query seed expansion",
        "- full query diagnostics",
        "- full query triage",
        "- corpus expansion inventory",
        "- synthetic 1k / 5k / 10k scale stress benchmark",
        "",
        "## Claim Boundary",
        "",
        "- diagnostic_only: true",
        "- triage_only: true",
        "- synthetic_expansion: true",
        "- synthetic_scale_stress_only: true",
        "- synthetic_expansion_is_not_new_legal_corpus: true",
        "- full_scale_real_corpus_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- legal_advice: false",
        "",
        "This report does not claim a full-scale real-law corpus benchmark.",
        "",
        "This report does not include vector or hybrid baselines.",
        "",
        "Synthetic chunks are explicitly labeled and are not additional legal evidence.",
        "",
        "## Full Query Expansion",
        "",
        f"- query_count: {summary['full_branch_status']['query_count']}",
        f"- added_query_count: {summary['full_branch_status']['added_query_count']}",
        "",
        "## Diagnostics",
        "",
        f"- diagnostic_status: {summary['diagnostics']['diagnostic_status']}",
        f"- acceptance_passed: {summary['diagnostics']['acceptance_passed']}",
        f"- raw_result_count: {summary['diagnostics']['raw_result_count']}",
        f"- query_class_count: {summary['diagnostics']['query_class_count']}",
        "",
        "## Triage Summary",
        "",
    ]

    for key, count in sorted(summary["triage"]["triage_summary"].items()):
        lines.append(f"- {key}: {count}")

    lines.extend(
        [
            "",
            "## Corpus Inventory",
            "",
            f"- artifact_count: {summary['corpus_inventory']['artifact_count']}",
            f"- text_corpus_candidate_count: {summary['corpus_inventory']['text_corpus_candidate_count']}",
            "",
            "## Synthetic Scale Benchmark",
            "",
            f"- target_sizes: {summary['synthetic_scale']['target_sizes']}",
            "",
            table_row(
                [
                    "target_size",
                    "mode",
                    "target_correct",
                    "candidate_reduction",
                    "estimated_p99_ms",
                    "actual_elapsed_p99_ms",
                    "token_cost_per_1k",
                    "esi",
                ]
            ),
            table_row(["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:"]),
        ]
    )

    for row in scale_rows:
        lines.append(
            table_row(
                [
                    row.get("target_size"),
                    row.get("mode"),
                    row.get("target_correct_rate"),
                    row.get("candidate_reduction_ratio"),
                    row.get("latency_p99_ms"),
                    row.get("actual_elapsed_p99_ms"),
                    row.get("estimated_token_cost_usd_per_1k_queries"),
                    row.get("esi_mean"),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Verify",
            "",
            "    python -m pytest tests -k rq7",
            "    python examples/hsrag_law/rq7_scale/scripts/build_rq7_full_branch_status.py",
            "    python examples/hsrag_law/rq7_scale/scripts/run_rq7_synthetic_scale_benchmark.py --target-sizes 1000,5000,10000",
            "",
            "## Known Limits",
            "",
            "- Real-law corpus currently remains limited by available source artifacts.",
            "- Synthetic scale expansion is for scale stress only.",
            "- Vector / hybrid baselines are pending.",
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
