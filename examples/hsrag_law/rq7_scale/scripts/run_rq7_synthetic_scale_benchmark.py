from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def run_json_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def parse_sizes(value: str) -> list[int]:
    sizes = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not sizes:
        raise ValueError("NO_TARGET_SIZES")
    return sorted(set(sizes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    parser.add_argument("--target-sizes", default="1000,5000,10000")
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
    target_sizes = parse_sizes(args.target_sizes)

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_id = "rq7_synthetic_scale_benchmark_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    run_dir = base_dir / "04_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    benchmark_results: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    for target_size in target_sizes:
        registry_path = run_dir / f"chunk_registry.synthetic_{target_size}.json"

        builder = run_json_command(
            [
                sys.executable,
                str(base_dir / "scripts" / "build_rq7_synthetic_expanded_registry.py"),
                "--rq4-csv",
                str(rq4_csv_path),
                "--target-size",
                str(target_size),
                "--output",
                str(registry_path),
            ]
        )

        runner = run_json_command(
            [
                sys.executable,
                str(base_dir / "scripts" / "run_rq7.py"),
                "--config",
                str(config_path),
                "--chunk-registry",
                str(registry_path),
            ]
        )

        metrics_path = Path(runner["metrics_summary"])
        metrics_rows = read_csv_rows(metrics_path)

        for row in metrics_rows:
            metric_rows.append(
                {
                    "target_size": target_size,
                    "real_chunk_count": builder["real_chunk_count"],
                    "synthetic_chunk_count": builder["synthetic_chunk_count"],
                    "mode": row["mode"],
                    "corpus_size": row["corpus_size"],
                    "target_correct_rate": row["target_correct_rate"],
                    "candidate_reduction_ratio": row["candidate_reduction_ratio"],
                    "latency_p99_ms": row["latency_p99_ms"],
                    "actual_elapsed_p99_ms": row.get("actual_elapsed_p99_ms", "0.0"),
                    "estimated_token_cost_usd_per_1k_queries": row["estimated_token_cost_usd_per_1k_queries"],
                    "esi_mean": row["esi_mean"],
                    "returned_domain_salt_valid_rate": row.get("returned_domain_salt_valid_rate", "0.0"),
                }
            )

        benchmark_results.append(
            {
                "target_size": target_size,
                "builder": builder,
                "runner": runner,
                "passed": runner.get("status") == "OK",
                "registry": str(registry_path),
            }
        )

    all_passed = all(item["passed"] for item in benchmark_results)

    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.json"
    output_md = output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.md"
    output_csv = output_dir / "RQ7_SYNTHETIC_SCALE_BENCHMARK.csv"

    summary = {
        "schema": "HSRAG_RQ7_SYNTHETIC_SCALE_BENCHMARK_V0_1",
        "status": "OK" if all_passed else "FAILED",
        "run_id": run_id,
        "run_started_at_utc": run_started_at_utc,
        "target_sizes": target_sizes,
        "benchmark_results": benchmark_results,
        "metric_csv": str(output_csv),
        "claim_boundary": {
            "synthetic_expansion": True,
            "synthetic_chunks_explicitly_labeled": True,
            "synthetic_expansion_is_not_new_legal_corpus": True,
            "scale_stress_only": True,
            "full_scale_real_corpus_benchmark": False,
            "vector_hybrid_baselines": False,
            "legal_advice": False,
        },
    }

    write_json(output_json, summary)
    write_csv(output_csv, metric_rows)

    lines = [
        "# RQ7 Synthetic Scale Benchmark",
        "",
        f"- status: {summary['status']}",
        f"- run_id: {run_id}",
        f"- target_sizes: {', '.join(str(size) for size in target_sizes)}",
        "",
        "## Claim Boundary",
        "",
        "- synthetic_expansion: true",
        "- synthetic_chunks_explicitly_labeled: true",
        "- synthetic_expansion_is_not_new_legal_corpus: true",
        "- scale_stress_only: true",
        "- full_scale_real_corpus_benchmark: false",
        "- vector_hybrid_baselines: false",
        "- legal_advice: false",
        "",
        "## Metrics CSV",
        "",
        f"- `{output_csv.as_posix()}`",
        "",
    ]

    output_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
