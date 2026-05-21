from __future__ import annotations

import argparse
import json
import shutil
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

    published_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    public_report_summary = run_json_command(
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

    source_report = Path(public_report_summary["report"])

    if not source_report.exists():
        raise SystemExit(f"SOURCE_PUBLIC_REPORT_NOT_FOUND:{source_report}")

    output_dir.mkdir(parents=True, exist_ok=True)

    published_report = output_dir / "RQ7_PUBLIC_REPORT.md"
    published_summary = output_dir / "RQ7_PUBLIC_REPORT_SUMMARY.json"

    shutil.copyfile(source_report, published_report)

    summary = {
        "schema": "HSRAG_RQ7_PUBLISHED_PUBLIC_REPORT_V0_1",
        "status": "OK" if public_report_summary.get("status") == "OK" else "FAILED",
        "published_at_utc": published_at_utc,
        "source_report": str(source_report),
        "published_report": str(published_report),
        "published_summary": str(published_summary),
        "public_report": public_report_summary,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "public_report_published": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    write_json(published_summary, summary)

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if summary["status"] != "OK":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
