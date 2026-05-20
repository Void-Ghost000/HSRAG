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
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

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

    latest_clean = (
        core_summary.get("latest_report_is_clean") is True
        and all(
            item.get("latest_report_is_clean") is True
            for item in adapter_summary.get("adapter_results", [])
        )
        and candidate_summary.get("latest_report_is_clean") is True
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
        and latest_clean
    )

    summary = {
        "schema": "HSRAG_RQ7_ALL_VERIFY_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "inventory": inventory_summary,
        "core_verify": core_summary,
        "adapter_matrix": adapter_summary,
        "candidate_run": candidate_summary,
        "latest_report_is_clean": latest_clean,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "all_passed": passed,
        "claim_boundary": {
            "master_verify_only": True,
            "full_scale_benchmark": False,
            "official_rq4_corpus_connected": False,
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
        f"latest_report_is_clean: {latest_clean}",
        f"all_passed: {passed}",
        "",
        "claim_boundary:",
        "- master_verify_only: true",
        "- full_scale_benchmark: false",
        "- official_rq4_corpus_connected: false",
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
