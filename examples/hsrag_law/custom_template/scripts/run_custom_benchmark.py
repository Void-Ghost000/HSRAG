from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


BASE = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE / "output"

DEFAULT_CHUNKS_PATH = OUTPUT_DIR / "custom_chunks.csv"
DEFAULT_MANIFEST_PATH = OUTPUT_DIR / "custom_manifest.json"
DEFAULT_CASES = 200
DEFAULT_SEED = 20260505
DEFAULT_COST_PER_1K_TOKENS = 0.0001


@dataclass
class BenchmarkCase:
    case_id: str
    case_type: str
    query: str
    expected_decision: str
    expected_corpus_id: str
    expected_domain_hash: str


@dataclass
class RouteResult:
    decision: str
    reason: str
    detected_corpus_id: str
    detected_domain_hash: str
    retrieved_chunk_id: str
    retrieved_corpus_id: str
    retrieved_domain_hash: str
    score: float
    token_estimate: int
    latency_ms: float


@dataclass
class CaseRecord:
    case_id: str
    case_type: str
    query: str
    expected_decision: str
    expected_corpus_id: str
    expected_domain_hash: str
    decision: str
    reason: str
    detected_corpus_id: str
    detected_domain_hash: str
    retrieved_chunk_id: str
    retrieved_corpus_id: str
    retrieved_domain_hash: str
    score: float
    token_estimate: int
    latency_ms: float
    target_correct: bool
    false_allow: bool
    wrong_corpus_misrouting: bool
    wrong_domain_misrouting: bool


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload_hash: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_query(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9_§.\s-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    normalized = normalize_query(text)
    return [t for t in re.split(r"\s+", normalized) if len(t) >= 2]


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    idx = int(math.ceil(0.95 * len(values_sorted))) - 1
    idx = max(0, min(idx, len(values_sorted) - 1))
    return values_sorted[idx]


def build_index(chunks: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    by_corpus: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    by_domain_hash: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    known_corpus_ids = set()
    domain_by_corpus: Dict[str, str] = {}

    for row in chunks:
        corpus_id = row.get("corpus_id", "")
        domain_hash = row.get("domain_hash", "")

        if corpus_id:
            known_corpus_ids.add(corpus_id)
            by_corpus[corpus_id].append(row)

        if domain_hash:
            by_domain_hash[domain_hash].append(row)

        if corpus_id and domain_hash:
            domain_by_corpus[corpus_id] = domain_hash

    return {
        "by_corpus": by_corpus,
        "by_domain_hash": by_domain_hash,
        "known_corpus_ids": known_corpus_ids,
        "domain_by_corpus": domain_by_corpus,
    }


def detect_corpus_like_tokens(query: str) -> List[str]:
    normalized = query.upper()
    candidates = re.findall(r"[A-Z]+(?:_[A-Z0-9]+)+", normalized)
    return sorted(set(candidates))


def detect_known_corpora(query: str, known_corpus_ids: Sequence[str]) -> List[str]:
    upper = query.upper()
    found = []
    for corpus_id in known_corpus_ids:
        if corpus_id.upper() in upper:
            found.append(corpus_id)
    return sorted(set(found))


def is_conflict_form(query: str, known_hits: Sequence[str], corpus_like_tokens: Sequence[str]) -> bool:
    q = normalize_query(query)

    if len(set(known_hits)) >= 2:
        return True

    if len(set(corpus_like_tokens)) >= 2:
        return True

    conflict_words = ["compare", "versus", "vs", "between", "conflict", "contradiction"]
    if any(word in q.split() for word in conflict_words) and len(set(corpus_like_tokens)) >= 1:
        return True

    return False


def is_ambiguous_form(query: str) -> bool:
    q = normalize_query(query)

    ambiguous_patterns = [
        "the law",
        "this law",
        "that law",
        "legal rule",
        "the regulation",
        "this regulation",
        "what does it say",
        "what is required",
    ]

    return any(pattern in q for pattern in ambiguous_patterns)


def lexical_score(query: str, chunk_text: str) -> float:
    q_tokens = set(tokenize(query))
    c_tokens = set(tokenize(chunk_text))

    if not q_tokens or not c_tokens:
        return 0.0

    overlap = len(q_tokens & c_tokens)
    return overlap / max(1, len(q_tokens))


def route_query(query: str, chunks: Sequence[Dict[str, str]], index: Dict[str, Any]) -> RouteResult:
    started = time.perf_counter()

    known_corpus_ids = sorted(index["known_corpus_ids"])
    known_hits = detect_known_corpora(query, known_corpus_ids)
    corpus_like_tokens = detect_corpus_like_tokens(query)

    if is_conflict_form(query, known_hits, corpus_like_tokens):
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RouteResult(
            decision="BLOCK_CONFLICT_QUERY",
            reason="Conflict-form query detected before retrieval.",
            detected_corpus_id="|".join(known_hits),
            detected_domain_hash="",
            retrieved_chunk_id="",
            retrieved_corpus_id="",
            retrieved_domain_hash="",
            score=0.0,
            token_estimate=0,
            latency_ms=latency_ms,
        )

    if len(known_hits) == 0:
        if corpus_like_tokens:
            decision = "BLOCK_UNSUPPORTED_QUERY"
            reason = "Corpus-like identifier is not present in the custom corpus."
        elif is_ambiguous_form(query):
            decision = "BLOCK_AMBIGUOUS_QUERY"
            reason = "No stable custom corpus identifier found."
        else:
            decision = "BLOCK_UNSUPPORTED_QUERY"
            reason = "No supported custom corpus identifier found."

        latency_ms = (time.perf_counter() - started) * 1000.0
        return RouteResult(
            decision=decision,
            reason=reason,
            detected_corpus_id="",
            detected_domain_hash="",
            retrieved_chunk_id="",
            retrieved_corpus_id="",
            retrieved_domain_hash="",
            score=0.0,
            token_estimate=0,
            latency_ms=latency_ms,
        )

    detected_corpus_id = known_hits[0]
    detected_domain_hash = index["domain_by_corpus"].get(detected_corpus_id, "")

    candidates = index["by_corpus"].get(detected_corpus_id, [])

    best_row: Optional[Dict[str, str]] = None
    best_score = -1.0

    for row in candidates:
        score = lexical_score(query, row.get("text", ""))
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None:
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RouteResult(
            decision="BLOCK_NO_EVIDENCE",
            reason="Matched corpus has no retrievable chunks.",
            detected_corpus_id=detected_corpus_id,
            detected_domain_hash=detected_domain_hash,
            retrieved_chunk_id="",
            retrieved_corpus_id="",
            retrieved_domain_hash="",
            score=0.0,
            token_estimate=0,
            latency_ms=latency_ms,
        )

    retrieved_domain_hash = best_row.get("domain_hash", "")
    if retrieved_domain_hash != detected_domain_hash:
        latency_ms = (time.perf_counter() - started) * 1000.0
        return RouteResult(
            decision="BLOCK_DOMAIN_HASH_MISMATCH",
            reason="Detected domain hash does not match retrieved domain hash.",
            detected_corpus_id=detected_corpus_id,
            detected_domain_hash=detected_domain_hash,
            retrieved_chunk_id=best_row.get("chunk_id", ""),
            retrieved_corpus_id=best_row.get("corpus_id", ""),
            retrieved_domain_hash=retrieved_domain_hash,
            score=best_score,
            token_estimate=0,
            latency_ms=latency_ms,
        )

    latency_ms = (time.perf_counter() - started) * 1000.0
    return RouteResult(
        decision="ALLOW_WITH_EVIDENCE",
        reason="Query routed to a matched CTHC corpus and salted domain hash.",
        detected_corpus_id=detected_corpus_id,
        detected_domain_hash=detected_domain_hash,
        retrieved_chunk_id=best_row.get("chunk_id", ""),
        retrieved_corpus_id=best_row.get("corpus_id", ""),
        retrieved_domain_hash=retrieved_domain_hash,
        score=best_score,
        token_estimate=estimate_tokens(best_row.get("text", "")),
        latency_ms=latency_ms,
    )


def make_cases(chunks: Sequence[Dict[str, str]], cases: int) -> List[BenchmarkCase]:
    if not chunks:
        raise ValueError("No chunks available. Run build_custom_corpus.py first.")

    corpus_ids = sorted(set(row.get("corpus_id", "") for row in chunks if row.get("corpus_id", "")))
    if not corpus_ids:
        raise ValueError("No corpus_id found in custom_chunks.csv.")

    domain_by_corpus = {}
    title_by_corpus = {}

    for row in chunks:
        corpus_id = row.get("corpus_id", "")
        if corpus_id:
            domain_by_corpus[corpus_id] = row.get("domain_hash", "")
            title_by_corpus[corpus_id] = row.get("title", "Custom Legal Corpus")

    case_types = ["supported", "unsupported", "ambiguous", "conflict"]
    generated: List[BenchmarkCase] = []

    for i in range(cases):
        case_type = case_types[i % len(case_types)]
        corpus_id = corpus_ids[i % len(corpus_ids)]
        domain_hash = domain_by_corpus.get(corpus_id, "")
        title = title_by_corpus.get(corpus_id, "Custom Legal Corpus")

        if case_type == "supported":
            query = f"Under {corpus_id}, what does {title} say about purpose, routing, or evidence?"
            expected_decision = "ALLOW_WITH_EVIDENCE"
            expected_corpus_id = corpus_id
            expected_domain_hash = domain_hash

        elif case_type == "unsupported":
            query = "Under NON_EXISTENT_LAW_999, what rule is described?"
            expected_decision = "BLOCK_UNSUPPORTED_QUERY"
            expected_corpus_id = ""
            expected_domain_hash = ""

        elif case_type == "ambiguous":
            query = "What does the law say about evidence?"
            expected_decision = "BLOCK_AMBIGUOUS_QUERY"
            expected_corpus_id = ""
            expected_domain_hash = ""

        else:
            query = f"Compare {corpus_id} with NON_EXISTENT_LAW_999 and explain which one controls."
            expected_decision = "BLOCK_CONFLICT_QUERY"
            expected_corpus_id = ""
            expected_domain_hash = ""

        generated.append(
            BenchmarkCase(
                case_id=f"CUSTOM_CASE_{i + 1:06d}",
                case_type=case_type,
                query=query,
                expected_decision=expected_decision,
                expected_corpus_id=expected_corpus_id,
                expected_domain_hash=expected_domain_hash,
            )
        )

    return generated


def evaluate_case(case: BenchmarkCase, result: RouteResult) -> CaseRecord:
    allow = result.decision == "ALLOW_WITH_EVIDENCE"

    if case.case_type == "supported":
        target_correct = (
            allow
            and result.retrieved_corpus_id == case.expected_corpus_id
            and result.retrieved_domain_hash == case.expected_domain_hash
        )
        false_allow = False
        wrong_corpus_misrouting = allow and result.retrieved_corpus_id != case.expected_corpus_id
        wrong_domain_misrouting = allow and result.retrieved_domain_hash != case.expected_domain_hash
    else:
        target_correct = result.decision == case.expected_decision or result.decision.startswith("BLOCK_")
        false_allow = allow
        wrong_corpus_misrouting = False
        wrong_domain_misrouting = False

    return CaseRecord(
        case_id=case.case_id,
        case_type=case.case_type,
        query=case.query,
        expected_decision=case.expected_decision,
        expected_corpus_id=case.expected_corpus_id,
        expected_domain_hash=case.expected_domain_hash,
        decision=result.decision,
        reason=result.reason,
        detected_corpus_id=result.detected_corpus_id,
        detected_domain_hash=result.detected_domain_hash,
        retrieved_chunk_id=result.retrieved_chunk_id,
        retrieved_corpus_id=result.retrieved_corpus_id,
        retrieved_domain_hash=result.retrieved_domain_hash,
        score=result.score,
        token_estimate=result.token_estimate,
        latency_ms=result.latency_ms,
        target_correct=target_correct,
        false_allow=false_allow,
        wrong_corpus_misrouting=wrong_corpus_misrouting,
        wrong_domain_misrouting=wrong_domain_misrouting,
    )


def build_audit_chain(events_payloads: Sequence[tuple[str, Dict[str, Any]]]) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous = "GENESIS"

    for index, (event_type, payload) in enumerate(events_payloads):
        payload_hash = stable_json_hash(payload)
        event_seed = {
            "index": index,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "previous_hash": previous,
        }
        event_hash = stable_json_hash(event_seed)

        event = AuditEvent(
            index=index,
            event_type=event_type,
            payload_hash=payload_hash,
            payload=payload,
            previous_hash=previous,
            event_hash=event_hash,
        )
        events.append(event)
        previous = event_hash

    return events


def verify_audit_chain(events: Sequence[AuditEvent]) -> bool:
    previous = "GENESIS"

    for event in events:
        if event.previous_hash != previous:
            return False

        payload_hash = stable_json_hash(event.payload)
        if payload_hash != event.payload_hash:
            return False

        event_seed = {
            "index": event.index,
            "event_type": event.event_type,
            "payload_hash": event.payload_hash,
            "previous_hash": event.previous_hash,
        }

        if stable_json_hash(event_seed) != event.event_hash:
            return False

        previous = event.event_hash

    return True


def summarize(
    case_records: Sequence[CaseRecord],
    chunks: Sequence[Dict[str, str]],
    manifest: Dict[str, Any],
    cost_per_1k: float,
    audit_ok: bool,
) -> Dict[str, Any]:
    total_cases = len(case_records)
    supported = [r for r in case_records if r.case_type == "supported"]
    unsupported = [r for r in case_records if r.case_type == "unsupported"]
    ambiguous = [r for r in case_records if r.case_type == "ambiguous"]
    conflict = [r for r in case_records if r.case_type == "conflict"]

    supported_correct = sum(1 for r in supported if r.target_correct)
    wrong_corpus = sum(1 for r in supported if r.wrong_corpus_misrouting)
    wrong_domain = sum(1 for r in supported if r.wrong_domain_misrouting)

    unsupported_false_allow = sum(1 for r in unsupported if r.false_allow)
    ambiguous_false_allow = sum(1 for r in ambiguous if r.false_allow)
    conflict_false_allow = sum(1 for r in conflict if r.false_allow)

    total_tokens = sum(r.token_estimate for r in case_records)
    total_cost = (total_tokens / 1000.0) * cost_per_1k

    target_correct = supported_correct / len(supported) if supported else 0.0
    wrong_corpus_rate = wrong_corpus / len(supported) if supported else 0.0
    wrong_domain_rate = wrong_domain / len(supported) if supported else 0.0
    unsupported_false_allow_rate = unsupported_false_allow / len(unsupported) if unsupported else 0.0
    ambiguous_false_allow_rate = ambiguous_false_allow / len(ambiguous) if ambiguous else 0.0
    conflict_false_allow_rate = conflict_false_allow / len(conflict) if conflict else 0.0

    latencies = [r.latency_ms for r in case_records]
    p95_latency_ms = p95(latencies)

    decision = "CUSTOM_BENCHMARK_PASS"
    failures: List[str] = []

    if target_correct < 1.0:
        failures.append(f"TARGET_CORRECT expected=1.0 actual={target_correct}")
    if wrong_corpus_rate != 0.0:
        failures.append(f"WRONG_CORPUS_MISROUTING expected=0.0 actual={wrong_corpus_rate}")
    if wrong_domain_rate != 0.0:
        failures.append(f"WRONG_DOMAIN_MISROUTING expected=0.0 actual={wrong_domain_rate}")
    if unsupported_false_allow_rate != 0.0:
        failures.append(f"UNSUPPORTED_FALSE_ALLOW expected=0.0 actual={unsupported_false_allow_rate}")
    if ambiguous_false_allow_rate != 0.0:
        failures.append(f"AMBIGUOUS_FALSE_ALLOW expected=0.0 actual={ambiguous_false_allow_rate}")
    if conflict_false_allow_rate != 0.0:
        failures.append(f"CONFLICT_FALSE_ALLOW expected=0.0 actual={conflict_false_allow_rate}")
    if not audit_ok:
        failures.append("AUDIT_CHAIN expected=complete actual=incomplete")

    if failures:
        decision = "CUSTOM_BENCHMARK_FAIL"

    corpus_ids = sorted(set(row.get("corpus_id", "") for row in chunks if row.get("corpus_id", "")))
    domain_hashes = sorted(set(row.get("domain_hash", "") for row in chunks if row.get("domain_hash", "")))

    return {
        "name": "HSRAG_LAW_CUSTOM_BENCHMARK",
        "decision": decision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": total_cases,
        "corpus_count": len(corpus_ids),
        "corpora": corpus_ids,
        "domain_hash_count": len(domain_hashes),
        "chunk_count": len(chunks),
        "manifest_title": manifest.get("title", ""),
        "manifest_corpus_id": manifest.get("corpus_id", ""),
        "target_correct": target_correct,
        "wrong_corpus_misrouting": wrong_corpus_rate,
        "wrong_domain_misrouting": wrong_domain_rate,
        "unsupported_query_false_allow": unsupported_false_allow_rate,
        "ambiguous_query_false_allow": ambiguous_false_allow_rate,
        "conflict_query_false_allow": conflict_false_allow_rate,
        "p95_latency_ms": p95_latency_ms,
        "mean_latency_ms": statistics.mean(latencies) if latencies else 0.0,
        "total_tokens": total_tokens,
        "estimated_total_cost": total_cost,
        "audit_chain_complete": 1.0 if audit_ok else 0.0,
        "failures": failures,
    }


def write_outputs(summary: Dict[str, Any], case_records: Sequence[CaseRecord], audit_events: Sequence[AuditEvent]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    case_rows = [asdict(r) for r in case_records]

    write_csv(
        OUTPUT_DIR / "custom_benchmark_cases.csv",
        case_rows,
        [
            "case_id",
            "case_type",
            "query",
            "expected_decision",
            "expected_corpus_id",
            "expected_domain_hash",
            "decision",
            "reason",
            "detected_corpus_id",
            "detected_domain_hash",
            "retrieved_chunk_id",
            "retrieved_corpus_id",
            "retrieved_domain_hash",
            "score",
            "token_estimate",
            "latency_ms",
            "target_correct",
            "false_allow",
            "wrong_corpus_misrouting",
            "wrong_domain_misrouting",
        ],
    )

    gate_rows = [
        {
            "metric": "target_correct",
            "expected": "1.0",
            "actual": summary["target_correct"],
            "passed": summary["target_correct"] == 1.0,
        },
        {
            "metric": "wrong_corpus_misrouting",
            "expected": "0.0",
            "actual": summary["wrong_corpus_misrouting"],
            "passed": summary["wrong_corpus_misrouting"] == 0.0,
        },
        {
            "metric": "wrong_domain_misrouting",
            "expected": "0.0",
            "actual": summary["wrong_domain_misrouting"],
            "passed": summary["wrong_domain_misrouting"] == 0.0,
        },
        {
            "metric": "unsupported_query_false_allow",
            "expected": "0.0",
            "actual": summary["unsupported_query_false_allow"],
            "passed": summary["unsupported_query_false_allow"] == 0.0,
        },
        {
            "metric": "ambiguous_query_false_allow",
            "expected": "0.0",
            "actual": summary["ambiguous_query_false_allow"],
            "passed": summary["ambiguous_query_false_allow"] == 0.0,
        },
        {
            "metric": "conflict_query_false_allow",
            "expected": "0.0",
            "actual": summary["conflict_query_false_allow"],
            "passed": summary["conflict_query_false_allow"] == 0.0,
        },
        {
            "metric": "audit_chain_complete",
            "expected": "1.0",
            "actual": summary["audit_chain_complete"],
            "passed": summary["audit_chain_complete"] == 1.0,
        },
    ]

    write_csv(
        OUTPUT_DIR / "custom_benchmark_gate_checks.csv",
        gate_rows,
        ["metric", "expected", "actual", "passed"],
    )

    with (OUTPUT_DIR / "custom_benchmark_audit_chain.jsonl").open("w", encoding="utf-8") as f:
        for event in audit_events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")

    (OUTPUT_DIR / "custom_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# HSRAG LAW Custom Benchmark Summary",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        "## Scope",
        "",
        f"- cases: `{summary['cases']}`",
        f"- corpus_count: `{summary['corpus_count']}`",
        f"- chunk_count: `{summary['chunk_count']}`",
        f"- domain_hash_count: `{summary['domain_hash_count']}`",
        "",
        "## Metrics",
        "",
        f"- target_correct: `{summary['target_correct']}`",
        f"- wrong_corpus_misrouting: `{summary['wrong_corpus_misrouting']}`",
        f"- wrong_domain_misrouting: `{summary['wrong_domain_misrouting']}`",
        f"- unsupported_query_false_allow: `{summary['unsupported_query_false_allow']}`",
        f"- ambiguous_query_false_allow: `{summary['ambiguous_query_false_allow']}`",
        f"- conflict_query_false_allow: `{summary['conflict_query_false_allow']}`",
        f"- p95_latency_ms: `{summary['p95_latency_ms']}`",
        f"- total_tokens: `{summary['total_tokens']}`",
        f"- estimated_total_cost: `{summary['estimated_total_cost']}`",
        f"- audit_chain_complete: `{summary['audit_chain_complete']}`",
        "",
    ]

    if summary["failures"]:
        lines.append("## Failures")
        lines.append("")
        for failure in summary["failures"]:
            lines.append(f"- {failure}")
        lines.append("")

    (OUTPUT_DIR / "custom_benchmark_summary.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local HSRAG LAW custom corpus benchmark.")
    parser.add_argument("--chunks", default=str(DEFAULT_CHUNKS_PATH), help="Path to custom_chunks.csv.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Path to custom_manifest.json.")
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES, help="Number of benchmark cases.")
    parser.add_argument("--cost-per-1k", type=float, default=DEFAULT_COST_PER_1K_TOKENS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    chunks_path = Path(args.chunks)
    manifest_path = Path(args.manifest)

    chunks = read_csv_dicts(chunks_path)
    manifest = load_manifest(manifest_path)
    index = build_index(chunks)

    cases = make_cases(chunks, cases=args.cases)

    case_records: List[CaseRecord] = []
    for case in cases:
        result = route_query(case.query, chunks, index)
        case_records.append(evaluate_case(case, result))

    audit_events = build_audit_chain(
        [
            (
                "CUSTOM_BENCHMARK_CONFIG",
                {
                    "chunks_path": str(chunks_path),
                    "manifest_path": str(manifest_path),
                    "cases": args.cases,
                    "cost_per_1k": args.cost_per_1k,
                    "chunks_hash": stable_json_hash(chunks),
                    "manifest_hash": stable_json_hash(manifest),
                },
            ),
            (
                "CUSTOM_BENCHMARK_CASES",
                {
                    "case_count": len(cases),
                    "cases_hash": stable_json_hash([asdict(case) for case in cases]),
                },
            ),
            (
                "CUSTOM_BENCHMARK_RESULTS",
                {
                    "case_record_count": len(case_records),
                    "case_records_hash": stable_json_hash([asdict(record) for record in case_records]),
                },
            ),
        ]
    )

    audit_ok = verify_audit_chain(audit_events)

    summary = summarize(
        case_records=case_records,
        chunks=chunks,
        manifest=manifest,
        cost_per_1k=args.cost_per_1k,
        audit_ok=audit_ok,
    )

    write_outputs(summary, case_records, audit_events)

    print("=" * 80)
    print("HSRAG LAW — CUSTOM CORPUS BENCHMARK")
    print("=" * 80)
    print(f"decision: {summary['decision']}")
    print(f"cases: {summary['cases']}")
    print(f"corpus_count: {summary['corpus_count']}")
    print(f"chunk_count: {summary['chunk_count']}")
    print(f"domain_hash_count: {summary['domain_hash_count']}")
    print("")
    print("Metrics:")
    print(f"  target_correct: {summary['target_correct']}")
    print(f"  wrong_corpus_misrouting: {summary['wrong_corpus_misrouting']}")
    print(f"  wrong_domain_misrouting: {summary['wrong_domain_misrouting']}")
    print(f"  unsupported_query_false_allow: {summary['unsupported_query_false_allow']}")
    print(f"  ambiguous_query_false_allow: {summary['ambiguous_query_false_allow']}")
    print(f"  conflict_query_false_allow: {summary['conflict_query_false_allow']}")
    print(f"  p95_latency_ms: {summary['p95_latency_ms']}")
    print(f"  total_tokens: {summary['total_tokens']}")
    print(f"  estimated_total_cost: {summary['estimated_total_cost']}")
    print(f"  audit_chain_complete: {summary['audit_chain_complete']}")
    print("")

    if summary["failures"]:
        print("Failures:")
        for failure in summary["failures"]:
            print(f"  - {failure}")
        print("")

    print(f"results_dir: {OUTPUT_DIR}")
    print("=" * 80)

    return 0 if summary["decision"] == "CUSTOM_BENCHMARK_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())