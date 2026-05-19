from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

from hsrag_api_sqlite.db import connect_db, init_db
from hsrag_api_sqlite.ingest import ingest_api_spec, ingest_api_spec_file


def sample_payload() -> dict:
    sample_path = Path(__file__).resolve().parents[1] / "input" / "api_spec.example.json"
    return json.loads(sample_path.read_text(encoding="utf-8"))


def count_rows(db_path: Path, table_name: str) -> int:
    allowed = {"api_specs", "ingest_events", "guard_decisions", "audit_log"}
    if table_name not in allowed:
        raise ValueError("invalid table name")

    conn = connect_db(db_path)
    try:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    finally:
        conn.close()

    return int(row["count"])


def test_ingest_api_spec_creates_cthc_address(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    init_db(db_path)

    result = ingest_api_spec(sample_payload(), db_path=db_path)

    assert result.status == "ok"
    assert result.reason_code == "API_SPEC_INGESTED"
    assert result.data["endpoint_count"] == 2
    assert result.data["inserted_count"] == 2

    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            "SELECT cthc_address, cthc_hash, authority_hash, source_hash FROM api_specs"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 2
    assert all(row["cthc_address"].startswith("cthc://api/") for row in rows)
    assert all(row["cthc_hash"].startswith("sha256:") for row in rows)
    assert all(row["authority_hash"].startswith("sha256:") for row in rows)
    assert all(row["source_hash"].startswith("sha256:") for row in rows)


def test_ingest_api_spec_file_creates_records(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    sample_path = Path(__file__).resolve().parents[1] / "input" / "api_spec.example.json"

    result = ingest_api_spec_file(sample_path, db_path=db_path)

    assert result.status == "ok"
    assert count_rows(db_path, "api_specs") == 2


def test_reingest_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    payload = sample_payload()

    first = ingest_api_spec(payload, db_path=db_path)
    second = ingest_api_spec(payload, db_path=db_path)

    assert first.status == "ok"
    assert second.status == "ok"
    assert second.reason_code == "INGEST_IDEMPOTENT_ALREADY_EXISTS"
    assert second.data["idempotent_count"] == 2
    assert count_rows(db_path, "api_specs") == 2
    assert count_rows(db_path, "ingest_events") == 2
    assert count_rows(db_path, "audit_log") == 2


def test_same_cthc_hash_different_source_hash_creates_revision(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    original = sample_payload()
    changed = copy.deepcopy(original)
    changed["endpoints"][0]["responses"]["409"] = {
        "description": "Conflict."
    }

    first = ingest_api_spec(original, db_path=db_path)
    second = ingest_api_spec(changed, db_path=db_path)

    assert first.status == "ok"
    assert second.status == "ok"
    assert second.reason_code == "NEW_SPEC_REVISION_CREATED"
    assert second.data["revision_count"] == 1
    assert count_rows(db_path, "api_specs") == 3

    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT method, path, spec_revision, is_current, superseded_at_utc
            FROM api_specs
            WHERE method = ? AND path = ?
            ORDER BY spec_revision
            """,
            ("GET", "/users/{id}"),
        ).fetchall()
    finally:
        conn.close()

    assert [row["spec_revision"] for row in rows] == [1, 2]
    assert rows[0]["is_current"] == 0
    assert rows[0]["superseded_at_utc"] is not None
    assert rows[1]["is_current"] == 1


def test_import_time_is_utc_consistent(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    result = ingest_api_spec(sample_payload(), db_path=db_path)

    assert result.status == "ok"
    event_time = result.data["created_at_utc"]
    assert event_time.endswith("Z")

    conn = connect_db(db_path)
    try:
        api_times = {
            row["created_at_utc"]
            for row in conn.execute("SELECT created_at_utc FROM api_specs").fetchall()
        }
        ingest_times = {
            row["created_at_utc"]
            for row in conn.execute("SELECT created_at_utc FROM ingest_events").fetchall()
        }
        guard_times = {
            row["created_at_utc"]
            for row in conn.execute("SELECT created_at_utc FROM guard_decisions").fetchall()
        }
        audit_times = {
            row["created_at_utc"]
            for row in conn.execute("SELECT created_at_utc FROM audit_log").fetchall()
        }
    finally:
        conn.close()

    assert api_times == {event_time}
    assert ingest_times == {event_time}
    assert guard_times == {event_time}
    assert audit_times == {event_time}


def test_ingest_rejects_secret_like_input(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    init_db(db_path)

    payload = sample_payload()
    payload["authorization"] = "Bearer fake"

    result = ingest_api_spec(payload, db_path=db_path)

    assert result.status == "error"
    assert result.reason_code == "SECRET_LIKE_FIELD_REJECTED"
    assert count_rows(db_path, "api_specs") == 0


def test_ingest_records_guard_and_audit_logs(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"

    result = ingest_api_spec(sample_payload(), db_path=db_path)

    assert result.status == "ok"
    assert count_rows(db_path, "ingest_events") == 1
    assert count_rows(db_path, "guard_decisions") == 2
    assert count_rows(db_path, "audit_log") == 1


def test_ingest_uses_parameterized_sql_for_injection_like_path(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    payload = sample_payload()
    payload["endpoints"][0]["path"] = "/users/{id}'); DROP TABLE api_specs; --"

    result = ingest_api_spec(payload, db_path=db_path)

    assert result.status == "ok"

    conn = connect_db(db_path)
    try:
        table_exists = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = ? AND name = ?
            """,
            ("table", "api_specs"),
        ).fetchone()
    finally:
        conn.close()

    assert table_exists is not None
    assert count_rows(db_path, "api_specs") == 2


def test_invalid_json_file_returns_error(tmp_path: Path) -> None:
    db_path = tmp_path / "api_specs.sqlite3"
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")

    result = ingest_api_spec_file(bad_json, db_path=db_path)

    assert result.status == "error"
    assert result.reason_code == "INVALID_JSON_INPUT"
