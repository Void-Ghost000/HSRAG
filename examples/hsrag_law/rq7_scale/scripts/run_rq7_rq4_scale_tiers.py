from __future__ import annotations

import argparse
import copy
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TIERS = [100, 300, 600, 889]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def target_keys_from_query_seed(base_dir: Path) -> list[tuple[str, str]]:
    query_seed_path = base_dir / "02_input" / "query_seed.example.json"
    query_seed = load_json(query_seed_path)

    keys: list[tuple[str, str]] = []

    for query in query_seed.get("queries", []):
        target = query.get("target")
        if not target:
            continue

        corpus = target.get("corpus")
        unit = target.get("unit")

        if corpus and unit:
            key = (str(corpus), str(unit))
            if key not in keys:
                keys.append(key)

    return keys


def select_tier_chunks(
    chunks: list[dict[str, Any]],
    tier_size: int,
    required_keys: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    if tier_size > len(chunks):
        raise ValueError(f"TIER_SIZE_EXCEEDS_REGISTRY:{tier_size}>{len(chunks)}")

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    for corpus, unit in required_keys:
        match = next(
            (
                chunk for chunk in chunks
                if str(chunk.get("corpus")) == corpus
                and str(chunk.get("unit")) == unit
            ),
            None,
        )

        if match is not None and match["chunk_id"] not in selected_ids:
            selected.append(match)
            selected_ids.add(str(match["chunk_id"]))

    for chunk in chunks:
        if len(selected) >= tier_size:
            break

        chunk_id = str(chunk["chunk_id"])
        if chunk_id in selected_ids:
            continue

        selected.append(chunk)
        selected_ids.add(chunk_id)

    if len(selected) != tier_size:
        raise ValueError(f"TIER_SELECTION_SIZE_MISMATCH:{len(selected)}!={tier_size}")

    return selected


def summarize_metrics_for_tier(
    tier_size: int,
    runner_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics_path = Path(runner_summary["metrics_summary"])
    rows = read_csv_rows(metrics_path)

    output_rows: list[dict[str, Any]] = []

    for row in rows:
        output_rows.append(
            {
                "tier_size": tier_size,
                "run_id": runner_summary["run_id"],
                "mode": row["mode"],
                "corpus_size": row["corpus_size"],
                "target_correct_rate": row["target_correct_rate"],
                "wrong_corpus_collision_rate": row["wrong_corpus_collision_rate"],
                "wrong_jurisdiction_collision_rate": row["wrong_jurisdiction_collision_rate"],
                "no_evidence_false_allow_rate": row["no_evidence_false_allow_rate"],
                "ambiguous_false_allow_rate": row["ambiguous_false_allow_rate"],
                "candidate_reduction_ratio": row["candidate_reduction_ratio"],
                "retrieved_token_count_mean": row["retrieved_token_count_mean"],
                "estimated_token_cost_usd_per_1k_queries": row["estimated_token_cost_usd_per_1k_queries"],
                "latency_p99_ms": row["latency_p99_ms"],
                "esi_mean": row["esi_mean"],
                "returned_domain_salt_valid_rate": row["returned_domain_salt_valid_rate"],
            }
        )

    return output_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    parser.add_argument("--tiers", default="100,300,600,889")
    args = parser.parse_args()

    config_path = Path(args.config)
    rq4_csv_path = Path(args.rq4_csv)

    if not config_path.exists():
        raise SystemExit(f"CONFIG_NOT_FOUND:{config_path}")

    if not rq4_csv_path.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv_path}")

    base_dir = config_path.resolve().parent

    requested_tiers = [
        int(item.strip())
        for item in args.tiers.split(",")
        if item.strip()
    ]

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    verify_id = "rq7_rq4_scale_tiers_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")
    verify_dir = base_dir / "04_runs" / verify_id
    verify_dir.mkdir(parents=True, exist_ok=False)

    full_registry_path = verify_dir / "chunk_registry.rq4_rebuilt.full.json"

    builder_summary = run_json_command(
        [
            sys.executable,
            str(base_dir / "scripts" / "build_chunk_registry_from_rq4_rebuilt.py"),
            "--csv",
            str(rq4_csv_path),
            "--output",
            str(full_registry_path),
        ]
    )

    full_registry = load_json(full_registry_path)
    all_chunks = list(full_registry["chunks"])
    full_chunk_count = len(all_chunks)

    tiers = sorted(set(tier for tier in requested_tiers if tier <= full_chunk_count))

    if not tiers:
        raise SystemExit("NO_VALID_TIERS")

    required_keys = target_keys_from_query_seed(base_dir)

    config = load_json(config_path)

    tier_results: list[dict[str, Any]] = []
    metrics_rows: list[dict[str, Any]] = []

    for tier_size in tiers:
        tier_chunks = select_tier_chunks(
            chunks=all_chunks,
            tier_size=tier_size,
            required_keys=required_keys,
        )

        tier_registry = copy.deepcopy(full_registry)
        tier_registry["description"] = f"RQ7 RQ4 rebuilt tier registry, tier_size={tier_size}"
        tier_registry["chunk_count"] = len(tier_chunks)
        tier_registry["chunks"] = tier_chunks
        tier_registry["scale_tier"] = {
            "tier_size": tier_size,
            "full_chunk_count": full_chunk_count,
            "required_query_targets_preserved": required_keys,
        }

        tier_registry_path = verify_dir / f"chunk_registry.rq4_rebuilt.tier_{tier_size}.json"
        write_json(tier_registry_path, tier_registry)

        tier_config = copy.deepcopy(config)
        tier_config["_rq7_base_dir"] = str(base_dir)
        tier_config["scale_tiers"] = [
            {
                "name": f"rq4_rebuilt_{tier_size}",
                "chunk_count": tier_size,
            }
        ]

        tier_config_path = verify_dir / f"config.rq7.tier_{tier_size}.json"
        write_json(tier_config_path, tier_config)

        runner_summary = run_json_command(
            [
                sys.executable,
                str(base_dir / "scripts" / "run_rq7.py"),
                "--config",
                str(tier_config_path),
                "--chunk-registry",
                str(tier_registry_path),
            ]
        )

        acceptance = load_json(Path(runner_summary["acceptance_gates"]))

        required_artifacts = [
            "raw_results",
            "metrics_summary",
            "metrics_by_query_class",
            "acceptance_gates",
            "audit_chain",
            "report",
        ]

        missing = [
            name for name in required_artifacts
            if name not in runner_summary or not Path(runner_summary[name]).exists()
        ]

        tier_passed = (
            runner_summary.get("status") == "OK"
            and runner_summary.get("passed") is True
            and runner_summary.get("salted_domain_gate") is True
            and runner_summary.get("latest_report") is None
            and acceptance.get("passed") is True
            and not missing
        )

        tier_results.append(
            {
                "tier_size": tier_size,
                "passed": tier_passed,
                "registry": str(tier_registry_path),
                "config": str(tier_config_path),
                "runner": runner_summary,
                "acceptance_passed": acceptance.get("passed"),
                "missing_artifacts": missing,
            }
        )

        metrics_rows.extend(
            summarize_metrics_for_tier(
                tier_size=tier_size,
                runner_summary=runner_summary,
            )
        )

    all_passed = (
        builder_summary.get("status") == "OK"
        and builder_summary.get("rq4_rebuilt_artifact_adapter") is True
        and full_chunk_count >= 800
        and all(result["passed"] for result in tier_results)
    )

    summary = {
        "schema": "HSRAG_RQ7_RQ4_SCALE_TIERS_V0_1",
        "status": "OK" if all_passed else "FAILED",
        "verify_id": verify_id,
        "run_started_at_utc": run_started_at_utc,
        "rq4_csv": str(rq4_csv_path),
        "full_registry": str(full_registry_path),
        "full_chunk_count": full_chunk_count,
        "requested_tiers": requested_tiers,
        "executed_tiers": tiers,
        "builder": builder_summary,
        "tier_results": tier_results,
        "all_passed": all_passed,
        "local_only": True,
        "zero_network": True,
        "zero_secret": True,
        "claim_boundary": {
            "rq4_rebuilt_artifact_connected": True,
            "scale_tier_runner": True,
            "full_scale_benchmark": False,
            "unit_derivation_is_heuristic": True,
            "legal_advice": False,
        },
    }

    summary_json = verify_dir / "rq7_rq4_scale_tier_summary.json"
    summary_csv = verify_dir / "rq7_rq4_scale_tier_summary.csv"
    summary_txt = verify_dir / "rq7_rq4_scale_tier_summary.txt"

    write_json(summary_json, summary)
    write_csv(summary_csv, metrics_rows)

    lines = [
        "HSRAG RQ7 RQ4 scale tier runner",
        "",
        f"status: {summary['status']}",
        f"verify_id: {verify_id}",
        f"rq4_csv: {rq4_csv_path}",
        f"full_chunk_count: {full_chunk_count}",
        f"executed_tiers: {', '.join(str(tier) for tier in tiers)}",
        f"all_passed: {all_passed}",
        "",
        "claim_boundary:",
        "- rq4_rebuilt_artifact_connected: true",
        "- scale_tier_runner: true",
        "- full_scale_benchmark: false",
        "- unit_derivation_is_heuristic: true",
        "- legal_advice: false",
        "",
        f"summary_json: {summary_json}",
        f"summary_csv: {summary_csv}",
    ]

    summary_txt.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
