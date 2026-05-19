from __future__ import annotations

import sqlite3

import pytest

from hsrag_api_sqlite.db import (
    EXPECTED_TABLES,
    SCHEMA_VERSION,
    connect_db,
    get_indexes,
    get_table_columns,
    init_db,
    list_tables,
)


def test_init_db_creates_tables(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    result = init_db(db_path)

    assert result.status == "ok"
    assert result.reason_code == "DB_SCHEMA_INITIALIZED"
    assert db_path.exists()

    conn = connect_db(db_path)
    try:
        tables = set(list_tables(conn))
    finally:
        conn.close()

    assert EXPECTED_TABLES.issubset(tables)


def test_init_db_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    first = init_db(db_path)
    second = init_db(db_path)

    assert first.status == "ok"
    assert second.status == "ok"
    assert first.reason_code == "DB_SCHEMA_INITIALIZED"
    assert second.reason_code == "DB_SCHEMA_INITIALIZED"


def test_init_db_supports_memory_database() -> None:
    result = init_db(":memory:")

    assert result.status == "ok"
    assert result.reason_code == "DB_SCHEMA_INITIALIZED"


def test_schema_meta_version_is_written(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = ?",
            ("schema_version",),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row["value"] == SCHEMA_VERSION


def test_api_specs_has_required_columns(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        columns = set(get_table_columns(conn, "api_specs"))
    finally:
        conn.close()

    required = {
        "id",
        "cthc_address",
        "cthc_hash",
        "authority_hash",
        "source_hash",
        "service_name",
        "api_version",
        "spec_revision",
        "method",
        "path",
        "summary",
        "parameters_json",
        "responses_json",
        "constraints_json",
        "evidence_class",
        "tacl_layer",
        "contract_role",
        "authority_rank",
        "source_type",
        "is_current",
        "created_at_utc",
        "updated_at_utc",
        "superseded_at_utc",
    }

    assert required.issubset(columns)


def test_audit_tables_have_required_columns(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        ingest_columns = set(get_table_columns(conn, "ingest_events"))
        guard_columns = set(get_table_columns(conn, "guard_decisions"))
        audit_columns = set(get_table_columns(conn, "audit_log"))
    finally:
        conn.close()

    assert {
        "event_hash",
        "input_hash",
        "status",
        "reason_code",
        "endpoint_count",
        "created_at_utc",
    }.issubset(ingest_columns)

    assert {
        "event_hash",
        "gate_name",
        "decision",
        "reason_code",
        "details_json",
        "created_at_utc",
    }.issubset(guard_columns)

    assert {
        "event_hash",
        "prev_event_hash",
        "event_type",
        "payload_hash",
        "created_at_utc",
    }.issubset(audit_columns)


def test_api_specs_indexes_are_created(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        indexes = get_indexes(conn, "api_specs")
    finally:
        conn.close()

    index_names = {item["name"] for item in indexes}

    assert "idx_api_specs_cthc_hash" in index_names
    assert "idx_api_specs_source_hash" in index_names
    assert "idx_api_specs_method_path" in index_names
    assert "idx_api_specs_service_version_method_path" in index_names
    assert any(item["unique"] for item in indexes)


def test_api_specs_constraints_reject_invalid_method(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO api_specs (
                    cthc_address,
                    cthc_hash,
                    authority_hash,
                    source_hash,
                    service_name,
                    api_version,
                    spec_revision,
                    method,
                    path,
                    summary,
                    parameters_json,
                    responses_json,
                    constraints_json,
                    evidence_class,
                    tacl_layer,
                    contract_role,
                    authority_rank,
                    source_type,
                    is_current,
                    created_at_utc,
                    updated_at_utc,
                    superseded_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "cthc://api/demo/v1/FETCH/users",
                    "sha256:cthc",
                    "sha256:authority",
                    "sha256:source",
                    "demo",
                    "v1",
                    1,
                    "FETCH",
                    "/users",
                    "bad method",
                    "{}",
                    "{}",
                    "{}",
                    "FHS",
                    "L0",
                    "core",
                    100,
                    "test",
                    1,
                    "2026-05-19T00:00:00Z",
                    "2026-05-19T00:00:00Z",
                    None,
                ),
            )
    finally:
        conn.close()


def test_table_name_helpers_reject_unknown_table(tmp_path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    result = init_db(db_path)
    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        with pytest.raises(ValueError):
            get_table_columns(conn, "api_specs; DROP TABLE api_specs")
        with pytest.raises(ValueError):
            get_indexes(conn, "api_specs; DROP TABLE api_specs")
    finally:
        conn.close()
