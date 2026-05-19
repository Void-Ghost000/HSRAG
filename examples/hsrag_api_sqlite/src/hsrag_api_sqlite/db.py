from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from hsrag_api_sqlite.contracts import Result, error_result, ok_result


SCHEMA_VERSION = "0.1.0"

EXPECTED_TABLES = {
    "schema_meta",
    "api_specs",
    "ingest_events",
    "guard_decisions",
    "audit_log",
}


def connect_db(db_path: str | Path = ":memory:") -> sqlite3.Connection:
    if str(db_path) != ":memory:":
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
    else:
        conn = sqlite3.connect(":memory:")

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = ":memory:") -> Result:
    try:
        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            tables = list_tables(conn)
            missing = sorted(EXPECTED_TABLES - set(tables))

            if missing:
                return error_result(
                    "DB_SCHEMA_INCOMPLETE",
                    [f"missing tables: {missing}"],
                )

            return ok_result(
                "DB_SCHEMA_INITIALIZED",
                {
                    "schema_version": SCHEMA_VERSION,
                    "tables": sorted(tables),
                    "db_path": str(db_path),
                },
            )
        finally:
            conn.close()

    except sqlite3.Error as exc:
        return error_result("SQLITE_INIT_FAILED", [str(exc)])
    except OSError as exc:
        return error_result("DB_PATH_ERROR", [str(exc)])


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS api_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            cthc_address TEXT NOT NULL,
            cthc_hash TEXT NOT NULL,
            authority_hash TEXT NOT NULL,
            source_hash TEXT NOT NULL,

            service_name TEXT NOT NULL,
            api_version TEXT NOT NULL,
            spec_revision INTEGER NOT NULL,

            method TEXT NOT NULL,
            path TEXT NOT NULL,
            summary TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            responses_json TEXT NOT NULL,
            constraints_json TEXT NOT NULL,

            evidence_class TEXT NOT NULL,
            tacl_layer TEXT NOT NULL,
            contract_role TEXT NOT NULL,
            authority_rank INTEGER NOT NULL,
            source_type TEXT NOT NULL,

            is_current INTEGER NOT NULL,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL,
            superseded_at_utc TEXT,

            CHECK (spec_revision >= 1),
            CHECK (is_current IN (0, 1)),
            CHECK (method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')),
            CHECK (evidence_class IN ('FHS', 'CHS', 'EHS')),
            CHECK (tacl_layer IN ('L0', 'L1', 'L2', 'L3', 'L4')),
            CHECK (contract_role IN ('core', 'supplement', 'candidate', 'discovery')),
            UNIQUE (cthc_hash, source_hash)
        );

        CREATE TABLE IF NOT EXISTS ingest_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT NOT NULL UNIQUE,
            input_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            endpoint_count INTEGER NOT NULL,
            created_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS guard_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT NOT NULL,
            gate_name TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            details_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_hash TEXT NOT NULL UNIQUE,
            prev_event_hash TEXT,
            event_type TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_api_specs_cthc_hash
            ON api_specs(cthc_hash);

        CREATE INDEX IF NOT EXISTS idx_api_specs_source_hash
            ON api_specs(source_hash);

        CREATE INDEX IF NOT EXISTS idx_api_specs_method_path
            ON api_specs(method, path);

        CREATE INDEX IF NOT EXISTS idx_api_specs_service_version_method_path
            ON api_specs(service_name, api_version, method, path);

        CREATE INDEX IF NOT EXISTS idx_api_specs_evidence_class
            ON api_specs(evidence_class);

        CREATE INDEX IF NOT EXISTS idx_api_specs_tacl_layer
            ON api_specs(tacl_layer);

        CREATE INDEX IF NOT EXISTS idx_api_specs_current
            ON api_specs(is_current);

        CREATE INDEX IF NOT EXISTS idx_ingest_events_created_at
            ON ingest_events(created_at_utc);

        CREATE INDEX IF NOT EXISTS idx_guard_decisions_event_hash
            ON guard_decisions(event_hash);

        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
            ON audit_log(created_at_utc);
        """
    )

    conn.execute(
        """
        INSERT INTO schema_meta(key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        ("schema_version", SCHEMA_VERSION),
    )

    conn.commit()


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = ?
          AND name NOT LIKE ?
        ORDER BY name
        """,
        ("table", "sqlite_%"),
    ).fetchall()

    return [str(row["name"]) for row in rows]


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    if table_name not in EXPECTED_TABLES:
        raise ValueError(f"unknown table name: {table_name}")

    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row["name"]) for row in rows]


def get_indexes(conn: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    if table_name not in EXPECTED_TABLES:
        raise ValueError(f"unknown table name: {table_name}")

    rows = conn.execute(f"PRAGMA index_list({table_name})").fetchall()
    return [
        {
            "seq": row["seq"],
            "name": row["name"],
            "unique": bool(row["unique"]),
            "origin": row["origin"],
            "partial": bool(row["partial"]),
        }
        for row in rows
    ]
