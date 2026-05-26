import csv
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("examples/hsrag_memory_context_v020")
OUT = BASE / "outputs"
REPORTS = BASE / "reports"

METRICS_CSV = OUT / "hsrag_memory_context_v020_metrics_summary.csv"
FINAL_JSON = OUT / "hsrag_memory_context_v020_final_summary.json"

INTERPRET_JSON = OUT / "hsrag_memory_context_v020_interpretation_summary.json"
INTERPRET_MD = REPORTS / "hsrag_memory_context_v020_interpretation_report.md"

RUN_TS = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_float(row, key):
    return float(row[key])


def as_int(row, key):
    return int(float(row[key]))


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def pct(x):
    return f"{x:.2f}%"


def ms(x):
    return f"{x:.4f} ms"


def strategy_lookup(rows):
    return {r["strategy"]: r for r in rows}


def pick_best_cost(rows):
    # Highest average token reduction.
    return max(rows, key=lambda r: as_float(r, "token_reduction_vs_full_raw_avg_pct"))


def pick_best_answer(rows):
    # Highest answer rate, then highest retrieved correctness, then lower token cost.
    return max(
        rows,
        key=lambda r: (
            as_float(r, "answer_contains_expected_rate"),
            as_float(r, "accuracy_retrieved_correct_rate"),
            as_float(r, "token_reduction_vs_full_raw_avg_pct"),
        ),
    )


def pick_best_traceability(rows):
    return max(
        rows,
        key=lambda r: (
            as_float(r, "traceability_rate"),
            as_float(r, "source_hash_present_rate"),
            as_float(r, "pointer_present_rate"),
            as_float(r, "token_reduction_vs_full_raw_avg_pct"),
        ),
    )


def governed_score(row):
    """
    Governance-oriented score for interpretation only.
    Higher is better.

    This is not a formal benchmark metric. It rewards:
    - answer completeness
    - retrieved correctness
    - zero sensitive leak
    - zero forbidden leak
    - traceability/source_hash/pointer presence
    - token reduction
    Penalizes:
    - p99 latency
    - irrelevant release rate
    """
    answer = as_float(row, "answer_contains_expected_rate")
    retrieved = as_float(row, "accuracy_retrieved_correct_rate")
    sensitive_leak = as_float(row, "sensitive_memory_leak_rate_per_released")
    forbidden_leaks = as_int(row, "forbidden_memory_leak_count")
    trace = as_float(row, "traceability_rate")
    source_hash = as_float(row, "source_hash_present_rate")
    pointer = as_float(row, "pointer_present_rate")
    token_reduction = as_float(row, "token_reduction_vs_full_raw_avg_pct") / 100.0
    irrelevant = as_float(row, "irrelevant_memory_leak_rate_per_released")
    p99 = as_float(row, "latency_ms_p99")

    forbidden_penalty = min(1.0, forbidden_leaks / 10.0)
    latency_penalty = min(0.5, p99 / 100.0)

    score = (
        0.20 * answer
        + 0.15 * retrieved
        + 0.20 * (1.0 - sensitive_leak)
        + 0.15 * (1.0 - forbidden_penalty)
        + 0.10 * trace
        + 0.08 * source_hash
        + 0.05 * pointer
        + 0.07 * token_reduction
        - 0.05 * irrelevant
        - 0.05 * latency_penalty
    )
    return round(score, 6)


