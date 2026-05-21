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
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_rq4_verify_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    registry_path = verify_dir / "chunk_registry.rq4_rebuilt.verify.json"

    builder_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(rq4_csv_path),
            "--output",
            str(registry_path),
        ]
    )

    registry = load_json(registry_path)

    runner_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7.py"),
            "--config",
            str(config_path),
            "--chunk-registry",
            str(registry_path),
        ]
    )

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

    chunk_count = int(registry.get("chunk_count", 0))
    corpora = sorted({chunk["corpus"] for chunk in registry.get("chunks", [])})
    units = sorted({chunk["unit"] for chunk in registry.get("chunks", [])})

    passed = (
        builder_summary.get("status") == "OK"
        and builder_summary.get("rq4_rebuilt_artifact_adapter") is True
        and chunk_count >= 800
        and runner_summary.get("status") == "OK"
        and runner_summary.get("passed") is True
        and runner_summary.get("salted_domain_gate") is True
        and runner_summary.get("latest_report") is None
        and acceptance.get("passed") is True
        and not missing
    )

    summary = {
        "schema": "HSRAG_RQ7_RQ4_VERIFY_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "rq4_csv": str(rq4_csv_path),
        "generated_registry": str(registry_path),
        "builder": builder_summary,
        "registry": {
            "chunk_count": chunk_count,
            "corpora": corpora,
            "unit_count": len(units),
            "sample_units": units[:20],
            "claim_boundary": registry.get("claim_boundary", {}),
        },
        "runner": runner_summary,
        "acceptance_passed": acceptance.get("passed"),
        "missing_runner_artifacts": missing,
        "latest_report_is_clean": runner_summary.get("latest_report") is None,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "full_scale_benchmark": False,
            "official_rq4_corpus_connected": True,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    summary_json = verify_dir / "rq7_rq4_verify_summary.json"
    summary_txt = verify_dir / "rq7_rq4_verify_summary.txt"

    write_json(summary_json, summary)

    lines = [
        "HSRAG RQ7 RQ4 rebuilt artifact verify",
        "",
        f"status: {summary['status']}",
        f"verify_id: {verify_id}",
        f"rq4_csv: {rq4_csv_path}",
        f"chunk_count: {chunk_count}",
        f"corpora: {', '.join(corpora)}",
        f"unit_count: {len(units)}",
        f"acceptance_passed: {summary['acceptance_passed']}",
        f"latest_report_is_clean: {summary['latest_report_is_clean']}",
        "",
        "claim_boundary:",
        "- rq4_rebuilt_artifact_connected: true",
        "- full_scale_benchmark: false",
        "- official_rq4_corpus_connected: true",
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
