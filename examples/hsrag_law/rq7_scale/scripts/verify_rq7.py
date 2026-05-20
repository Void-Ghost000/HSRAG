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
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="examples/hsrag_law/rq7_scale/config.rq7.json",
    )
    parser.add_argument(
        "--manifest",
        default="examples/hsrag_law/rq7_scale/02_input/real_law_manifest.example.json",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=220,
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    manifest_path = Path(args.manifest)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not manifest_path.exists():
        raise SystemExit(f"MANIFEST_NOT_FOUND:{manifest_path}")

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_verify_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")

    base_dir = config_path.resolve().parent
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    generated_registry_path = verify_dir / "chunk_registry.generated.verify.json"

    builder_cmd = [
        sys.executable,
        str(base_dir / "scripts" / "build_chunk_registry.py"),
        "--manifest",
        str(manifest_path),
        "--output",
        str(generated_registry_path),
        "--max-tokens",
        str(args.max_tokens),
    ]

    builder_result = run_command(builder_cmd)
    builder_summary = json.loads(builder_result.stdout)

    runner_cmd = [
        sys.executable,
        str(base_dir / "scripts" / "run_rq7.py"),
        "--config",
        str(config_path),
        "--chunk-registry",
        str(generated_registry_path),
    ]

    runner_result = run_command(runner_cmd)
    runner_summary = json.loads(runner_result.stdout)

    required_paths = {
        "raw_results": Path(runner_summary["raw_results"]),
        "metrics_summary": Path(runner_summary["metrics_summary"]),
        "acceptance_gates": Path(runner_summary["acceptance_gates"]),
        "audit_chain": Path(runner_summary["audit_chain"]),
        "report": Path(runner_summary["report"]),
    }

    missing = [name for name, path in required_paths.items() if not path.exists()]

    acceptance = load_json(required_paths["acceptance_gates"])

    latest_report_is_clean = runner_summary.get("latest_report") is None

    passed = (
        builder_summary.get("status") == "OK"
        and runner_summary.get("status") == "OK"
        and runner_summary.get("passed") is True
        and acceptance.get("passed") is True
        and not missing
        and latest_report_is_clean
    )

    summary = {
        "schema": "HSRAG_RQ7_VERIFY_SUMMARY_V0_1",
        "status": "OK" if passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "config": str(config_path),
        "manifest": str(manifest_path),
        "generated_registry": str(generated_registry_path),
        "builder": builder_summary,
        "runner": runner_summary,
        "required_artifacts_exist": not missing,
        "missing_artifacts": missing,
        "acceptance_passed": acceptance.get("passed"),
        "latest_report_is_clean": latest_report_is_clean,
        "one_command_verify": True,
        "claim_boundary": {
            "synthetic_dry_run": runner_summary.get("synthetic_dry_run"),
            "toy_retrieval": runner_summary.get("toy_retrieval"),
            "salted_domain_gate": runner_summary.get("salted_domain_gate"),
            "full_scale_benchmark": False,
            "official_rq4_corpus_connected": False,
        },
    }

    summary_path = verify_dir / "rq7_verify_summary.json"
    write_json(summary_path, summary)

    text_summary = "\n".join(
        [
            "HSRAG RQ7 one-command verify",
            "",
            f"status: {summary['status']}",
            f"verify_id: {verify_id}",
            f"builder_status: {builder_summary.get('status')}",
            f"runner_status: {runner_summary.get('status')}",
            f"acceptance_passed: {acceptance.get('passed')}",
            f"required_artifacts_exist: {not missing}",
            f"latest_report_is_clean: {latest_report_is_clean}",
            "",
            "claim_boundary:",
            "- toy_retrieval: true",
            "- salted_domain_gate: true",
            "- full_scale_benchmark: false",
            "- official_rq4_corpus_connected: false",
            "",
            f"summary_json: {summary_path}",
        ]
    )

    text_summary_path = verify_dir / "rq7_verify_summary.txt"
    text_summary_path.write_text(text_summary, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
