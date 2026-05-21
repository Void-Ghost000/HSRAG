from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def get_query_class(query: dict[str, Any]) -> str:
    return str(query.get("query_class") or query.get("case_type") or "")


def get_query_text(query: dict[str, Any]) -> str:
    for key in ("query", "text", "question", "prompt"):
        if key in query and query[key]:
            return str(query[key])
    return ""


def set_query_text(query: dict[str, Any], value: str) -> None:
    if "query" in query:
        query["query"] = value
    elif "text" in query:
        query["text"] = value
    elif "question" in query:
        query["question"] = value
    elif "prompt" in query:
        query["prompt"] = value
    else:
        query["query"] = value


def set_query_id(query: dict[str, Any], value: str) -> None:
    if "query_id" in query:
        query["query_id"] = value
    elif "case_id" in query:
        query["case_id"] = value
    elif "id" in query:
        query["id"] = value
    else:
        query["query_id"] = value


def set_query_class(query: dict[str, Any], value: str) -> None:
    query["query_class"] = value
    if "case_type" in query:
        query["case_type"] = value


def set_target(query: dict[str, Any], target: dict[str, Any] | None) -> None:
    if target:
        query["target"] = copy.deepcopy(target)
    else:
        query.pop("target", None)


def clone_variant(
    template: dict[str, Any],
    query_id: str,
    query_class: str,
    query_text: str,
    target: dict[str, Any] | None,
) -> dict[str, Any]:
    query = copy.deepcopy(template)
    set_query_id(query, query_id)
    set_query_class(query, query_class)
    set_query_text(query, query_text)
    set_target(query, target)
    query["rq7_full_expansion"] = True
    return query


def find_template(queries: list[dict[str, Any]], query_class: str) -> dict[str, Any] | None:
    for query in queries:
        if get_query_class(query) == query_class:
            return query
    return None


def first_target_template(queries: list[dict[str, Any]]) -> dict[str, Any]:
    for query in queries:
        if query.get("target"):
            return query
    if not queries:
        raise ValueError("EMPTY_BASE_QUERY_SEED")
    return queries[0]


def first_no_target_template(queries: list[dict[str, Any]]) -> dict[str, Any]:
    for query in queries:
        if not query.get("target"):
            return query
    return first_target_template(queries)


