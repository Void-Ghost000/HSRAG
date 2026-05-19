from __future__ import annotations

import copy
import json
from pathlib import Path

from hsrag_api_sqlite.db import connect_db
from hsrag_api_sqlite.ingest import ingest_api_spec
from hsrag_api_sqlite.query import (
    history_by_cthc_hash,
    query_by_cthc_address,
    query_by_cthc_hash,
    query_by_method_path,
    semantic_discovery,
)


def sample_payload() -> dict:
    sample_path = Path(__file__).resolve().parents[1] / "input" / "api_spec.example.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


def ingest_sample(db_path: Path) -> dict:
    payload = sample_payload()
    result = ingest_api_spec(payload, db_path=db_path)
    assert result.status == "ok"
    return result.data


def first_get_user_record(db_path: Path) -> dict:
    conn = connect_db(db_path)
    try:
        row = conn.execute(
            """
            SELECT *
            FROM api_specs
            WHERE method = ? AND path = ? AND is_current = ?
            ORDER BY spec_revision DESC
            LIMIT 1
            """,
            ("GET", "/users/{id}", 1),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    return dict(row)


def test_query_by_cthc_hash_finds_current_fhs(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)
    record = first_get_user_record(db_path)

    result = query_by_cthc_hash(db_path, record["cthc_hash"])

    assert result.status == "found"
    assert result.reason_code == "CANONICAL_SPEC_FOUND_BY_CTHC_HASH"
    assert result.data["canonical_contract"]["evidence_class"] == "FHS"
    assert result.data["canonical_contract"]["is_current"] == 1


def test_query_by_cthc_address_finds_spec(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)
    record = first_get_user_record(db_path)

    result = query_by_cthc_address(db_path, record["cthc_address"])

    assert result.status == "found"
    assert result.reason_code == "CANONICAL_SPEC_FOUND_BY_CTHC_HASH"
    assert result.data["canonical_contract"]["path"] == "/users/{id}"


def test_query_by_method_path_with_service_version(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)

    result = query_by_method_path(
        db_path,
        method="GET",
        path="/users/{id}",
        service_name="demo-user-service",
        api_version="v1",
    )

    assert result.status == "found"
    assert result.reason_code == "API_SPEC_FOUND"
    assert result.data["canonical_contract"]["method"] == "GET"


def test_query_by_method_path_without_service_version_when_unique(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)

    result = query_by_method_path(
        db_path,
        method="POST",
        path="/users",
    )

    assert result.status == "found"
    assert result.reason_code == "API_SPEC_FOUND"
    assert result.data["canonical_contract"]["path"] == "/users"


def test_query_by_method_path_ambiguous_requires_pointer(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    first = sample_payload()
    second = copy.deepcopy(first)
    second["service_name"] = "other-user-service"

    ingest_api_spec(first, db_path=db_path)
    ingest_api_spec(second, db_path=db_path)

    result = query_by_method_path(
        db_path,
        method="GET",
        path="/users/{id}",
    )

    assert result.status == "blocked"
    assert result.reason_code == "AMBIGUOUS_API_SPEC_REQUIRES_CTHC_POINTER"


def test_query_by_cthc_hash_not_found() -> None:
    result = query_by_cthc_hash(
        ":memory:",
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )

    assert result.status == "not_found"
    assert result.reason_code == "SPEC_NOT_FOUND"


def test_query_by_cthc_hash_rejects_invalid_hash(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    result = query_by_cthc_hash(db_path, "not-a-hash")

    assert result.status == "error"
    assert result.reason_code == "INVALID_CTHC_HASH"


def test_query_by_cthc_address_rejects_invalid_address(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    result = query_by_cthc_address(db_path, "http://example.com")

    assert result.status == "error"
    assert result.reason_code == "INVALID_CTHC_ADDRESS"


def test_history_by_cthc_hash_returns_revisions(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    original = sample_payload()
    changed = copy.deepcopy(original)
    changed["endpoints"][0]["responses"]["409"] = {
        "description": "Conflict."
    }

    ingest_api_spec(original, db_path=db_path)
    ingest_api_spec(changed, db_path=db_path)

    record = first_get_user_record(db_path)

    result = history_by_cthc_hash(db_path, record["cthc_hash"])

    assert result.status == "found"
    assert result.reason_code == "SPEC_HISTORY_FOUND"

    revisions = [
        item["spec_revision"]
        for item in result.data["history"]
        if item["path"] == "/users/{id}"
    ]

    assert revisions == [1, 2]


def test_semantic_discovery_returns_candidates_only(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)

    result = semantic_discovery(db_path, "user")

    assert result.status == "found_with_warning"
    assert result.reason_code == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION"
    assert result.data["candidates"]


def test_semantic_discovery_not_found(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)

    result = semantic_discovery(db_path, "definitely-not-present")

    assert result.status == "not_found"
    assert result.reason_code == "SPEC_NOT_FOUND"


def test_result_contract_not_found_for_method_path(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    ingest_sample(db_path)

    result = query_by_method_path(
        db_path,
        method="DELETE",
        path="/users/{id}",
        service_name="demo-user-service",
        api_version="v1",
    )

    assert result.status == "not_found"
    assert result.reason_code == "SPEC_NOT_FOUND"
    assert result.retryable is False
    assert result.errors == []
