from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def select_candidate(inventory: dict[str, Any], prefer: str | None = None) -> dict[str, Any]:
    candidates = [
        item for item in inventory.get("artifacts", [])
        if item.get("rq7_auto_csv_candidate") is True
    ]

    if not candidates:
        raise ValueError("NO_RQ7_CSV_CANDIDATE_FOUND")

    if prefer:
        preferred = [
            item for item in candidates
            if prefer.lower() in str(item.get("path", "")).lower()
            or prefer.lower() in str(item.get("filename", "")).lower()
        ]

        if preferred:
            return sorted(preferred, key=lambda item: str(item["path"]))[0]

        raise ValueError(f"PREFERRED_CANDIDATE_NOT_FOUND:{prefer}")

    return sorted(candidates, key=lambda item: str(item["path"]))[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="examples/hsrag_law")
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--prefer", required=False, default=None)
    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent
    root = Path(args.root)

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_candidate_run_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    inventory_path = verify_dir / "rq7_candidate_inventory.json"
    inventory_report_path = verify_dir / "rq7_candidate_inventory.md"

    scan_cmd = [
        sys.executable,
        str(base_dir / "scripts" / "scan_rq7_artifacts.py"),
        "--root",
        str(root),
        "--output",
        str(inventory_path),
        "--report",
        str(inventory_report_path),
    ]

    scan_result = run_command(scan_cmd)
    scan_summary = json.loads(scan_result.stdout)
    inventory = load_json(inventory_path)

    candidate = select_candidate(inventory, prefer=args.prefer)
    candidate_path = Path(candidate["path"])

    registry_path = verify_dir / "chunk_registry.selected_candidate.json"

    build_cmd = [
        sys.executable,
        str(base_dir / "scripts" / "build_chunk_registry_auto_csv.py"),
        "--csv",
        str(candidate_path),
        "--output",
        str(registry_path),
    ]

    build_result = run_command(build_cmd)
    build_summary = json.loads(build_result.stdout)

    run_cmd = [
        sys.executable,
        str(base_dir / "scripts" / "run_rq7.py"),
        "--config",
        str(config_path),
        "--chunk-registry",
        str(registry_path),
    ]

    run_result = run_command(run_cmd)
    runner_summary = json.loads(run_result.stdout)

    required_runner_artifacts = [
        "raw_results",
        "metrics_summary",
        "metrics_by_query_class",
        "acceptance_gates",
        "audit_chain",
        "report",
    ]

    missing = [
        name for name in required_runner_artifacts
        if name not in runner_summary or not Path(runner_summary[name]).exists()
    ]

    acceptance = load_json(Path(runner_summary["acceptance_gates"]))

    passed = (
        scan_summary.get("status") == "OK"
        and scan_summary.get("local_only") is True
        and scan_summary.get("zero_network") is True
        and scan_summary.get("zero_secret") is True
        and build_summary.get("status") == "OK"
        and runner_summary.get("status") == "OK"
        and runner_summary.get("passed") is True
        and runner_summary.get("salted_domain_gate") is True
        and runner_summary.get("latest_report") is None
        and acceptance.get("passed") is True
        and not missing
    )

    summary = {
        "schema": "HSRAG_RQ7_CANDIDATE_RUN_V0_1",
        "status": "OK" if passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "scan_summary": scan_summary,
        "selected_candidate": {
            "path": candidate["path"],
            "filename": candidate["filename"],
            "sha256": candidate["sha256"],
            "row_count": candidate["row_count"],
            "detected_columns": candidate["detected_columns"],
        },
        "builder": build_summary,
        "runner": runner_summary,
        "acceptance_passed": acceptance.get("passed"),
        "missing_runner_artifacts": missing,
        "latest_report_is_clean": runner_summary.get("latest_report") is None,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "claim_boundary": {
            "candidate_run_only": True,
            "full_scale_benchmark": False,
            "official_rq4_corpus_connected": False,
            "legal_advice": False,
        },
    }

    summary_json = verify_dir / "rq7_candidate_run_summary.json"
    summary_txt = verify_dir / "rq7_candidate_run_summary.txt"

    write_json(summary_json, summary)

    lines = [
        "HSRAG RQ7 candidate select and run",
        "",
        f"status: {summary['status']}",
        f"verify_id: {verify_id}",
        f"selected_candidate: {candidate['path']}",
        f"candidate_rows: {candidate['row_count']}",
        f"acceptance_passed: {summary['acceptance_passed']}",
        f"latest_report_is_clean: {summary['latest_report_is_clean']}",
        "",
        "claim_boundary:",
        "- candidate_run_only: true",
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