def build_full_seed(base_seed: dict[str, Any], min_added: int = 18) -> dict[str, Any]:
    base_queries = list(base_seed.get("queries", []))

    if not base_queries:
        raise ValueError("BASE_QUERY_SEED_HAS_NO_QUERIES")

    target_templates = [query for query in base_queries if query.get("target")]
    if not target_templates:
        target_templates = [first_target_template(base_queries)]

    exact_template = find_template(base_queries, "exact_unit") or first_target_template(base_queries)
    no_evidence_template = find_template(base_queries, "no_evidence") or first_no_target_template(base_queries)
    ambiguous_template = find_template(base_queries, "ambiguous_cross_domain") or first_no_target_template(base_queries)
    mismatch_template = find_template(base_queries, "mismatch_trap") or first_no_target_template(base_queries)

    added: list[dict[str, Any]] = []
    counter = 1

    for template in target_templates:
        target = copy.deepcopy(template.get("target") or {})
        corpus = str(target.get("corpus", "UNKNOWN_CORPUS"))
        unit = str(target.get("unit", "UNKNOWN_UNIT"))
        jurisdiction = str(target.get("jurisdiction", ""))

        target_texts = [
            ("exact_unit", f"{corpus} {unit}: identify the relevant rule and evidence."),
            ("exact_unit", f"What does {corpus} {unit} cover?"),
            ("typo_abbreviation", f"{corpus.replace('_', ' ')} {unit.replace('_', ' ')} pls summarize the legal point."),
            ("jurisdiction_distractor", f"Ignore unrelated jurisdiction hints and answer using {jurisdiction} {corpus} {unit}."),
        ]

        for query_class, text in target_texts:
            added.append(
                clone_variant(
                    exact_template,
                    f"rq7_full_target_{counter:04d}",
                    query_class,
                    text,
                    target,
                )
            )
            counter += 1

    no_target_variants = [
        (
            no_evidence_template,
            "no_evidence",
            "Does the Martian Neural Safety Act Article 999 require lunar model licensing?",
        ),
        (
            no_evidence_template,
            "no_evidence",
            "What does the Atlantis AI Liability Regulation say about underwater foundation models?",
        ),
        (
            ambiguous_template,
            "ambiguous_cross_domain",
            "Compare AI prohibitions, children privacy, and platform liability without specifying a jurisdiction or article.",
        ),
        (
            ambiguous_template,
            "ambiguous_cross_domain",
            "Tell me the legal rule across EU AI law and US internet law, but do not pick a specific source.",
        ),
        (
            mismatch_template,
            "mismatch_trap",
            "Under EU AI Act Article 5, what does 47 U.S.C. Section 230 require?",
        ),
        (
            mismatch_template,
            "mismatch_trap",
            "Under COPPA, explain EU AI Act prohibited AI practices as if they were the same corpus.",
        ),
    ]

    for template, query_class, text in no_target_variants:
        added.append(
            clone_variant(
                template,
                f"rq7_full_guard_{counter:04d}",
                query_class,
                text,
                None,
            )
        )
        counter += 1

    while len(added) < min_added:
        template = target_templates[len(added) % len(target_templates)]
        target = copy.deepcopy(template.get("target") or {})
        corpus = str(target.get("corpus", "UNKNOWN_CORPUS"))
        unit = str(target.get("unit", "UNKNOWN_UNIT"))
        added.append(
            clone_variant(
                exact_template,
                f"rq7_full_extra_{counter:04d}",
                "exact_unit",
                f"Retrieve the boundary-controlled evidence for {corpus} {unit}.",
                target,
            )
        )
        counter += 1

    output = copy.deepcopy(base_seed)
    output["schema"] = str(output.get("schema", "HSRAG_RQ7_QUERY_SEED_V0_1")) + "_FULL_EXPANSION"
    output["description"] = "RQ7 full benchmark expanded query seed. Built from query_seed.example.json."
    output["base_query_count"] = len(base_queries)
    output["added_query_count"] = len(added)
    output["query_count"] = len(base_queries) + len(added)
    output["claim_boundary"] = {
        "query_expansion_only": True,
        "full_scale_benchmark": False,
        "vector_hybrid_baselines": False,
    }
    output["queries"] = base_queries + added
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-seed", default="examples/hsrag_law/rq7_scale/02_input/query_seed.example.json")
    parser.add_argument("--output-seed", default="examples/hsrag_law/rq7_scale/02_input/query_seed.full.example.json")
    parser.add_argument("--base-config", default="examples/hsrag_law/rq7_scale/config.rq7.json")
    parser.add_argument("--output-config", default="examples/hsrag_law/rq7_scale/config.rq7.full_queries.json")
    args = parser.parse_args()

    base_seed_path = Path(args.base_seed)
    output_seed_path = Path(args.output_seed)
    base_config_path = Path(args.base_config)
    output_config_path = Path(args.output_config)

    base_seed = load_json(base_seed_path)
    full_seed = build_full_seed(base_seed)

    write_json(output_seed_path, full_seed)

    config = load_json(base_config_path)
    config["_rq7_base_dir"] = str(base_config_path.resolve().parent)
    config["query_seed_path"] = "02_input/query_seed.full.example.json"
    config["rq7_full_query_expansion"] = True

    write_json(output_config_path, config)

    print(
        json.dumps(
            {
                "status": "OK",
                "base_query_count": full_seed["base_query_count"],
                "added_query_count": full_seed["added_query_count"],
                "query_count": full_seed["query_count"],
                "output_seed": str(output_seed_path),
                "output_config": str(output_config_path),
                "query_seed_path": config["query_seed_path"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
