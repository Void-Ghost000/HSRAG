from __future__ import annotations

import argparse
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
    release_id = "rq7_release_verify_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    release_dir = base_dir / "04_runs" / release_id
    release_dir.mkdir(parents=True, exist_ok=False)

    master = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "verify_rq7_all.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
        ]
    )

    public_report = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "build_rq7_public_report.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
            "--tiers",
            str(args.tiers),
        ]
    )

    report_path = Path(public_report["report"])

    if not report_path.exists():
        raise SystemExit(f"PUBLIC_REPORT_NOT_FOUND:{report_path}")

    report_text = report_path.read_text(encoding="utf-8")

    required_report_phrases = [
        "This report does not claim full-scale benchmark completion.",
        "This report does not include vector or hybrid baselines.",
        "The current RQ4 unit derivation is heuristic.",
        "actual_elapsed_p99_ms",
        "python -m pytest tests -k rq7",
    ]

    missing_report_phrases = [
        phrase for phrase in required_report_phrases
        if phrase not in report_text
    ]

    claim_boundary_ok = (
        master.get("claim_boundary", {}).get("full_scale_benchmark") is False
        and master.get("claim_boundary", {}).get("legal_advice") is False
        and master.get("claim_boundary", {}).get("unit_derivation_is_heuristic") is True
        and public_report.get("claim_boundary", {}).get("full_scale_benchmark") is False
        and public_report.get("claim_boundary", {}).get("vector_hybrid_baselines") is False
        and public_report.get("claim_boundary", {}).get("legal_advice") is False
        and public_report.get("claim_boundary", {}).get("unit_derivation_is_heuristic") is True
        and not missing_report_phrases
    )

    passed = (
        master.get("status") == "OK"
        and master.get("all_passed") is True
        and master.get("latest_report_is_clean") is True
        and public_report.get("status") == "OK"
        and public_report.get("rq4_chunk_count", 0) >= 800
        and public_report.get("actual_elapsed_timing_available") is True
        and claim_boundary_ok
    )

    summary = {
        "schema": "HSRAG_RQ7_RELEASE_VERIFY_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "release_id": release_id,
        "run_started_at_utc": run_started_at_utc,
        "master_verify": {
            "status": master.get("status"),
            "verify_id": master.get("verify_id"),
            "all_passed": master.get("all_passed"),
            "latest_report_is_clean": master.get("latest_report_is_clean"),
        },
        "public_report": {
            "status": public_report.get("status"),
            "report_id": public_report.get("report_id"),
            "report": public_report.get("report"),
            "rq4_chunk_count": public_report.get("rq4_chunk_count"),
            "executed_tiers": public_report.get("executed_tiers"),
            "actual_elapsed_timing_available": public_report.get("actual_elapsed_timing_available"),
        },
        "claim_boundary_ok": claim_boundary_ok,
        "missing_report_phrases": missing_report_phrases,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "release_checkpoint": True,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "rq4_metrics_snapshot_available": True,
            "rq4_scale_tiers_available": True,
            "public_report_available": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    summary_json = release_dir / "rq7_release_verify_summary.json"
    summary_txt = release_dir / "rq7_release_verify_summary.txt"

    write_json(summary_json, summary)

    lines = [
        "HSRAG RQ7 release verify",
        "",
        f"status: {summary['status']}",
        f"release_id: {release_id}",
        f"master_verify_status: {summary['master_verify']['status']}",
        f"master_all_passed: {summary['master_verify']['all_passed']}",
        f"public_report_status: {summary['public_report']['status']}",
        f"rq4_chunk_count: {summary['public_report']['rq4_chunk_count']}",
        f"executed_tiers: {summary['public_report']['executed_tiers']}",
        f"claim_boundary_ok: {claim_boundary_ok}",
        "",
        "claim_boundary:",
        "- rq4_rebuilt_artifact_connected: true",
        "- rq4_metrics_snapshot_available: true",
        "- rq4_scale_tiers_available: true",
        "- public_report_available: true",
        "- full_scale_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- unit_derivation_is_heuristic: true",
        "- legal_advice: false",
        "",
        f"summary_json: {summary_json}",
    ]

    summary_txt.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