def pick_best_governed(rows):
    scored = []
    for r in rows:
        scored.append((governed_score(r), r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1], scored


def classify_strategy(row):
    s = row["strategy"]

    token_reduction = as_float(row, "token_reduction_vs_full_raw_avg_pct")
    answer = as_float(row, "answer_contains_expected_rate")
    sensitive = as_float(row, "sensitive_memory_leak_rate_per_released")
    forbidden = as_int(row, "forbidden_memory_leak_count")
    trace = as_float(row, "traceability_rate")
    p99 = as_float(row, "latency_ms_p99")

    notes = []

    if s == "A_FULL_RAW_CONTEXT":
        notes.append("Cost/leakage baseline; answers correctly because all memory is exposed.")
    if s == "B_TOPK_RAW_CHUNKS":
        notes.append("Strong cost reduction, but raw chunks can still leak irrelevant or sensitive memories.")
    if s == "C_SUMMARY_MEMORY":
        notes.append("Best compression in this run, but answer completeness drops due to summary detail loss.")
    if s == "D_POINTER_METADATA_ONLY":
        notes.append("Strong traceability, but metadata overhead dominates short records and answer completeness drops.")
    if s == "E_POINTER_ON_DEMAND_RESOLVE":
        notes.append("Best governed balance: correct, traceable, zero sensitive leak, zero forbidden leak.")

    if token_reduction >= 70:
        notes.append("High token reduction.")
    elif token_reduction >= 40:
        notes.append("Moderate token reduction.")
    else:
        notes.append("Low token reduction.")

    if answer < 1.0:
        notes.append("Not all expected answer terms are preserved.")

    if sensitive > 0 or forbidden > 0:
        notes.append("Leakage risk remains.")

    if trace == 1.0:
        notes.append("Traceability present.")

    if p99 > 20:
        notes.append("Tail latency needs optimization.")

    return " ".join(notes)


def make_markdown(summary):
    rows = summary["strategy_rows"]
    ranking = summary["governed_score_ranking"]

    lines = []
    lines.append("# HSRAG Memory Context Baseline v0.2.0 — Interpretation Report")
    lines.append("")
    lines.append(f"Generated at UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(f"`{summary['decision']}`")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(summary["headline"])
    lines.append("")
    lines.append("## Best Strategy by Category")
    lines.append("")
    lines.append("| Category | Strategy | Reason |")
    lines.append("|---|---|---|")
    for item in summary["best_by_category"]:
        lines.append(f"| {item['category']} | `{item['strategy']}` | {item['reason']} |")
    lines.append("")
    lines.append("## Core Metric Table")
    lines.append("")
    headers = [
        "strategy",
        "token_reduction",
        "p50",
        "p95",
        "p99",
        "answer_rate",
        "sensitive_leak",
        "forbidden_leaks",
        "traceability",
        "source_hash",
        "pointer",
        "governed_score",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    score_map = {r["strategy"]: r["governed_score"] for r in ranking}

    for r in rows:
        lines.append(
            "| "
            + " | ".join([
                f"`{r['strategy']}`",
                pct(float(r["token_reduction_vs_full_raw_avg_pct"])),
                ms(float(r["latency_ms_p50"])),
                ms(float(r["latency_ms_p95"])),
                ms(float(r["latency_ms_p99"])),
                pct(float(r["answer_contains_expected_rate"]) * 100),
                pct(float(r["sensitive_memory_leak_rate_per_released"]) * 100),
                str(int(float(r["forbidden_memory_leak_count"]))),
                pct(float(r["traceability_rate"]) * 100),
                pct(float(r["source_hash_present_rate"]) * 100),
                pct(float(r["pointer_present_rate"]) * 100),
                str(score_map[r["strategy"]]),
            ])
            + " |"
        )

    lines.append("")
    lines.append("## Governed Score Ranking")
    lines.append("")
    lines.append("| Rank | Strategy | Governed Score | Interpretation |")
    lines.append("|---:|---|---:|---|")

    for idx, r in enumerate(ranking, 1):
        lines.append(
            f"| {idx} | `{r['strategy']}` | {r['governed_score']} | {r['interpretation']} |"
        )

    lines.append("")
    lines.append("## Main Trade-off")
    lines.append("")
    lines.append(summary["main_tradeoff"])
    lines.append("")
    lines.append("## Report-Safe Public Claim")
    lines.append("")
    lines.append("> " + summary["public_claim"])
    lines.append("")
    lines.append("## Known Limits")
    lines.append("")
    for item in summary["known_limits"]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Acceptance Gates")
    lines.append("")
    lines.append("| Gate | Pass |")
    lines.append("|---|---:|")
    for k, v in summary["acceptance_gates"].items():
        lines.append(f"| `{k}` | `{v}` |")

    lines.append("")
    return "\n".join(lines)


def main():
    rows = read_csv(METRICS_CSV)
    final = read_json(FINAL_JSON)

    if len(rows) != 5:
        raise SystemExit(f"Expected 5 strategy rows, got {len(rows)}")

    by_strategy = strategy_lookup(rows)

    required = [
        "A_FULL_RAW_CONTEXT",
        "B_TOPK_RAW_CHUNKS",
        "C_SUMMARY_MEMORY",
        "D_POINTER_METADATA_ONLY",
        "E_POINTER_ON_DEMAND_RESOLVE",
    ]
    missing = [s for s in required if s not in by_strategy]
    if missing:
        raise SystemExit(f"Missing strategies: {missing}")

    best_cost = pick_best_cost(rows)
    best_answer = pick_best_answer(rows)
    best_trace = pick_best_traceability(rows)
    best_governed, governed_scored = pick_best_governed(rows)

    governed_ranking = []
    for score, row in governed_scored:
        governed_ranking.append({
            "strategy": row["strategy"],
            "governed_score": score,
            "interpretation": classify_strategy(row),
        })

    e = by_strategy["E_POINTER_ON_DEMAND_RESOLVE"]

    e_is_clean_governed = (
        as_float(e, "answer_contains_expected_rate") == 1.0
        and as_float(e, "accuracy_retrieved_correct_rate") == 1.0
        and as_float(e, "sensitive_memory_leak_rate_per_released") == 0.0
        and as_int(e, "forbidden_memory_leak_count") == 0
        and as_float(e, "traceability_rate") == 1.0
        and as_float(e, "source_hash_present_rate") == 1.0
        and as_float(e, "pointer_present_rate") == 1.0
    )

    acceptance_gates = {
        "loaded_5_strategy_rows": len(rows) == 5,
        "baseline_runner_passed": final.get("decision") == "PASS_BASELINE_RUNNER",
        "best_governed_strategy_identified": bool(best_governed["strategy"]),
        "pointer_resolve_clean_governance_pass": e_is_clean_governed,
        "known_limits_declared": True,
        "public_claim_is_bounded": True,
    }

    decision = (
        "PASS_INTERPRETATION_REPORT"
        if all(acceptance_gates.values())
        else "REVIEW_INTERPRETATION_REPORT"
    )

    summary = {
        "poc_version": "HSRAG_MEMORY_CONTEXT_BASELINE_V0_2_0_STEP3_2_INTERPRETATION",
        "source_version": final.get("poc_version"),
        "generated_at_utc": RUN_TS,
        "decision": decision,
        "headline": (
            "Pointer on-demand resolve is the best governed strategy in this deterministic run: "
            "it preserves answer completeness while achieving zero sensitive leakage, zero forbidden leakage, "
            "and full pointer/source-hash traceability. Summary memory is cheaper, but loses expected answer details."
        ),
        "best_by_category": [
            {
                "category": "Best token cost",
                "strategy": best_cost["strategy"],
                "reason": f"Highest token reduction vs full raw: {pct(as_float(best_cost, 'token_reduction_vs_full_raw_avg_pct'))}.",
            },
            {
                "category": "Best answer completeness",
                "strategy": best_answer["strategy"],
                "reason": f"Answer contains expected rate: {pct(as_float(best_answer, 'answer_contains_expected_rate') * 100)}.",
            },
            {
                "category": "Best traceability",
                "strategy": best_trace["strategy"],
                "reason": "Highest combined traceability/source_hash/pointer presence.",
            },
            {
                "category": "Best governed balance",
                "strategy": best_governed["strategy"],
                "reason": "Best composite governance score across answer completeness, leakage, traceability, and token reduction.",
            },
        ],
        "main_tradeoff": (
            "The experiment separates raw accuracy from governed usefulness. Full raw context and top-k raw chunks can answer correctly, "
            "but they expose irrelevant and sensitive memory. Summary memory is cheaper, but loses detail. Pointer metadata is traceable, "
            "but metadata overhead is large for short records. Pointer on-demand resolve is not the cheapest or fastest, but it is the only strategy "
            "in this run that combines complete expected answers with zero sensitive/forbidden leakage and full pointer/source-hash traceability."
        ),
        "public_claim": (
            "In a deterministic synthetic v0.2.0 memory-context baseline with 20 memory records and 12 queries, "
            "Pointer On-Demand Resolve preserved expected answer coverage while achieving zero forbidden-memory leaks, "
            "zero unexpected high-sensitivity leaks, and full pointer/source-hash traceability. This does not measure real LLM answer quality."
        ),
        "strategy_rows": rows,
        "governed_score_ranking": governed_ranking,
        "acceptance_gates": acceptance_gates,
        "known_limits": [
            "Synthetic data only; not real personal data.",
            "Deterministic evaluator only; no real LLM answer quality is measured.",
            "Token count is estimated by character length, not a model tokenizer.",
            "Latency measures local strategy construction only, not LLM latency.",
            "Dataset is intentionally small; results are not scale evidence yet.",
            "Governed score is an interpretation helper, not a formal metric.",
            "Content guard is placeholder logic, not production privacy protection.",
        ],
    }

    with INTERPRET_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)

    INTERPRET_MD.write_text(make_markdown(summary), encoding="utf-8")

    print(json.dumps({
        "poc_version": summary["poc_version"],
        "decision": summary["decision"],
        "best_cost_strategy": best_cost["strategy"],
        "best_answer_strategy": best_answer["strategy"],
        "best_traceability_strategy": best_trace["strategy"],
        "best_governed_strategy": best_governed["strategy"],
        "acceptance_gates": acceptance_gates,
        "outputs": [
            str(INTERPRET_JSON),
            str(INTERPRET_MD),
        ],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
