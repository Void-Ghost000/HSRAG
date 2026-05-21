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
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent
    checked_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    release_verify = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "verify_rq7_release.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
            "--tiers",
            str(args.tiers),
        ]
    )

    published_report = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "publish_rq7_public_report.py"),
            "--config",
            str(config_path),
            "--rq4-csv",
            str(rq4_csv_path),
            "--tiers",
            str(args.tiers),
            "--output-dir",
            str(output_dir),
        ]
    )

    report_path = Path(published_report["published_report"])
    summary_path = Path(published_report["published_summary"])

    if not report_path.exists():
        raise SystemExit(f"PUBLISHED_REPORT_NOT_FOUND:{report_path}")

    if not summary_path.exists():
        raise SystemExit(f"PUBLISHED_SUMMARY_NOT_FOUND:{summary_path}")

    report_text = report_path.read_text(encoding="utf-8")

    required_phrases = [
        "# HSRAG RQ7 Public Report",
        "This report does not claim full-scale benchmark completion.",
        "This report does not include vector or hybrid baselines.",
        "The current RQ4 unit derivation is heuristic.",
        "actual_elapsed_p99_ms",
        "python -m pytest tests -k rq7",
    ]

    missing_phrases = [phrase for phrase in required_phrases if phrase not in report_text]

    passed = (
        release_verify.get("status") == "OK"
        and release_verify.get("release_checkpoint") is True
        and release_verify.get("claim_boundary_ok") is True
        and published_report.get("status") == "OK"
        and published_report.get("claim_boundary", {}).get("public_report_published") is True
        and not missing_phrases
    )

    checkpoint = {
        "schema": "HSRAG_RQ7_FINAL_RELEASE_CHECKPOINT_V0_1",
        "status": "OK" if passed else "FAILED",
        "checked_at_utc": checked_at_utc,
        "release_verify": release_verify,
        "published_report": published_report,
        "missing_report_phrases": missing_phrases,
        "test_command": "python -m pytest tests -k rq7",
        "release_checkpoint": True,
        "claim_boundary": {
            "rq7_v0_1_checkpoint": True,
            "rq4_rebuilt_artifact_connected": True,
            "rq4_metrics_snapshot_available": True,
            "rq4_scale_tiers_available": True,
            "public_report_published": True,
            "actual_elapsed_timing_available": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_json = output_dir / "RQ7_RELEASE_CHECKPOINT.json"
    checkpoint_md = output_dir / "RQ7_RELEASE_CHECKPOINT.md"

    write_json(checkpoint_json, checkpoint)

    lines = [
        "# RQ7 Release Checkpoint",
        "",
        f"- status: {checkpoint['status']}",
        f"- checked_at_utc: {checked_at_utc}",
        "- rq7_v0_1_checkpoint: true",
        "- rq4_rebuilt_artifact_connected: true",
        "- rq4_metrics_snapshot_available: true",
        "- rq4_scale_tiers_available: true",
        "- public_report_published: true",
        "- actual_elapsed_timing_available: true",
        "- full_scale_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- unit_derivation_is_heuristic: true",
        "- legal_advice: false",
        "",
        "## Published Files",
        "",
        f"- `{report_path.as_posix()}`",
        f"- `{summary_path.as_posix()}`",
        f"- `{checkpoint_json.as_posix()}`",
        "",
        "## Verify",
        "",
        "    python -m pytest tests -k rq7",
        "    python examples/hsrag_law/rq7_scale/scripts/verify_rq7_release.py --tiers 100,300,600,889",
        "",
        "## Claim Boundary",
        "",
        "This checkpoint does not claim full-scale benchmark completion.",
        "",
        "This checkpoint does not include vector or hybrid baselines.",
        "",
        "The current RQ4 unit derivation is heuristic.",
        "",
        "This is not legal advice.",
        "",
    ]

    checkpoint_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True))

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
