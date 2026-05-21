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
    parser.add_argument("--root", default="examples/hsrag_law/rq7_scale/02_input")
    parser.add_argument("--prefer", default="auto")
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_all_verify_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    inventory_json = verify_dir / "rq7_inventory.json"
    inventory_md = verify_dir / "rq7_inventory.md"

    inventory_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "scan_rq7_artifacts.py"),
            "--root",
            str(args.root),
            "--output",
            str(inventory_json),
            "--report",
            str(inventory_md),
        ]
    )

    core_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "verify_rq7.py"),
            "--config",
            str(config_path),
        ]
    )

    adapter_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "verify_rq7_adapters.py"),
            "--config",
            str(config_path),
        ]
    )

    candidate_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7_candidate.py"),
            "--root",
            str(args.root),
            "--config",
            str(config_path),
            "--prefer",
            str(args.prefer),
        ]
    )

    rq4_metrics_snapshot = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "snapshot_rq7_rq4_metrics.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
        ]
    )

    rq4_verify = rq4_metrics_snapshot.get("rq4_verify", {})

    latest_clean = (
        core_summary.get("latest_report_is_clean") is True
        and all(
            item.get("latest_report_is_clean") is True
            for item in adapter_summary.get("adapter_results", [])
        )
        and candidate_summary.get("latest_report_is_clean") is True
        and rq4_verify.get("latest_report_is_clean") is True
    )

    passed = (
        inventory_summary.get("status") == "OK"
        and inventory_summary.get("local_only") is True
        and inventory_summary.get("zero_network") is True
        and inventory_summary.get("zero_secret") is True
        and core_summary.get("status") == "OK"
        and core_summary.get("one_command_verify") is True
        and core_summary.get("acceptance_passed") is True
        and adapter_summary.get("status") == "OK"
        and adapter_summary.get("all_passed") is True
        and candidate_summary.get("status") == "OK"
        and candidate_summary.get("acceptance_passed") is True
        and rq4_metrics_snapshot.get("status") == "OK"
        and rq4_verify.get("acceptance_passed") is True
        and rq4_verify.get("chunk_count", 0) >= 800
        and rq4_verify.get("unit_derivation_is_heuristic") is True
        and latest_clean
    )

    summary = {
        "schema": "HSRAG_RQ7_ALL_VERIFY_SUMMARY_V0_3",
        "status": "OK" if passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "inventory": inventory_summary,
        "core_verify": core_summary,
        "adapter_matrix": adapter_summary,
        "candidate_run": candidate_summary,
        "rq4_verify": rq4_verify,
        "rq4_metrics_snapshot": rq4_metrics_snapshot,
        "latest_report_is_clean": latest_clean,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "all_passed": passed,
        "claim_boundary": {
            "master_verify_only": True,
            "rq4_rebuilt_artifact_connected": True,
            "rq4_metrics_snapshot_available": True,
            "official_rq4_corpus_connected": True,
            "unit_derivation_is_heuristic": True,
            "full_scale_benchmark": False,
            "legal_advice": False,
        },
    }

    summary_json = verify_dir / "rq7_all_verify_summary.json"
    summary_txt = verify_dir / "rq7_all_verify_summary.txt"

    write_json(summary_json, summary)

    lines = [
        "HSRAG RQ7 master verify",
        "",
        f"status: {summary['status']}",
        f"verify_id: {verify_id}",
        f"inventory_status: {inventory_summary.get('status')}",
        f"core_verify_status: {core_summary.get('status')}",
        f"adapter_matrix_status: {adapter_summary.get('status')}",
        f"candidate_run_status: {candidate_summary.get('status')}",
        f"rq4_metrics_snapshot_status: {rq4_metrics_snapshot.get('status')}",
        f"rq4_chunk_count: {rq4_verify.get('chunk_count')}",
        f"latest_report_is_clean: {latest_clean}",
        f"all_passed: {passed}",
        "",
        "claim_boundary:",
        "- master_verify_only: true",
        "- rq4_rebuilt_artifact_connected: true",
        "- rq4_metrics_snapshot_available: true",
        "- official_rq4_corpus_connected: true",
        "- unit_derivation_is_heuristic: true",
        "- full_scale_benchmark: false",
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
