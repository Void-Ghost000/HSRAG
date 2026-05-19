from __future__ import annotations

import json
from pathlib import Path

from hsrag_api_sqlite.db import connect_db
from hsrag_api_sqlite.ingest import ingest_api_spec_file
from hsrag_api_sqlite.query import (
    history_by_cthc_hash,
    query_by_cthc_hash,
    query_by_method_path,
    semantic_discovery,
)


def petstore_path() -> Path:
    return Path(__file__).resolve().parents[1] / "input" / "petstore_subset.api_spec.json"


def test_petstore_subset_json_is_valid_and_non_empty() -> None:
    raw = petstore_path().read_text(encoding="utf-8")

    assert raw.strip(), "input/petstore_subset.api_spec.json must not be empty"

    payload = json.loads(raw)

    assert payload["service_name"] == "petstore-demo"
    assert payload["api_version"] == "v1"
    assert payload["evidence_class"] == "FHS"
    assert payload["tacl_layer"] == "L0"
    assert payload["contract_role"] == "core"
    assert isinstance(payload["endpoints"], list)
    assert len(payload["endpoints"]) == 3


def test_ingest_petstore_subset_creates_three_specs(tmp_path: Path) -> None:
    db_path = tmp_path / "petstore.sqlite3"

    result = ingest_api_spec_file(petstore_path(), db_path=db_path)

    assert result.status == "ok"
    assert result.reason_code == "API_SPEC_INGESTED"
    assert result.data["endpoint_count"] == 3
    assert result.data["inserted_count"] == 3

    conn = connect_db(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM api_specs").fetchone()
    finally:
        conn.close()

    assert row["count"] == 3


def test_query_petstore_by_method_path(tmp_path: Path) -> None:
    db_path = tmp_path / "petstore.sqlite3"
    ingest_api_spec_file(petstore_path(), db_path=db_path)

    result = query_by_method_path(
        db_path,
        method="GET",
        path="/pet/{petId}",
        service_name="petstore-demo",
        api_version="v1",
    )

    assert result.status == "found"
    assert result.reason_code == "API_SPEC_FOUND"

    contract = result.data["canonical_contract"]

    assert contract["service_name"] == "petstore-demo"
    assert contract["method"] == "GET"
    assert contract["path"] == "/pet/{petId}"
    assert contract["evidence_class"] == "FHS"
    assert contract["tacl_layer"] == "L0"
    assert contract["contract_role"] == "core"


def test_query_petstore_by_cthc_hash(tmp_path: Path) -> None:
    db_path = tmp_path / "petstore.sqlite3"
    ingest_result = ingest_api_spec_file(petstore_path(), db_path=db_path)

    first_endpoint = ingest_result.data["endpoints"][0]
    cthc_hash = first_endpoint["cthc_hash"]

    result = query_by_cthc_hash(db_path, cthc_hash)

    assert result.status == "found"
    assert result.reason_code == "CANONICAL_SPEC_FOUND_BY_CTHC_HASH"
    assert result.data["canonical_contract"]["path"] == "/pet/{petId}"


def test_petstore_semantic_discovery_is_candidates_only(tmp_path: Path) -> None:
    db_path = tmp_path / "petstore.sqlite3"
    ingest_api_spec_file(petstore_path(), db_path=db_path)

    result = semantic_discovery(db_path, "pet")

    assert result.status == "found_with_warning"
    assert result.reason_code == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION"
    assert result.data["candidates"]
    assert result.warnings


def test_petstore_history_query_returns_single_revision(tmp_path: Path) -> None:
    db_path = tmp_path / "petstore.sqlite3"
    ingest_result = ingest_api_spec_file(petstore_path(), db_path=db_path)

    first_endpoint = ingest_result.data["endpoints"][0]
    cthc_hash = first_endpoint["cthc_hash"]

    result = history_by_cthc_hash(db_path, cthc_hash)

    assert result.status == "found"
    assert result.reason_code == "SPEC_HISTORY_FOUND"

    history = result.data["history"]

    assert len(history) == 1
    assert history[0]["spec_revision"] == 1
    assert history[0]["is_current"] == 1
