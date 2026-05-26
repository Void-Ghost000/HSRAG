from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

POC_VERSION = "HSRAG_MEMORY_CONTEXT_SCALE_V0_2_1_FAILURE_DIAGNOSIS"

BASE = Path("examples/hsrag_memory_context_v021_scale")
DATA = BASE / "data"
OUT = BASE / "outputs"
REPORTS = BASE / "reports"

RESULTS_CSV = OUT / "v021_scale_strategy_results.csv"
METRICS_CSV = OUT / "v021_scale_metrics_summary.csv"
QUERIES_100K = DATA / "queries_100000.jsonl"
MEMORIES_100K = DATA / "memory_items_100000.jsonl"

CASES_CSV = OUT / "v021_scale_failure_cases_100k_e_pointer_resolve.csv"
TOPIC_CSV = OUT / "v021_scale_failure_by_topic_100k_e_pointer_resolve.csv"
SUMMARY_JSON = OUT / "v021_scale_failure_diagnosis_summary.json"
REPORT_MD = REPORTS / "v021_scale_failure_diagnosis_report.md"

TARGET_N = 100000
TARGET_STRATEGY = "E_POINTER_ON_DEMAND_RESOLVE"

TOP_K_POINTER = 20
TOP_K_RESOLVE = 5


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def is_sensitive(item: Dict[str, Any]) -> bool:
    return item["tier"] == "FHS" or item["sensitivity"] == "high"


