from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def table_row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value) for value in values) + " |"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    parser.add_argument("--tiers", default="100,300,600,889")
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report_id = "rq7_public_report_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    report_dir = base_dir / "04_runs" / report_id
    report_dir.mkdir(parents=True, exist_ok=False)

    snapshot = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "snapshot_rq7_rq4_metrics.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
        ]
    )

    scale = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7_rq4_scale_tiers.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
            "--tiers",
            str(args.tiers),
        ]
    )

    scale_dir = base_dir / "04_runs" / scale["verify_id"]
    scale_csv = scale_dir / "rq7_rq4_scale_tier_summary.csv"

    if not scale_csv.exists():
        raise SystemExit(f"SCALE_SUMMARY_CSV_NOT_FOUND:{scale_csv}")

    scale_rows = read_csv_rows(scale_csv)

    passed = (
        snapshot.get("status") == "OK"
        and snapshot.get("rq4_verify", {}).get("acceptance_passed") is True
        and scale.get("status") == "OK"
        and scale.get("all_passed") is True
        and scale.get("full_chunk_count", 0) >= 800
    )

    report_path = report_dir / "RQ7_PUBLIC_REPORT.md"
    summary_path = report_dir / "rq7_public_report_summary.json"

    lines: list[str] = [
        "# HSRAG RQ7 Public Report",
        "",
        "## Status",
        "",
        f"- report_id: {report_id}",
        f"- run_started_at_utc: {run_started_at_utc}",
        f"- status: {'OK' if passed else 'FAILED'}",
        f"- rq4_rebuilt_chunk_count: {snapshot.get('rq4_verify', {}).get('chunk_count')}",
        f"- scale_tiers: {', '.join(str(item) for item in scale.get('executed_tiers', []))}",
        f"- actual_elapsed_timing_available: true",
        "",
        "## What This Report Covers",
        "",
        "This report summarizes the current RQ7 local verification stack using the RQ4 rebuilt chunk artifact.",
        "",
        "It covers:",
        "",
        "- RQ4 rebuilt artifact connection",
        "- RQ4 metrics snapshot",
        "- RQ4 scale-tier run",
        "- retrieval-mode comparison output",
        "- query-class metrics availability",
        "- actual elapsed timing propagation",
        "",
        "## Claim Boundary",
        "",
        "This report does not claim that HSRAG replaces all RAG systems.",
        "",
        "This report does not claim full-scale benchmark completion.",
        "",
        "This report does not provide legal advice.",
        "",
        "This report does not include vector or hybrid baselines.",
        "",
        "The current RQ4 unit derivation is heuristic.",
        "",
        "Latency values include local actual elapsed measurements, but this is not a production latency benchmark.",
        "",
        "## RQ4 Metrics Snapshot",
        "",
        f"- snapshot_status: {snapshot.get('status')}",
        f"- acceptance_passed: {snapshot.get('rq4_verify', {}).get('acceptance_passed')}",
        f"- latest_report_is_clean: {snapshot.get('rq4_verify', {}).get('latest_report_is_clean')}",
        f"- chunk_count: {snapshot.get('rq4_verify', {}).get('chunk_count')}",
        f"- unit_count: {snapshot.get('rq4_verify', {}).get('unit_count')}",
        f"- unit_derivation_is_heuristic: {snapshot.get('rq4_verify', {}).get('unit_derivation_is_heuristic')}",
        "",
        "## Available Modes",
        "",
    ]

    for mode in snapshot.get("modes", []):
        lines.append(f"- {mode}")

    lines.extend(
        [
            "",
            "## Available Query Classes",
            "",
        ]
    )

    for query_class in snapshot.get("query_classes", []):
        lines.append(f"- {query_class}")

    lines.extend(
        [
            "",
            "## Scale Tier Metrics",
            "",
            table_row(
                [
                    "tier_size",
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
                    row.get("tier_size"),
                    row.get("mode"),
                    row.get("target_correct_rate"),
                    row.get("candidate_reduction_ratio"),
                    row.get("latency_p99_ms"),
                    row.get("actual_elapsed_p99_ms", "NA"),
                    row.get("estimated_token_cost_usd_per_1k_queries"),
                    row.get("esi_mean"),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Reproduction Commands",
            "",
            "Run RQ7 master verify:",
            "",
            "    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_all.py",
            "",
            "Run RQ4 metrics snapshot:",
            "",
            "    python examples/hsrag_law/rq7_scale/scripts/snapshot_rq7_rq4_metrics.py",
            "",
            "Run RQ4 scale tiers:",
            "",
            f"    python examples/hsrag_law/rq7_scale/scripts/run_rq7_rq4_scale_tiers.py --tiers {args.tiers}",
            "",
            "Run all RQ7 tests:",
            "",
            "    python -m pytest tests -k rq7",
            "",
            "## Known Limits",
            "",
            "- RQ4 unit derivation is heuristic.",
            "- Full-scale benchmark is still pending.",
            "- Vector and hybrid baselines are not implemented yet.",
            "- Token cost is estimated, not API billing.",
            "- Production latency is not measured.",
            "- This is not legal advice.",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "schema": "HSRAG_RQ7_PUBLIC_REPORT_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "report_id": report_id,
        "run_started_at_utc": run_started_at_utc,
        "report": str(report_path),
        "snapshot_id": snapshot.get("snapshot_id"),
        "scale_verify_id": scale.get("verify_id"),
        "scale_summary_csv": str(scale_csv),
        "rq4_chunk_count": snapshot.get("rq4_verify", {}).get("chunk_count"),
        "executed_tiers": scale.get("executed_tiers"),
        "actual_elapsed_timing_available": True,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "public_report_only": True,
            "full_scale_benchmark": False,
            "unit_derivation_is_heuristic": True,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
    }

    write_json(summary_path, summary)

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
