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


def run_rq7_with_registry(base_dir: Path, config_path: Path, registry_path: Path) -> dict[str, Any]:
    result = run_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "run_rq7.py"),
            "--config",
            str(config_path),
            "--chunk-registry",
            str(registry_path),
        ]
    )
    return json.loads(result.stdout)


def artifact_exists(summary: dict[str, Any]) -> bool:
    required = [
        "raw_results",
        "metrics_summary",
        "metrics_by_query_class",
        "acceptance_gates",
        "audit_chain",
        "report",
    ]

    return all(Path(summary[name]).exists() for name in required)


def verify_acceptance(summary: dict[str, Any]) -> bool:
    gates = load_json(Path(summary["acceptance_gates"]))
    return gates.get("passed") is True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="examples/hsrag_law/rq7_scale/config.rq7.json",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_adapter_verify_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    adapter_specs = [
        {
            "adapter": "txt_manifest",
            "builder": [
                sys.executable,
                str(base_dir / "scripts" / "build_chunk_registry.py"),
                "--manifest",
                str(base_dir / "02_input" / "real_law_manifest.example.json"),
                "--output",
                str(verify_dir / "chunk_registry.txt_manifest.json"),
            ],
            "registry": verify_dir / "chunk_registry.txt_manifest.json",
        },
        {
            "adapter": "fixed_csv",
            "builder": [
                sys.executable,
                str(base_dir / "scripts" / "build_chunk_registry_from_csv.py"),
                "--csv",
                str(base_dir / "02_input" / "rq7_csv_fixture.example.csv"),
                "--output",
                str(verify_dir / "chunk_registry.fixed_csv.json"),
            ],
            "registry": verify_dir / "chunk_registry.fixed_csv.json",
        },
        {
            "adapter": "auto_csv",
            "builder": [
                sys.executable,
                str(base_dir / "scripts" / "build_chunk_registry_auto_csv.py"),
                "--csv",
                str(base_dir / "02_input" / "rq7_auto_csv_fixture.example.csv"),
                "--output",
                str(verify_dir / "chunk_registry.auto_csv.json"),
            ],
            "registry": verify_dir / "chunk_registry.auto_csv.json",
        },
    ]

    adapter_results: list[dict[str, Any]] = []

    for spec in adapter_specs:
        builder_result = run_command(spec["builder"])
        builder_summary = json.loads(builder_result.stdout)

        registry_path = Path(spec["registry"])
        runner_summary = run_rq7_with_registry(
            base_dir=base_dir,
            config_path=config_path,
            registry_path=registry_path,
        )

        required_artifacts_exist = artifact_exists(runner_summary)
        acceptance_passed = verify_acceptance(runner_summary)

        adapter_passed = (
            builder_summary.get("status") == "OK"
            and runner_summary.get("status") == "OK"
            and runner_summary.get("passed") is True
            and runner_summary.get("salted_domain_gate") is True
            and runner_summary.get("latest_report") is None
            and required_artifacts_exist
            and acceptance_passed
        )

        adapter_results.append(
            {
                "adapter": spec["adapter"],
                "passed": adapter_passed,
                "builder": builder_summary,
                "runner": runner_summary,
                "registry": str(registry_path),
                "required_artifacts_exist": required_artifacts_exist,
                "acceptance_passed": acceptance_passed,
                "latest_report_is_clean": runner_summary.get("latest_report") is None,
            }
        )

    all_passed = all(result["passed"] for result in adapter_results)

    summary = {
        "schema": "HSRAG_RQ7_ADAPTER_VERIFY_MATRIX_V0_1",
        "status": "OK" if all_passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "adapter_count": len(adapter_results),
        "adapter_results": adapter_results,
        "all_passed": all_passed,
        "claim_boundary": {
            "full_scale_benchmark": False,
            "official_rq4_corpus_connected": False,
            "local_adapter_matrix_only": True,
        },
    }

    summary_json = verify_dir / "rq7_adapter_verify_summary.json"
    summary_txt = verify_dir / "rq7_adapter_verify_summary.txt"

    write_json(summary_json, summary)

    lines = [
        "HSRAG RQ7 adapter verify matrix",
        "",
        f"status: {summary['status']}",
        f"verify_id: {verify_id}",
        f"adapter_count: {summary['adapter_count']}",
        f"all_passed: {summary['all_passed']}",
        "",
        "adapters:",
    ]

    for result in adapter_results:
        lines.append(f"- {result['adapter']}: {'PASS' if result['passed'] else 'FAIL'}")

    lines.extend(
        [
            "",
            "claim_boundary:",
            "- full_scale_benchmark: false",
            "- official_rq4_corpus_connected: false",
            "- local_adapter_matrix_only: true",
            "",
            f"summary_json: {summary_json}",
        ]
    )

    summary_txt.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
