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
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.full_queries.json")
    parser.add_argument("--output-dir", default="examples/hsrag_law/rq7_scale/05_reports")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    base_dir = config_path.resolve().parent
    published_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    diagnostics = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "analyze_rq7_full_query_diagnostics.py"),
            "--config",
            str(config_path),
        ]
    )

    diagnostic_id = diagnostics["diagnostic_id"]
    diagnostic_dir = base_dir / "04_runs" / diagnostic_id

    source_json = diagnostic_dir / "rq7_full_query_diagnostics.json"
    source_md = diagnostic_dir / "rq7_full_query_diagnostics.md"

    if not source_json.exists():
        raise SystemExit(f"DIAGNOSTICS_JSON_NOT_FOUND:{source_json}")

    if not source_md.exists():
        raise SystemExit(f"DIAGNOSTICS_MD_NOT_FOUND:{source_md}")

    output_dir.mkdir(parents=True, exist_ok=True)

    published_json = output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.json"
    published_md = output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS.md"
    published_summary = output_dir / "RQ7_FULL_QUERY_DIAGNOSTICS_SUMMARY.json"

    shutil.copyfile(source_json, published_json)
    shutil.copyfile(source_md, published_md)

    summary = {
        "schema": "HSRAG_RQ7_FULL_QUERY_DIAGNOSTICS_PUBLISH_V0_1",
        "status": "OK",
        "published_at_utc": published_at_utc,
        "diagnostic_id": diagnostic_id,
        "diagnostic_status": diagnostics.get("diagnostic_status"),
        "acceptance_passed": diagnostics.get("acceptance_passed"),
        "raw_result_count": diagnostics.get("raw_result_count"),
        "query_class_count": diagnostics.get("query_class_count"),
        "published_json": str(published_json),
        "published_md": str(published_md),
        "published_summary": str(published_summary),
        "claim_boundary": {
            "diagnostic_only": True,
            "full_query_expansion": True,
            "acceptance_failure_allowed_for_diagnostics": True,
            "full_scale_benchmark": False,
            "vector_hybrid_baselines": False,
        },
    }

    write_json(published_summary, summary)

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
