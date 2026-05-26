from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE = Path("examples/hsrag_memory_context_v021_scale")
OUT = BASE / "outputs"
REPORTS = BASE / "reports"

FINAL_SUMMARY = OUT / "v021_scale_final_summary.json"
METRICS_CSV = OUT / "v021_scale_metrics_summary.csv"

FREEZE_MD = BASE / "V021_FREEZE_SUMMARY.md"
PUBLIC_MD = REPORTS / "v021_scale_public_summary.md"
FREEZE_JSON = OUT / "v021_freeze_summary.json"

POC_VERSION = "HSRAG_MEMORY_CONTEXT_SCALE_BASELINE_V0_2_1_FREEZE_SUMMARY"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    if not FINAL_SUMMARY.exists():
        raise FileNotFoundError(FINAL_SUMMARY)
    if not METRICS_CSV.exists():
        raise FileNotFoundError(METRICS_CSV)

    summary = load_json(FINAL_SUMMARY)
    metrics = load_csv(METRICS_CSV)

    failed = [
        name for name, value in summary["acceptance_gates"].items()
        if value is not True
    ]

    if summary["decision"] != "PASS_SCALE_BENCHMARK_RUNNER":
        raise SystemExit(f"Cannot freeze non-PASS result: {summary['decision']}")

    if failed:
        raise SystemExit(f"Cannot freeze with failed gates: {failed}")

    h = summary["highlight_100k_pointer_resolve"]

    metrics_100k = [
        row for row in metrics
        if int(row["n_memories"]) == 100000
    ]

    strategy_order = [
        "A_FULL_RAW_CONTEXT",
        "B_TOPK_RAW_CHUNKS",
        "C_SUMMARY_MEMORY",
        "D_POINTER_METADATA_ONLY",
        "E_POINTER_ON_DEMAND_RESOLVE",
    ]

    metrics_100k = sorted(
        metrics_100k,
        key=lambda row: strategy_order.index(row["strategy"])
    )

    freeze = {
        "poc_version": POC_VERSION,
        "decision": "FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE",
        "source_decision": summary["decision"],
        "created_at_utc": utc_now(),
        "scope": "synthetic_deterministic_memory_context_scale_benchmark",
        "n_list": summary["n_list"],
        "strategy_count": summary["strategy_count"],
        "result_row_count": summary["result_row_count"],
        "metric_row_count": summary["metric_row_count"],
        "highlight_100k_pointer_on_demand_resolve": {
            "token_reduction_vs_full_raw_avg_pct": h["token_reduction_vs_full_raw_avg_pct"],
            "latency_ms_p50": h["latency_ms_p50"],
            "latency_ms_p95": h["latency_ms_p95"],
            "latency_ms_p99": h["latency_ms_p99"],
            "answer_contains_expected_rate": h["answer_contains_expected_rate"],
            "sensitive_memory_leak_rate_avg": h["sensitive_memory_leak_rate_avg"],
            "traceability_rate": h["traceability_rate"],
            "context_tokens_avg": h["context_tokens_avg"],
            "memory_footprint_bytes_avg": h["memory_footprint_bytes_avg"],
        },
        "acceptance_gates": summary["acceptance_gates"],
        "claim_boundary": [
            "Synthetic deterministic benchmark only.",
            "No real LLM call.",
            "No real personal data.",
            "Latency measures local context construction only, not model inference.",
            "This does not prove GDPR compliance.",
            "Pointer on-demand resolve is evaluated as a context construction strategy, not as a full product."
        ],
        "known_limits": [
            "Exact memory hit is not optimized in v0.2.1.",
            "Dataset is synthetic and topic-structured.",
            "Evaluator checks deterministic answer coverage, not real model answer quality.",
            "Future work should add noisy query, semantic retrieval, real LLM evaluation, and exact-memory calibration."
        ],
        "next_steps": [
            "v0.2.2 exact-memory retrieval calibration.",
            "v0.2.3 noisy query / adversarial memory benchmark.",
            "v0.2.4 optional real LLM answer-quality evaluation.",
            "Later product line: local SQLite memory pointer SDK or VSCode/plugin wrapper."
        ],
    }

    write_json(FREEZE_JSON, freeze)

    freeze_lines: List[str] = []
    freeze_lines.append("# HSRAG Memory Context Scale Baseline v0.2.1 — Freeze Summary")
    freeze_lines.append("")
    freeze_lines.append("## Freeze Decision")
    freeze_lines.append("")
    freeze_lines.append("FREEZE_CONFIRMED_V0_2_1_SCALE_BASELINE")
    freeze_lines.append("")
    freeze_lines.append("## Scope")
    freeze_lines.append("")
    freeze_lines.append("Synthetic deterministic benchmark for comparing memory-context construction strategies.")
    freeze_lines.append("")
    freeze_lines.append("No real LLM call. No real personal data. No GDPR claim.")
    freeze_lines.append("")
    freeze_lines.append("## Strategies Compared")
    freeze_lines.append("")
    for strategy in strategy_order:
        freeze_lines.append(f"- {strategy}")
    freeze_lines.append("")
    freeze_lines.append("## Scale")
    freeze_lines.append("")
    freeze_lines.append("- 1,000 memories")
    freeze_lines.append("- 10,000 memories")
    freeze_lines.append("- 50,000 memories")
    freeze_lines.append("- 100,000 memories")
    freeze_lines.append("")
    freeze_lines.append("## 100k Highlight — E_POINTER_ON_DEMAND_RESOLVE")
    freeze_lines.append("")
    freeze_lines.append("| Metric | Value |")
    freeze_lines.append("|---|---:|")
    freeze_lines.append(f"| Token reduction vs full raw | {h['token_reduction_vs_full_raw_avg_pct']}% |")
    freeze_lines.append(f"| P50 local construction latency | {h['latency_ms_p50']} ms |")
    freeze_lines.append(f"| P95 local construction latency | {h['latency_ms_p95']} ms |")
    freeze_lines.append(f"| P99 local construction latency | {h['latency_ms_p99']} ms |")
    freeze_lines.append(f"| Answer coverage | {h['answer_contains_expected_rate']} |")
    freeze_lines.append(f"| Sensitive memory leak rate | {h['sensitive_memory_leak_rate_avg']} |")
    freeze_lines.append(f"| Traceability rate | {h['traceability_rate']} |")
    freeze_lines.append("")
    freeze_lines.append("## 100k Strategy Comparison")
    freeze_lines.append("")
    freeze_lines.append("| Strategy | Token reduction avg | P50 ms | P95 ms | P99 ms | Answer rate | Sensitive leak avg | Traceability |")
    freeze_lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")

    for row in metrics_100k:
        freeze_lines.append(
            f"| {row['strategy']} | "
            f"{row['token_reduction_vs_full_raw_avg_pct']}% | "
            f"{row['latency_ms_p50']} | "
            f"{row['latency_ms_p95']} | "
            f"{row['latency_ms_p99']} | "
            f"{row['answer_contains_expected_rate']} | "
            f"{row['sensitive_memory_leak_rate_avg']} | "
            f"{row['traceability_rate']} |"
        )

    freeze_lines.append("")
    freeze_lines.append("## Acceptance Gates")
    freeze_lines.append("")
    for name, value in summary["acceptance_gates"].items():
        freeze_lines.append(f"- {name}: {value}")
    freeze_lines.append("")
    freeze_lines.append("## Claim Boundary")
    freeze_lines.append("")
    for item in freeze["claim_boundary"]:
        freeze_lines.append(f"- {item}")
    freeze_lines.append("")
    freeze_lines.append("## Known Limits")
    freeze_lines.append("")
    for item in freeze["known_limits"]:
        freeze_lines.append(f"- {item}")
    freeze_lines.append("")
    freeze_lines.append("## Next Steps")
    freeze_lines.append("")
    for item in freeze["next_steps"]:
        freeze_lines.append(f"- {item}")
    freeze_lines.append("")

    FREEZE_MD.write_text("\n".join(freeze_lines), encoding="utf-8")

    public_lines: List[str] = []
    public_lines.append("# HSRAG Memory Context Baseline v0.2.1 — Public Summary")
    public_lines.append("")
    public_lines.append("This benchmark compares five ways to build memory context for an AI assistant, from full raw context stuffing to pointer-based on-demand resolve.")
    public_lines.append("")
    public_lines.append("The main question is simple:")
    public_lines.append("")
    public_lines.append("> Can a pointer-based memory context strategy remain small, fast, traceable, and safe at 100k synthetic memories?")
    public_lines.append("")
    public_lines.append("## Result")
    public_lines.append("")
    public_lines.append("At 100k synthetic memories, `E_POINTER_ON_DEMAND_RESOLVE` achieved:")
    public_lines.append("")
    public_lines.append(f"- {h['token_reduction_vs_full_raw_avg_pct']}% token reduction vs full raw context")
    public_lines.append(f"- P99 local context construction latency of {h['latency_ms_p99']} ms")
    public_lines.append(f"- answer coverage of {h['answer_contains_expected_rate']}")
    public_lines.append(f"- sensitive memory leak rate of {h['sensitive_memory_leak_rate_avg']}")
    public_lines.append(f"- traceability rate of {h['traceability_rate']}")
    public_lines.append("")
    public_lines.append("## What this does not claim")
    public_lines.append("")
    public_lines.append("- It does not call a real LLM.")
    public_lines.append("- It does not use real personal data.")
    public_lines.append("- It does not prove legal or GDPR compliance.")
    public_lines.append("- It measures local context construction, not model inference.")
    public_lines.append("")
    public_lines.append("## Why it matters")
    public_lines.append("")
    public_lines.append("The result suggests that memory systems can separate addressing, traceability, and selective disclosure instead of always stuffing raw memory into the model context.")
    public_lines.append("")

    PUBLIC_MD.write_text("\n".join(public_lines), encoding="utf-8")

    print(json.dumps({
        "decision": freeze["decision"],
        "source_decision": freeze["source_decision"],
        "freeze_json": str(FREEZE_JSON),
        "freeze_md": str(FREEZE_MD),
        "public_md": str(PUBLIC_MD),
        "highlight_100k_token_reduction": h["token_reduction_vs_full_raw_avg_pct"],
        "highlight_100k_acc": h["answer_contains_expected_rate"],
        "highlight_100k_sensitive_leak": h["sensitive_memory_leak_rate_avg"],
        "highlight_100k_traceability": h["traceability_rate"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
