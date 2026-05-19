from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


if __package__ in (None, ""):
    SRC_ROOT = Path(__file__).resolve().parents[1]
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))


from hsrag_api_sqlite.ingest import ingest_api_spec, load_json_file
from hsrag_api_sqlite.query import (
    history_by_cthc_hash,
    query_by_cthc_hash,
    query_by_method_path,
    semantic_discovery,
)
from hsrag_api_sqlite.hashing import make_cthc_hash


def result_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "as_dict"):
        return result.as_dict()
    raise TypeError("expected Result-like object with as_dict()")


def build_revision_payload(payload: dict[str, Any]) -> dict[str, Any]:
    changed = json.loads(json.dumps(payload))
    changed["endpoints"][0]["responses"]["409"] = {
        "description": "Conflict."
    }
    return changed


def run_demo(input_path: Path, db_path: Path, reset: bool) -> dict[str, Any]:
    if reset and db_path.exists():
        db_path.unlink()

    payload = load_json_file(input_path)
    changed_payload = build_revision_payload(payload)

    first_ingest = ingest_api_spec(payload, db_path=db_path)
    second_ingest = ingest_api_spec(changed_payload, db_path=db_path)

    cthc_hash = make_cthc_hash(
        service_name=payload["service_name"],
        api_version=payload["api_version"],
        method=payload["endpoints"][0]["method"],
        path=payload["endpoints"][0]["path"],
    )

    method_path_query = query_by_method_path(
        db_path=db_path,
        method=payload["endpoints"][0]["method"],
        path=payload["endpoints"][0]["path"],
        service_name=payload["service_name"],
        api_version=payload["api_version"],
    )

    pointer_query = query_by_cthc_hash(
        db_path=db_path,
        cthc_hash=cthc_hash,
    )

    history_query = history_by_cthc_hash(
        db_path=db_path,
        cthc_hash=cthc_hash,
    )

    semantic_query = semantic_discovery(
        db_path=db_path,
        query_text="user",
    )

    return {
        "demo_name": "hsrag_api_sqlite_demo_v0_1",
        "scope": {
            "local_only": True,
            "zero_secret": True,
            "zero_network": True,
            "db_path": str(db_path),
            "input_path": str(input_path),
        },
        "cthc_pointer": {
            "cthc_hash": cthc_hash,
            "note": "CTHC hash identifies the API spec unit. Query still passes authority and evidence gates.",
        },
        "steps": {
            "first_ingest": result_to_dict(first_ingest),
            "second_ingest_revision": result_to_dict(second_ingest),
            "query_by_method_path": result_to_dict(method_path_query),
            "query_by_cthc_hash": result_to_dict(pointer_query),
            "history_by_cthc_hash": result_to_dict(history_query),
            "semantic_discovery": result_to_dict(semantic_query),
        },
        "interpretation": {
            "canonical_lookup": "Use cthc_hash or exact method/path plus service/version.",
            "semantic_discovery": "Discovery-only. It returns candidates and requires pointer confirmation.",
            "revision_rule": "Same CTHC hash plus different source hash creates a new spec_revision.",
        },
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Run the local HSRAG API SQLite demo."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root / "input" / "api_spec.example.json",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=project_root / "data" / "demo_api_specs.sqlite3",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=project_root / "data" / "demo_report.json",
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Do not delete the existing demo DB before running.",
    )

    args = parser.parse_args()

    report = run_demo(
        input_path=args.input,
        db_path=args.db,
        reset=not args.keep_db,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("")
    print(f"Demo report written to: {args.report}")
    print(f"Demo DB written to: {args.db}")


if __name__ == "__main__":
    main()
