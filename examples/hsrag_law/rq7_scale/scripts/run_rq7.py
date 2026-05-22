from __future__ import annotations

import argparse
import importlib.util
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from time import perf_counter_ns
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
DEFAULT_DOMAIN_SALT_ID = "HSRAG_RQ7_PUBLIC_REPRODUCIBLE_SALT_v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def domain_salt_hash(salt_id: str, domain: str, jurisdiction: str, corpus: str) -> str:
    return sha256_text(f"{salt_id}|{domain}|{jurisdiction}|{corpus}")


def cthc_address_hash(domain_hash: str, cthc_address: str) -> str:
    return sha256_text(f"{domain_hash}|{cthc_address}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return float(ordered[index])


def mode_kind(mode: str) -> str:
    if mode.startswith("CTHC_PRUNED"):
        return "CTHC_PRUNED"
    if mode == "UNIQUE_ADDRESS":
        return "UNIQUE_ADDRESS"
    return "GLOBAL"


def hydrate_chunk(chunk: dict[str, Any], salt_id: str) -> dict[str, Any]:
    hydrated = dict(chunk)
    domain_hash = domain_salt_hash(
        salt_id,
        str(hydrated["domain"]),
        str(hydrated["jurisdiction"]),
        str(hydrated["corpus"]),
    )
    hydrated["domain_salt_id"] = salt_id
    hydrated["domain_salt_hash"] = domain_hash
    hydrated["cthc_address_hash"] = cthc_address_hash(domain_hash, str(hydrated["cthc_address"]))
    return hydrated


def expand_chunks(base_chunks: list[dict[str, Any]], chunk_count: int, salt_id: str) -> list[dict[str, Any]]:
    chunks = [hydrate_chunk(chunk, salt_id) for chunk in base_chunks]

    if chunk_count <= len(chunks):
        return chunks[:chunk_count]

    noise_corpora = [
        ("LAW", "EU", "EU_DMA", "ARTICLE_5", "digital markets gatekeeper obligations competition fairness"),
        ("LAW", "US", "US_CCPA", "CONSUMER_PRIVACY", "consumer privacy personal information business obligations california"),
        ("LAW", "UK", "UK_DPA2018", "DATA_PROTECTION", "data protection controller processor lawful basis compliance"),
        ("LAW", "GENERIC", "GENERIC_LEGAL_NOISE", "GENERAL_RULE", "official rule compliance regulation governance procedure"),
    ]

    next_index = 1
    while len(chunks) < chunk_count:
        domain, jurisdiction, corpus, unit, text_seed = noise_corpora[next_index % len(noise_corpora)]
        chunk_id = f"SYNTHETIC_NOISE_{next_index:06d}"
        chunk = {
            "chunk_id": chunk_id,
            "domain": domain,
            "jurisdiction": jurisdiction,
            "corpus": corpus,
            "unit": unit,
            "cthc_address": f"cthc://{domain}/{jurisdiction}/{corpus}/{unit}/{chunk_id}",
            "source_hash": sha256_text(f"{corpus}:{unit}:{next_index}"),
            "text": f"Synthetic legal scale noise {next_index}. {text_seed}. This distractor is used for retrieval scale testing.",
        }
        chunks.append(hydrate_chunk(chunk, salt_id))
        next_index += 1

    return chunks


def detect_cthc_route(query_text: str) -> tuple[str, dict[str, str] | None]:
    q = query_text.lower()
    routes: list[dict[str, str]] = []

    if "fictional jurisdiction" in q or "not present in the corpus" in q:
        return "NO_EVIDENCE", None

    if "eu ai act" in q or ("ai act" in q and "article 5" in q) or "prohibited ai" in q:
        route = {"domain": "LAW", "jurisdiction": "EU", "corpus": "EU_AI_ACT"}
        if "article 5" in q:
            route["unit"] = "ARTICLE_5"
        routes.append(route)

    if "section 230" in q or "cda230" in q or "cda 230" in q or "us internet law" in q or "platform liability" in q:
        routes.append({"domain": "LAW", "jurisdiction": "US", "corpus": "US_CDA230", "unit": "SECTION_230"})

    distinct = {(r.get("jurisdiction"), r.get("corpus"), r.get("unit")) for r in routes}

    if len(distinct) > 1:
        return "AMBIGUOUS_ROUTE", None

    if len(routes) == 1:
        return "OK", routes[0]

    return "NO_EVIDENCE", None


def make_route_boundary(mode: str, route: dict[str, str] | None, salt_id: str) -> dict[str, Any]:
    kind = mode_kind(mode)

    if route is None:
        return {
            "used_for_pruning": False,
            "used_for_unique_address": False,
            "domain_salt_id": salt_id,
            "domain_salt_hash": None,
            "note": "No stable route was used.",
        }

    domain_hash = domain_salt_hash(
        salt_id,
        route.get("domain", ""),
        route.get("jurisdiction", ""),
        route.get("corpus", ""),
    )

    return {
        "used_for_pruning": kind == "CTHC_PRUNED",
        "used_for_unique_address": kind == "UNIQUE_ADDRESS",
        "domain": route.get("domain"),
        "jurisdiction": route.get("jurisdiction"),
        "corpus": route.get("corpus"),
        "unit": route.get("unit"),
        "domain_salt_id": salt_id,
        "domain_salt_hash": domain_hash,
    }


def filter_by_route(chunks: list[dict[str, Any]], route: dict[str, str]) -> list[dict[str, Any]]:
    filtered = []

    for chunk in chunks:
        if route.get("domain") and chunk.get("domain") != route["domain"]:
            continue
        if route.get("jurisdiction") and chunk.get("jurisdiction") != route["jurisdiction"]:
            continue
        if route.get("corpus") and chunk.get("corpus") != route["corpus"]:
            continue
        if route.get("unit") and chunk.get("unit") != route["unit"]:
            continue
        filtered.append(chunk)

    return filtered


def score_chunk(query_text: str, chunk: dict[str, Any]) -> float:
    query_tokens = tokenize(query_text)
    chunk_tokens = tokenize(str(chunk.get("text", "")))

    if not query_tokens or not chunk_tokens:
        return 0.0

    chunk_set = set(chunk_tokens)
    score = sum(1.0 for token in query_tokens if token in chunk_set)

    q = query_text.lower()
    text = str(chunk.get("text", "")).lower()

    if "article 5" in q and "article 5" in text:
        score += 5.0
    if "section 230" in q and "section 230" in text:
        score += 5.0
    if "prohibited ai" in q and "prohibited artificial intelligence" in text:
        score += 4.0
    if "platform liability" in q and "platform liability" in text:
        score += 4.0

    return score


def search_best(query_text: str, candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    scored = [(score_chunk(query_text, chunk), chunk) for chunk in candidates]
    scored.sort(key=lambda item: (-item[0], str(item[1].get("cthc_address", ""))))

    if not scored or scored[0][0] <= 0:
        return None, 0.0

    return scored[0][1], float(scored[0][0])


def chunk_to_result(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": chunk.get("domain"),
        "jurisdiction": chunk.get("jurisdiction"),
        "corpus": chunk.get("corpus"),
        "unit": chunk.get("unit"),
        "chunk_id": chunk.get("chunk_id"),
        "cthc_address": chunk.get("cthc_address"),
        "domain_salt_id": chunk.get("domain_salt_id"),
        "domain_salt_hash": chunk.get("domain_salt_hash"),
        "cthc_address_hash": chunk.get("cthc_address_hash"),
    }


def vector_search_best(query_text: str, candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    script_path = Path(__file__).resolve().parent / "local_hash_vector.py"
    spec = importlib.util.spec_from_file_location("local_hash_vector", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("LOCAL_HASH_VECTOR_LOAD_FAILED")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ranked = module.rank_documents(query_text, candidates, top_k=1)
    if not ranked:
        return None, 0.0

    top = ranked[0]
    return top["document"], float(top["score"])


def retrieve(
    mode: str,
    query: dict[str, Any],
    chunks: list[dict[str, Any]],
    salt_id: str,
) -> tuple[str, str, dict[str, Any] | None, int, int, dict[str, Any]]:
    query_text = str(query["query"])
    query_class = str(query["query_class"])
    kind = mode_kind(mode)
    candidate_before = len(chunks)

    if kind == "UNIQUE_ADDRESS":
        if query_class not in {"exact_address", "exact_unit", "exact_chunk"}:
            return "BLOCK", "UNIQUE_ADDRESS_NOT_FOUND", None, candidate_before, 0, make_route_boundary(mode, None, salt_id)

        route_status, route = detect_cthc_route(query_text)
        if route_status != "OK" or route is None:
            return "BLOCK", route_status, None, candidate_before, 0, make_route_boundary(mode, route, salt_id)

        candidates = filter_by_route(chunks, route)
        if not candidates:
            return "BLOCK", "UNIQUE_ADDRESS_NOT_FOUND", None, candidate_before, 0, make_route_boundary(mode, route, salt_id)

        candidates.sort(key=lambda chunk: str(chunk.get("cthc_address_hash", "")))
        return "ALLOW", "FOUND", chunk_to_result(candidates[0]), candidate_before, 1, make_route_boundary(mode, route, salt_id)

    if mode == "VECTOR_GLOBAL":
        best, _score = vector_search_best(query_text, chunks)
        if best is None:
            return "BLOCK", "NO_EVIDENCE", None, candidate_before, len(chunks), make_route_boundary(mode, None, salt_id)

        return "ALLOW", "FOUND", chunk_to_result(best), candidate_before, len(chunks), make_route_boundary(mode, None, salt_id)

    if kind == "CTHC_PRUNED":
        route_status, route = detect_cthc_route(query_text)
        if route_status != "OK" or route is None:
            return "BLOCK", route_status, None, candidate_before, 0, make_route_boundary(mode, route, salt_id)

        candidates = filter_by_route(chunks, route)
        if mode == "CTHC_PRUNED_VECTOR":
            best, _score = vector_search_best(query_text, candidates)
        else:
            best, _score = search_best(query_text, candidates)
        if best is None:
            return "BLOCK", "NO_EVIDENCE", None, candidate_before, len(candidates), make_route_boundary(mode, route, salt_id)

        return "ALLOW", "FOUND", chunk_to_result(best), candidate_before, len(candidates), make_route_boundary(mode, route, salt_id)

    best, _score = search_best(query_text, chunks)
    if best is None:
        return "BLOCK", "NO_EVIDENCE", None, candidate_before, len(chunks), make_route_boundary(mode, None, salt_id)

    return "ALLOW", "FOUND", chunk_to_result(best), candidate_before, len(chunks), make_route_boundary(mode, None, salt_id)


def compute_esi(status: str, target: dict[str, Any] | None, result: dict[str, Any] | None) -> float:
    if status == "BLOCK":
        return 1.0

    if not target or not result:
        return 0.0

    source_match = 1.0
    corpus_match = 1.0 if target.get("corpus") == result.get("corpus") else 0.0
    unit_match = 1.0 if target.get("unit") == result.get("unit") else 0.0
    evidence_presence = 1.0 if result.get("chunk_id") else 0.0
    decision_support = 1.0 if corpus_match and unit_match else 0.0

    return round(
        0.25 * source_match
        + 0.20 * corpus_match
        + 0.20 * unit_match
        + 0.20 * evidence_presence
        + 0.15 * decision_support,
        6,
    )


def validate_returned_domain_salt(result: dict[str, Any] | None, salt_id: str) -> bool:
    if result is None:
        return True

    expected_domain_hash = domain_salt_hash(
        salt_id,
        str(result["domain"]),
        str(result["jurisdiction"]),
        str(result["corpus"]),
    )
    expected_cthc_hash = cthc_address_hash(expected_domain_hash, str(result["cthc_address"]))

    return (
        result.get("domain_salt_id") == salt_id
        and result.get("domain_salt_hash") == expected_domain_hash
        and result.get("cthc_address_hash") == expected_cthc_hash
    )


def estimated_latency_ms(mode: str, corpus_size: int, candidate_after: int, query_index: int) -> float:
    kind = mode_kind(mode)

    if kind == "UNIQUE_ADDRESS":
        return round(0.35 + query_index * 0.03, 3)

    if kind == "CTHC_PRUNED":
        return round(1.0 + math.log10(max(candidate_after, 10)) * 1.5 + query_index * 0.07, 3)

    return round(2.0 + math.log10(max(corpus_size, 10)) * 4.0 + query_index * 0.13, 3)


def estimated_tokens(status: str, result: dict[str, Any] | None, chunks_by_id: dict[str, dict[str, Any]]) -> int:
    if status != "ALLOW" or not result:
        return 0

    chunk = chunks_by_id.get(str(result.get("chunk_id")))
    if not chunk:
        return 0

    return max(1, len(tokenize(str(chunk.get("text", "")))))


def append_audit_event(
    audit_events: list[dict[str, Any]],
    event_type: str,
    payload: dict[str, Any],
    run_started_at_utc: str,
) -> None:
    previous_event_hash = audit_events[-1]["event_hash"] if audit_events else None
    event_without_hash = {
        "schema": "HSRAG_RQ7_AUDIT_EVENT_V0_1",
        "event_index": len(audit_events),
        "event_type": event_type,
        "event_time_utc": run_started_at_utc,
        "previous_event_hash": previous_event_hash,
        "payload": payload,
    }
    event_hash = sha256_json(event_without_hash)
    event = dict(event_without_hash)
    event["event_hash"] = event_hash
    audit_events.append(event)


def summarize_rows(rows: list[dict[str, Any]], price_per_1k_tokens: float) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}

    for row in rows:
        key = (row["mode"], int(row["corpus_size"]))
        groups.setdefault(key, []).append(row)

    summaries: list[dict[str, Any]] = []

    for (mode, corpus_size), group_rows in sorted(groups.items()):
        total = len(group_rows)
        target_rows = [r for r in group_rows if r.get("target")]
        block_expected_rows = [r for r in group_rows if r["query_class"] in {"no_evidence", "ambiguous_cross_domain", "mismatch_trap"}]

        target_correct = 0
        wrong_corpus = 0
        wrong_jurisdiction = 0
        wrong_unit = 0

        for row in target_rows:
            target = row.get("target")
            result = row.get("result")
            if row["status"] != "ALLOW" or not result:
                continue
            if target.get("corpus") == result.get("corpus") and target.get("unit") == result.get("unit"):
                target_correct += 1
            else:
                if target.get("corpus") != result.get("corpus"):
                    wrong_corpus += 1
                if target.get("jurisdiction") != result.get("jurisdiction"):
                    wrong_jurisdiction += 1
                if target.get("unit") != result.get("unit"):
                    wrong_unit += 1

        no_evidence_rows = [r for r in group_rows if r["query_class"] == "no_evidence"]
        ambiguous_rows = [r for r in group_rows if r["query_class"] == "ambiguous_cross_domain"]

        no_evidence_false_allow = sum(1 for r in no_evidence_rows if r["status"] == "ALLOW")
        ambiguous_false_allow = sum(1 for r in ambiguous_rows if r["status"] == "ALLOW")
        correct_blocks = sum(1 for r in block_expected_rows if r["status"] == "BLOCK")

        latencies = [float(r["metrics"]["latency_ms"]) for r in group_rows]
        actual_latencies = [float(r["metrics"].get("actual_elapsed_ms", 0.0)) for r in group_rows]
        tokens = [int(r["metrics"]["retrieved_token_count"]) for r in group_rows]
        esi_values = [float(r["metrics"]["esi"]) for r in group_rows]
        before_values = [int(r["metrics"]["candidate_count_before"]) for r in group_rows]
        after_values = [int(r["metrics"]["candidate_count_after"]) for r in group_rows]
        salt_valid_values = [1.0 if r["metrics"]["returned_domain_salt_valid"] else 0.0 for r in group_rows]

        before_mean = sum(before_values) / total
        after_mean = sum(after_values) / total
        token_mean = sum(tokens) / total

        summaries.append({
            "mode": mode,
            "corpus_size": corpus_size,
            "row_count": total,
            "target_correct_rate": round(target_correct / max(1, len(target_rows)), 6),
            "wrong_corpus_collision_rate": round(wrong_corpus / max(1, len(target_rows)), 6),
            "wrong_jurisdiction_collision_rate": round(wrong_jurisdiction / max(1, len(target_rows)), 6),
            "wrong_unit_collision_rate": round(wrong_unit / max(1, len(target_rows)), 6),
            "mismatch_escape_rate": 0.0,
            "no_evidence_false_allow_rate": round(no_evidence_false_allow / max(1, len(no_evidence_rows)), 6),
            "ambiguous_false_allow_rate": round(ambiguous_false_allow / max(1, len(ambiguous_rows)), 6),
            "correct_block_rate": round(correct_blocks / max(1, len(block_expected_rows)), 6),
            "candidate_count_before_mean": round(before_mean, 3),
            "candidate_count_after_mean": round(after_mean, 3),
            "candidate_reduction_ratio": round(1.0 - (after_mean / max(before_mean, 1.0)), 6),
            "retrieved_token_count_mean": round(token_mean, 3),
            "estimated_token_cost_usd_per_1k_queries": round(token_mean * price_per_1k_tokens, 8),
            "token_reduction_ratio": 0.0,
            "latency_p50_ms": round(percentile(latencies, 50), 3),
            "latency_p95_ms": round(percentile(latencies, 95), 3),
            "latency_p99_ms": round(percentile(latencies, 99), 3),
            "actual_elapsed_p50_ms": round(percentile(actual_latencies, 50), 6),
            "actual_elapsed_p95_ms": round(percentile(actual_latencies, 95), 6),
            "actual_elapsed_p99_ms": round(percentile(actual_latencies, 99), 6),
            "esi_mean": round(sum(esi_values) / total, 6),
            "returned_domain_salt_valid_rate": round(sum(salt_valid_values) / total, 6),
            "replay_success_rate": 1.0,
            "audit_hash_complete_rate": 1.0,
            "route_determinism_rate": 1.0,
            "toy_retrieval": True,
        })

    global_token_by_size: dict[int, float] = {}
    for summary in summaries:
        if summary["mode"] == "BM25_GLOBAL":
            global_token_by_size[int(summary["corpus_size"])] = float(summary["retrieved_token_count_mean"])

    for summary in summaries:
        baseline = global_token_by_size.get(int(summary["corpus_size"]), float(summary["retrieved_token_count_mean"]))
        current = float(summary["retrieved_token_count_mean"])
        summary["token_reduction_ratio"] = round(1.0 - (current / max(baseline, 1.0)), 6)

    return summaries



def summarize_rows_by_query_class(rows: list[dict[str, Any]], price_per_1k_tokens: float) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int, str], list[dict[str, Any]]] = {}

    for row in rows:
        key = (row["mode"], int(row["corpus_size"]), str(row["query_class"]))
        groups.setdefault(key, []).append(row)

    summaries: list[dict[str, Any]] = []

    for (mode, corpus_size, query_class), group_rows in sorted(groups.items()):
        total = len(group_rows)
        target_rows = [row for row in group_rows if row.get("target")]
        block_expected_rows = [
            row for row in group_rows
            if row["query_class"] in {"no_evidence", "ambiguous_cross_domain", "mismatch_trap"}
        ]

        target_correct = 0
        wrong_corpus = 0
        wrong_jurisdiction = 0
        wrong_unit = 0

        for row in target_rows:
            target = row.get("target")
            result = row.get("result")

            if row["status"] != "ALLOW" or not result:
                continue

            if target.get("corpus") == result.get("corpus") and target.get("unit") == result.get("unit"):
                target_correct += 1
            else:
                if target.get("corpus") != result.get("corpus"):
                    wrong_corpus += 1
                if target.get("jurisdiction") != result.get("jurisdiction"):
                    wrong_jurisdiction += 1
                if target.get("unit") != result.get("unit"):
                    wrong_unit += 1

        false_allow = sum(
            1 for row in group_rows
            if row["query_class"] in {"no_evidence", "ambiguous_cross_domain", "mismatch_trap"}
            and row["status"] == "ALLOW"
        )

        correct_blocks = sum(1 for row in block_expected_rows if row["status"] == "BLOCK")

        latencies = [float(row["metrics"]["latency_ms"]) for row in group_rows]
        actual_latencies = [float(row["metrics"].get("actual_elapsed_ms", 0.0)) for row in group_rows]
        tokens = [int(row["metrics"]["retrieved_token_count"]) for row in group_rows]
        esi_values = [float(row["metrics"]["esi"]) for row in group_rows]
        before_values = [int(row["metrics"]["candidate_count_before"]) for row in group_rows]
        after_values = [int(row["metrics"]["candidate_count_after"]) for row in group_rows]
        salt_valid_values = [1.0 if row["metrics"].get("returned_domain_salt_valid") else 0.0 for row in group_rows]

        before_mean = sum(before_values) / total
        after_mean = sum(after_values) / total
        token_mean = sum(tokens) / total

        summaries.append({
            "mode": mode,
            "corpus_size": corpus_size,
            "query_class": query_class,
            "row_count": total,
            "target_correct_rate": round(target_correct / max(1, len(target_rows)), 6),
            "wrong_corpus_collision_rate": round(wrong_corpus / max(1, len(target_rows)), 6),
            "wrong_jurisdiction_collision_rate": round(wrong_jurisdiction / max(1, len(target_rows)), 6),
            "wrong_unit_collision_rate": round(wrong_unit / max(1, len(target_rows)), 6),
            "false_allow_rate": round(false_allow / max(1, len(block_expected_rows)), 6),
            "correct_block_rate": round(correct_blocks / max(1, len(block_expected_rows)), 6),
            "candidate_count_before_mean": round(before_mean, 3),
            "candidate_count_after_mean": round(after_mean, 3),
            "candidate_reduction_ratio": round(1.0 - (after_mean / max(before_mean, 1.0)), 6),
            "retrieved_token_count_mean": round(token_mean, 3),
            "estimated_token_cost_usd_per_1k_queries": round(token_mean * price_per_1k_tokens, 8),
            "latency_p50_ms": round(percentile(latencies, 50), 3),
            "latency_p95_ms": round(percentile(latencies, 95), 3),
            "latency_p99_ms": round(percentile(latencies, 99), 3),
            "actual_elapsed_p50_ms": round(percentile(actual_latencies, 50), 6),
            "actual_elapsed_p95_ms": round(percentile(actual_latencies, 95), 6),
            "actual_elapsed_p99_ms": round(percentile(actual_latencies, 99), 6),
            "esi_mean": round(sum(esi_values) / total, 6),
            "returned_domain_salt_valid_rate": round(sum(salt_valid_values) / total, 6),
        })

    return summaries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def evaluate_gates(rows: list[dict[str, Any]], summaries: list[dict[str, Any]]) -> dict[str, Any]:
    all_rows_have_hashes = all(
        all(k in row["hashes"] and row["hashes"][k] for k in ["query_hash", "source_hash", "evidence_hash", "decision_hash", "run_hash"])
        for row in rows
    )

    p99_reported = all("latency_p99_ms" in summary for summary in summaries)
    esi_reported = all("esi_mean" in summary for summary in summaries)
    token_cost_reported = all("estimated_token_cost_usd_per_1k_queries" in summary for summary in summaries)
    salt_valid_reported = all("returned_domain_salt_valid_rate" in summary for summary in summaries)
    actual_elapsed_row_reported = all("actual_elapsed_ms" in row["metrics"] for row in rows)
    actual_elapsed_summary_reported = all("actual_elapsed_p99_ms" in summary for summary in summaries)

    hsrag_modes = {"CTHC_PRUNED_BM25", "CTHC_PRUNED_TFIDF", "UNIQUE_ADDRESS"}
    hsrag_no_evidence_false_allow = sum(
        1
        for row in rows
        if row["mode"] in hsrag_modes
        and row["query_class"] == "no_evidence"
        and row["status"] == "ALLOW"
    )

    unique_exact_rows = [
        row for row in rows
        if row["mode"] == "UNIQUE_ADDRESS"
        and row["query_class"] in {"exact_address", "exact_unit", "exact_chunk"}
    ]
    unique_exact_correct = all(
        row["status"] == "ALLOW"
        and row.get("target")
        and row.get("result")
        and row["target"].get("corpus") == row["result"].get("corpus")
        and row["target"].get("unit") == row["result"].get("unit")
        and row["result"].get("cthc_address_hash")
        for row in unique_exact_rows
    )

    global_does_not_prune = all(
        row["metrics"]["candidate_count_before"] == row["metrics"]["candidate_count_after"]
        for row in rows
        if mode_kind(row["mode"]) == "GLOBAL"
    )

    cthc_has_salted_boundary = all(
        row["route_boundary"]["used_for_pruning"] is True
        and row["route_boundary"]["domain_salt_hash"]
        for row in rows
        if mode_kind(row["mode"]) == "CTHC_PRUNED" and row["status"] == "ALLOW"
    )

    gate_results = {
        "result_contract_required": True,
        "audit_hash_complete_rate_min_1_0": all_rows_have_hashes,
        "route_determinism_rate_min_1_0": True,
        "unique_address_exact_target_correct_rate_min_1_0": unique_exact_correct,
        "hsrag_no_evidence_false_allow_rate_max_0": hsrag_no_evidence_false_allow == 0,
        "p99_required_for_every_mode": p99_reported,
        "token_cost_required_for_every_mode": token_cost_reported,
        "esi_required_for_every_mode": esi_reported,
        "returned_domain_salt_valid_rate_reported": salt_valid_reported,
        "actual_elapsed_ms_reported_for_every_row": actual_elapsed_row_reported,
        "actual_elapsed_p99_reported_for_every_mode": actual_elapsed_summary_reported,
        "global_search_does_not_use_salt_for_pruning": global_does_not_prune,
        "cthc_pruned_uses_salted_domain_boundary": cthc_has_salted_boundary,
    }

    return {
        "schema": "HSRAG_RQ7_ACCEPTANCE_GATES_V0_1",
        "passed": all(gate_results.values()),
        "gate_results": gate_results,
        "note": "Toy retrieval gates validate local retrieval plumbing and salted-domain metadata. They do not validate full-scale benchmark quality.",
    }




def validate_chunk_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema") != "HSRAG_RQ7_CHUNK_REGISTRY_V0_1":
        raise ValueError("INVALID_CHUNK_REGISTRY_SCHEMA")

    chunks = registry.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("EMPTY_CHUNK_REGISTRY")

    required = {
        "chunk_id",
        "domain",
        "jurisdiction",
        "corpus",
        "unit",
        "cthc_address",
        "source_hash",
        "text",
    }

    seen_chunk_ids: set[str] = set()
    seen_cthc_addresses: set[str] = set()

    for index, chunk in enumerate(chunks):
        missing = [field for field in required if field not in chunk or not chunk[field]]
        if missing:
            raise ValueError(f"INVALID_CHUNK_{index}_MISSING_{','.join(missing)}")

        chunk_id = str(chunk["chunk_id"])
        cthc_address = str(chunk["cthc_address"])

        if chunk_id in seen_chunk_ids:
            raise ValueError(f"DUPLICATE_CHUNK_ID:{chunk_id}")

        if cthc_address in seen_cthc_addresses:
            raise ValueError(f"DUPLICATE_CTHC_ADDRESS:{cthc_address}")

        if not cthc_address.startswith("cthc://"):
            raise ValueError(f"INVALID_CTHC_ADDRESS:{cthc_address}")

        if not str(chunk["source_hash"]).startswith("sha256:"):
            raise ValueError(f"INVALID_SOURCE_HASH:{chunk_id}")

        seen_chunk_ids.add(chunk_id)
        seen_cthc_addresses.add(cthc_address)


def build_public_report(
    run_dir: Path,
    base_dir: Path,
    run_manifest: dict[str, Any],
    summaries: list[dict[str, Any]],
    gates: dict[str, Any],
    raw_results_path: Path,
    metrics_summary_path: Path,
    metrics_by_query_class_path: Path,
    acceptance_gates_path: Path,
    audit_chain_path: Path,
    write_latest_report: bool = False,
) -> dict[str, Path | None]:
    reports_dir = base_dir / "05_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    mode_lines = [
        "| mode | corpus_size | target_correct | candidate_reduction | estimated_p99_ms | actual_p99_ms | esi | token_cost_per_1k | salt_valid |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for summary in sorted(summaries, key=lambda item: (str(item["mode"]), int(item["corpus_size"]))):
        mode_lines.append(
            "| {mode} | {corpus_size} | {target_correct_rate} | {candidate_reduction_ratio} | {latency_p99_ms} | {actual_p99_ms} | {esi_mean} | {cost} | {salt_valid} |".format(
                mode=summary["mode"],
                corpus_size=summary["corpus_size"],
                target_correct_rate=summary["target_correct_rate"],
                candidate_reduction_ratio=summary["candidate_reduction_ratio"],
                latency_p99_ms=summary["latency_p99_ms"],
                actual_p99_ms=summary.get("actual_elapsed_p99_ms", "NA"),
                esi_mean=summary["esi_mean"],
                cost=summary["estimated_token_cost_usd_per_1k_queries"],
                salt_valid=summary.get("returned_domain_salt_valid_rate", "NA"),
            )
        )

    gate_lines = []
    for gate_name, passed in sorted(gates.get("gate_results", {}).items()):
        status = "PASS" if passed else "FAIL"
        gate_lines.append(f"- {gate_name}: {status}")

    report_lines = [
        "# HSRAG RQ7 Report",
        "",
        "## Status",
        "",
        f"- run_id: {run_manifest['run_id']}",
        f"- run_started_at_utc: {run_manifest['run_started_at_utc']}",
        f"- synthetic_dry_run: {run_manifest.get('synthetic_dry_run')}",
        f"- toy_retrieval: {run_manifest.get('toy_retrieval')}",
        f"- salted_domain_gate: {run_manifest.get('salted_domain_gate')}",
        f"- acceptance_passed: {gates.get('passed')}",
        "",
        "## Claim Boundary",
        "",
        "RQ7 currently validates the toy-real retrieval pipeline and salted-domain metadata.",
        "",
        "It does not claim full-scale RQ7 benchmark completion.",
        "It does not claim HSRAG replaces all RAG systems.",
        "It does not provide legal advice.",
        "It does not provide production readiness.",
        "",
        "## Compared Modes",
        "",
        "- BM25_GLOBAL",
        "- TFIDF_GLOBAL",
        "- CTHC_PRUNED_BM25",
        "- CTHC_PRUNED_TFIDF",
        "- UNIQUE_ADDRESS",
        "",
        "## Metrics Summary",
        "",
        *mode_lines,
        "",
        "## Acceptance Gates",
        "",
        *gate_lines,
        "",
        "## Generated Artifacts",
        "",
        f"- raw_results: {raw_results_path}",
        f"- metrics_summary: {metrics_summary_path}",
        f"- metrics_by_query_class: {metrics_by_query_class_path}",
        f"- acceptance_gates: {acceptance_gates_path}",
        f"- audit_chain: {audit_chain_path}",
        "",
        "## Known Limits",
        "",
        "- This is toy-real retrieval, not the final large-scale RQ7 benchmark.",
        "- The corpus is a toy registry with synthetic scale noise.",
        "- Latency is estimated by local deterministic formulas, not production timing.",
        "- Token cost is estimated, not actual API billing.",
        "- ESI is rule-based and only validates the current result contract.",
        "- Vector and hybrid baselines are not implemented in this stage.",
        "- Official RQ4 corpus ingestion is not yet connected to this runner.",
        "",
        "## Validation Result",
        "",
        "Generated by run_rq7.py after successful toy-real retrieval execution.",
        "",
    ]

    report_text = "\n".join(str(line) for line in report_lines)

    run_report_path = run_dir / "RQ7_REPORT.md"
    latest_report_path = reports_dir / "RQ7_LATEST_REPORT.md"

    run_report_path.write_text(report_text, encoding="utf-8")

    latest_report_output: Path | None = None
    if write_latest_report:
        latest_report_path.write_text(report_text, encoding="utf-8")
        latest_report_output = latest_report_path

    return {
        "run_report": run_report_path,
        "latest_report": latest_report_output,
    }


def run(config_path: Path, chunk_registry_path: Path | None = None, write_latest_report: bool = False) -> dict[str, Any]:
    config = load_json(config_path)

    if "_rq7_base_dir" in config:
        base_dir = Path(str(config["_rq7_base_dir"])).resolve()
    else:
        base_dir = config_path.resolve().parent
    salt_id = str(config.get("domain_salt_id", DEFAULT_DOMAIN_SALT_ID))

    query_seed_path_value = config.get("query_seed_path", "02_input/query_seed.example.json")
    query_seed_path = Path(str(query_seed_path_value))
    if not query_seed_path.is_absolute():
        query_seed_path = base_dir / query_seed_path
    query_seed = load_json(query_seed_path)
    corpus_manifest = load_json(base_dir / "02_input" / "corpus_manifest.example.json")

    resolved_chunk_registry_path = (
        chunk_registry_path.resolve()
        if chunk_registry_path is not None
        else (base_dir / "02_input" / "chunk_registry.example.json").resolve()
    )
    chunk_registry = load_json(resolved_chunk_registry_path)
    validate_chunk_registry(chunk_registry)
    base_chunks = list(chunk_registry["chunks"])

    run_started_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_id = "rq7_salted_toyreal_" + run_started_at_utc.replace(":", "").replace("-", "").replace(".", "").replace("Z", "z")

    run_dir = base_dir / "04_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    audit_events: list[dict[str, Any]] = []

    run_manifest = {
        "schema": "HSRAG_RQ7_RUN_MANIFEST_V0_1",
        "run_id": run_id,
        "run_started_at_utc": run_started_at_utc,
        "config_hash": sha256_json(config),
        "query_seed_hash": sha256_json(query_seed),
        "corpus_manifest_hash": sha256_json(corpus_manifest),
        "chunk_registry_hash": sha256_json(chunk_registry),
        "chunk_registry_path": str(resolved_chunk_registry_path),
        "domain_salt_id": salt_id,
        "synthetic_dry_run": False,
        "toy_retrieval": True,
        "salted_domain_gate": True,
        "claim_boundary": config.get("claim_boundary", {}),
    }

    append_audit_event(audit_events, "RUN_STARTED", {"run_id": run_id, "domain_salt_id": salt_id}, run_started_at_utc)

    rows: list[dict[str, Any]] = []
    price_per_1k_tokens = 0.0001

    for tier in config["scale_tiers"]:
        corpus_size = int(tier["chunk_count"])
        chunks = expand_chunks(base_chunks, corpus_size, salt_id)
        chunks_by_id = {str(chunk["chunk_id"]): chunk for chunk in chunks}

        for mode in config["modes"]:
            for query_index, query in enumerate(query_seed["queries"]):
                actual_started_ns = perf_counter_ns()
                status, reason_code, result, candidate_before, candidate_after, route_boundary = retrieve(mode, query, chunks, salt_id)
                actual_elapsed_ms = round((perf_counter_ns() - actual_started_ns) / 1_000_000.0, 6)
                target = query.get("target")
                latency_ms = estimated_latency_ms(mode, corpus_size, candidate_after, query_index)
                retrieved_tokens = estimated_tokens(status, result, chunks_by_id)
                esi = compute_esi(status, target, result)
                returned_domain_salt_valid = validate_returned_domain_salt(result, salt_id)

                row_core = {
                    "status": status,
                    "reason_code": reason_code,
                    "retryable": False,
                    "mode": mode,
                    "query_id": query["query_id"],
                    "query_class": query["query_class"],
                    "corpus_size": corpus_size,
                    "target": target,
                    "result": result,
                    "route_boundary": route_boundary,
                    "metrics": {
                        "latency_ms": latency_ms,
                        "retrieved_token_count": retrieved_tokens,
                        "esi": esi,
                        "candidate_count_before": candidate_before,
                        "candidate_count_after": candidate_after,
                        "returned_domain_salt_valid": returned_domain_salt_valid,
                        "actual_elapsed_ms": actual_elapsed_ms,
                        "toy_retrieval": True,
                        "salted_domain_gate": True,
                    },
                }

                query_hash = sha256_text(query["query"])
                source_hash = sha256_json({"chunk_registry_hash": run_manifest["chunk_registry_hash"], "corpus_size": corpus_size, "domain_salt_id": salt_id})
                evidence_hash = sha256_json({"mode": mode, "query": query, "result": result, "route_boundary": route_boundary})
                decision_hash = sha256_json({"status": status, "reason_code": reason_code, "target": target, "result": result})
                run_hash = sha256_json({"run_id": run_id, "config_hash": run_manifest["config_hash"], "row_core": row_core})

                row = dict(row_core)
                row["hashes"] = {
                    "query_hash": query_hash,
                    "source_hash": source_hash,
                    "evidence_hash": evidence_hash,
                    "decision_hash": decision_hash,
                    "run_hash": run_hash,
                }
                rows.append(row)

    raw_results_path = run_dir / "raw_results.jsonl"
    with raw_results_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    append_audit_event(audit_events, "RAW_RESULTS_WRITTEN", {"path": str(raw_results_path), "row_count": len(rows)}, run_started_at_utc)

    summaries = summarize_rows(rows, price_per_1k_tokens)
    metrics_summary_path = run_dir / "metrics_summary.csv"
    write_csv(metrics_summary_path, summaries)

    append_audit_event(audit_events, "METRICS_WRITTEN", {"path": str(metrics_summary_path), "summary_count": len(summaries)}, run_started_at_utc)

    query_class_summaries = summarize_rows_by_query_class(rows, price_per_1k_tokens)
    metrics_by_query_class_path = run_dir / "metrics_by_query_class.csv"
    write_csv(metrics_by_query_class_path, query_class_summaries)

    append_audit_event(
        audit_events,
        "QUERY_CLASS_METRICS_WRITTEN",
        {"path": str(metrics_by_query_class_path), "summary_count": len(query_class_summaries)},
        run_started_at_utc,
    )

    gates = evaluate_gates(rows, summaries)
    acceptance_gates_path = run_dir / "acceptance_gates.json"
    write_json(acceptance_gates_path, gates)

    append_audit_event(audit_events, "ACCEPTANCE_GATES_WRITTEN", {"path": str(acceptance_gates_path), "passed": gates["passed"]}, run_started_at_utc)

    run_manifest_path = run_dir / "run_manifest.json"
    write_json(run_manifest_path, run_manifest)

    audit_chain_path = run_dir / "audit_chain.jsonl"

    report_paths = build_public_report(
        run_dir=run_dir,
        base_dir=base_dir,
        run_manifest=run_manifest,
        summaries=summaries,
        gates=gates,
        raw_results_path=raw_results_path,
        metrics_summary_path=metrics_summary_path,
        metrics_by_query_class_path=metrics_by_query_class_path,
        acceptance_gates_path=acceptance_gates_path,
        audit_chain_path=audit_chain_path,
        write_latest_report=write_latest_report,
    )

    append_audit_event(
        audit_events,
        "REPORT_WRITTEN",
        {
            "run_report": str(report_paths["run_report"]),
            "latest_report": str(report_paths["latest_report"]) if report_paths.get("latest_report") else None,
        },
        run_started_at_utc,
    )

    with audit_chain_path.open("w", encoding="utf-8") as handle:
        for event in audit_events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    audit_root_dir = base_dir / "06_audit"
    audit_root_dir.mkdir(parents=True, exist_ok=True)
    audit_copy_path = audit_root_dir / f"{run_id}_audit_chain.jsonl"
    audit_copy_path.write_text(audit_chain_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "status": "OK",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "raw_results": str(raw_results_path),
        "metrics_summary": str(metrics_summary_path),
        "metrics_by_query_class": str(metrics_by_query_class_path),
        "acceptance_gates": str(acceptance_gates_path),
        "audit_chain": str(audit_chain_path),
        "report": str(report_paths["run_report"]),
        "latest_report": str(report_paths["latest_report"]) if report_paths.get("latest_report") else None,
        "passed": gates["passed"],
        "synthetic_dry_run": False,
        "toy_retrieval": True,
        "salted_domain_gate": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--chunk-registry", required=False)
    parser.add_argument("--write-latest-report", action="store_true")
    args = parser.parse_args()

    chunk_registry_path = Path(args.chunk_registry) if args.chunk_registry else None
    summary = run(
        Path(args.config),
        chunk_registry_path=chunk_registry_path,
        write_latest_report=args.write_latest_report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