def resolved_context_for_topic(topic: str, memories_by_topic: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    ranked = memories_by_topic.get(topic, [])
    selected_before_guard = ranked[:TOP_K_POINTER]
    resolved = [item for item in selected_before_guard if not is_sensitive(item)][:TOP_K_RESOLVE]
    context_text = " ".join(item["text"] for item in resolved)

    return {
        "selected_before_guard_count": len(selected_before_guard),
        "resolved_count": len(resolved),
        "resolved_memory_ids": [item["memory_id"] for item in resolved],
        "resolved_context_text": context_text,
    }


def missing_terms(context_text: str, terms: List[str]) -> List[str]:
    lower = context_text.lower()
    return [term for term in terms if term.lower() not in lower]


def main() -> None:
    required = [RESULTS_CSV, METRICS_CSV, QUERIES_100K, MEMORIES_100K]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    results = load_csv(RESULTS_CSV)
    metrics = load_csv(METRICS_CSV)
    queries = load_jsonl(QUERIES_100K)
    memories = load_jsonl(MEMORIES_100K)

    queries_by_id = {row["query_id"]: row for row in queries}

    memories_by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in memories:
        memories_by_topic[item["topic"]].append(item)

    for topic in list(memories_by_topic.keys()):
        memories_by_topic[topic] = sorted(
            memories_by_topic[topic],
            key=lambda x: (x["source_hash"], x["memory_id"]),
        )

    e_rows = [
        row for row in results
        if int(row["n_memories"]) == TARGET_N and row["strategy"] == TARGET_STRATEGY
    ]

    e_failures = [
        row for row in e_rows
        if not parse_bool(row["answer_contains_expected"])
    ]

    case_rows: List[Dict[str, Any]] = []

    for row in e_failures:
        query = queries_by_id[row["query_id"]]
        topic = row["topic"]
        resolved_info = resolved_context_for_topic(topic, memories_by_topic)

        expected_terms = query["expected_answer_contains"]
        missing = missing_terms(resolved_info["resolved_context_text"], expected_terms)

        exact_hit = parse_bool(row["exact_memory_hit"])
        topic_hit = parse_bool(row["topic_hit"])

        if not topic_hit:
            reason = "TOPIC_ROUTING_FAILURE"
        elif not exact_hit:
            reason = "EXPECTED_MEMORY_NOT_SELECTED_BUT_TOPIC_CONTEXT_PRESENT"
        elif missing:
            reason = "EXPECTED_TERM_NOT_LITERAL_IN_RESOLVED_TEXT"
        else:
            reason = "UNKNOWN_EVALUATOR_MISMATCH"

        case_rows.append({
            "query_id": row["query_id"],
            "topic": topic,
            "strategy": TARGET_STRATEGY,
            "expected_terms": "|".join(expected_terms),
            "missing_terms": "|".join(missing),
            "exact_memory_hit": exact_hit,
            "topic_hit": topic_hit,
            "selected_count": row["selected_count"],
            "raw_release_count": row["raw_release_count"],
            "sensitive_memory_leak_rate": row["sensitive_memory_leak_rate"],
            "traceability_ok": row["traceability_ok"],
            "resolved_count": resolved_info["resolved_count"],
            "resolved_memory_ids": "|".join(resolved_info["resolved_memory_ids"]),
            "inferred_reason": reason,
        })

    by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_by_topic: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    for row in case_rows:
        by_topic[row["topic"]].append(row)

    for row in e_rows:
        all_by_topic[row["topic"]].append(row)

    strategy_topic_answer: Dict[str, Dict[str, float]] = {}

    for strategy in sorted(set(row["strategy"] for row in results)):
        strategy_topic_answer[strategy] = {}
        rows_for_strategy = [
            row for row in results
            if int(row["n_memories"]) == TARGET_N and row["strategy"] == strategy
        ]

        grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        for row in rows_for_strategy:
            grouped[row["topic"]].append(row)

        for topic, rows in grouped.items():
            strategy_topic_answer[strategy][topic] = round(
                sum(1.0 if parse_bool(row["answer_contains_expected"]) else 0.0 for row in rows) / len(rows),
                6,
            )

    topic_rows: List[Dict[str, Any]] = []

    for topic, failures in sorted(by_topic.items(), key=lambda kv: len(kv[1]), reverse=True):
        total_rows = all_by_topic[topic]
        total_count = len(total_rows)
        failure_count = len(failures)
        answer_rate = 0.0 if total_count == 0 else round((total_count - failure_count) / total_count, 6)

        missing_counter: Dict[str, int] = defaultdict(int)
        reason_counter: Dict[str, int] = defaultdict(int)

        for failure in failures:
            for term in str(failure["missing_terms"]).split("|"):
                if term:
                    missing_counter[term] += 1
            reason_counter[failure["inferred_reason"]] += 1

        top_missing = sorted(missing_counter.items(), key=lambda kv: kv[1], reverse=True)
        top_reasons = sorted(reason_counter.items(), key=lambda kv: kv[1], reverse=True)

        topic_rows.append({
            "topic": topic,
            "total_count": total_count,
            "failure_count": failure_count,
            "answer_rate": answer_rate,
            "top_missing_terms": json.dumps(dict(top_missing), ensure_ascii=False, sort_keys=True),
            "top_inferred_reasons": json.dumps(dict(top_reasons), ensure_ascii=False, sort_keys=True),
            "A_answer_rate": strategy_topic_answer.get("A_FULL_RAW_CONTEXT", {}).get(topic),
            "B_answer_rate": strategy_topic_answer.get("B_TOPK_RAW_CHUNKS", {}).get(topic),
            "C_answer_rate": strategy_topic_answer.get("C_SUMMARY_MEMORY", {}).get(topic),
            "D_answer_rate": strategy_topic_answer.get("D_POINTER_METADATA_ONLY", {}).get(topic),
            "E_answer_rate": strategy_topic_answer.get("E_POINTER_ON_DEMAND_RESOLVE", {}).get(topic),
        })

    metrics_100k = [
        row for row in metrics
        if int(row["n_memories"]) == TARGET_N
    ]

    e_metric = [
        row for row in metrics_100k
        if row["strategy"] == TARGET_STRATEGY
    ][0]

    if topic_rows:
        top_fail_topic = topic_rows[0]["topic"]
        top_fail_count = topic_rows[0]["failure_count"]
        top_missing_terms = topic_rows[0]["top_missing_terms"]
        top_reasons = topic_rows[0]["top_inferred_reasons"]
    else:
        top_fail_topic = None
        top_fail_count = 0
        top_missing_terms = "{}"
        top_reasons = "{}"

    if top_fail_topic == "audit_chain" and "traceability" in top_missing_terms:
        likely_root_cause = "SYNTHETIC_EXPECTED_TERM_MISMATCH_SUMMARY_VS_RAW_TEXT"
        recommended_fix = "Align audit_chain raw text with expected term traceability, or include summary metadata in E resolved context. Do not lower the gate."
    elif topic_rows:
        likely_root_cause = "E_POINTER_RESOLVE_ANSWER_COVERAGE_FAILURE_LOCALIZED"
        recommended_fix = "Inspect failed topic text, expected terms, and E resolve payload before changing gates."
    else:
        likely_root_cause = "NO_E_FAILURE_FOUND"
        recommended_fix = "No E failure found. Recheck prior summary."

    gates = {
        "results_csv_present": RESULTS_CSV.exists(),
        "metrics_csv_present": METRICS_CSV.exists(),
        "e_100k_rows_present": len(e_rows) == 100,
        "e_100k_failures_identified": len(e_failures) > 0,
        "failure_topic_breakdown_present": len(topic_rows) > 0,
        "case_rows_written": True,
        "topic_rows_written": True,
    }

    decision = "PASS_FAILURE_DIAGNOSIS" if all(gates.values()) else "REVIEW_FAILURE_DIAGNOSIS"

    summary = {
        "poc_version": POC_VERSION,
        "decision": decision,
        "scope": "diagnose_100k_E_pointer_on_demand_resolve_answer_coverage_failure",
        "target_n": TARGET_N,
        "target_strategy": TARGET_STRATEGY,
        "e_100k_total_rows": len(e_rows),
        "e_100k_failure_count": len(e_failures),
        "e_100k_answer_rate": float(e_metric["answer_contains_expected_rate"]),
        "e_100k_sensitive_leak_rate": float(e_metric["sensitive_memory_leak_rate_avg"]),
        "e_100k_traceability_rate": float(e_metric["traceability_rate"]),
        "top_fail_topic": top_fail_topic,
        "top_fail_count": top_fail_count,
        "top_missing_terms": top_missing_terms,
        "top_inferred_reasons": top_reasons,
        "likely_root_cause": likely_root_cause,
        "recommended_fix": recommended_fix,
        "acceptance_gates": gates,
        "outputs": [
            str(CASES_CSV),
            str(TOPIC_CSV),
            str(SUMMARY_JSON),
            str(REPORT_MD),
        ],
        "warnings": [
            "Diagnosis only; no benchmark gate was changed.",
            "Synthetic deterministic evaluator only.",
            "Do not claim PASS_SCALE_BENCHMARK until Step 9 is rerun after fix."
        ],
    }

    write_csv(CASES_CSV, case_rows)
    write_csv(TOPIC_CSV, topic_rows)
    write_json(SUMMARY_JSON, summary)

    lines = [
        "# v0.2.1 Scale Benchmark Failure Diagnosis",
        "",
        f"Decision: {decision}",
        "",
        "## Target",
        "",
        f"- N: {TARGET_N}",
        f"- Strategy: {TARGET_STRATEGY}",
        "",
        "## Main Finding",
        "",
        f"- E 100k answer rate: {summary['e_100k_answer_rate']}",
        f"- E 100k failure count: {summary['e_100k_failure_count']}",
        f"- Top fail topic: {top_fail_topic}",
        f"- Top fail count: {top_fail_count}",
        f"- Likely root cause: {likely_root_cause}",
        "",
        "## Recommendation",
        "",
        recommended_fix,
        "",
        "## Boundary",
        "",
        "- Diagnosis only.",
        "- No acceptance gate was lowered.",
        "- Rerun Step 9 after applying a fix.",
    ]

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    if decision != "PASS_FAILURE_DIAGNOSIS":
        raise SystemExit("Failure diagnosis did not pass all diagnosis gates.")


if __name__ == "__main__":
    main()
