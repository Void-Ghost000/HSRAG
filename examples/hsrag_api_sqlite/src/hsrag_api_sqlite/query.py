from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from hsrag_api_sqlite.contracts import (
    Result,
    blocked_result,
    error_result,
    found_result,
    not_found_result,
)
from hsrag_api_sqlite.db import apply_schema, connect_db
from hsrag_api_sqlite.guard import (
    resolve_canonical_candidate,
    semantic_discovery_result,
)
from hsrag_api_sqlite.hashing import make_cthc_hash


def query_by_cthc_hash(
    db_path: str | Path,
    cthc_hash: str,
) -> Result:
    if not isinstance(cthc_hash, str) or not cthc_hash.startswith("sha256:"):
        return error_result("INVALID_CTHC_HASH", ["cthc_hash must start with sha256:"])

    try:
        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            records = fetch_current_records_by_cthc_hash(conn, cthc_hash)
        finally:
            conn.close()

        if not records:
            return not_found_result("SPEC_NOT_FOUND")

        resolved = resolve_canonical_candidate(records)

        if resolved.status == "found":
            return found_result(
                "CANONICAL_SPEC_FOUND_BY_CTHC_HASH",
                resolved.data,
            )

        return resolved

    except sqlite3.Error as exc:
        return error_result("SQLITE_QUERY_FAILED", [str(exc)])


def query_by_cthc_address(
    db_path: str | Path,
    cthc_address: str,
) -> Result:
    if not isinstance(cthc_address, str) or not cthc_address.startswith("cthc://api/"):
        return error_result("INVALID_CTHC_ADDRESS", ["cthc_address must start with cthc://api/"])

    try:
        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            row = conn.execute(
                """
                SELECT cthc_hash
                FROM api_specs
                WHERE cthc_address = ?
                  AND is_current = ?
                ORDER BY authority_rank DESC, spec_revision DESC
                LIMIT 1
                """,
                (cthc_address, 1),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return not_found_result("SPEC_NOT_FOUND")

        return query_by_cthc_hash(db_path, row["cthc_hash"])

    except sqlite3.Error as exc:
        return error_result("SQLITE_QUERY_FAILED", [str(exc)])


def query_by_method_path(
    db_path: str | Path,
    method: str,
    path: str,
    *,
    service_name: str | None = None,
    api_version: str | None = None,
) -> Result:
    try:
        normalized_method = str(method).upper().strip()
        normalized_path = str(path).strip()

        conn = connect_db(db_path)
        try:
            apply_schema(conn)

            if service_name and api_version:
                cthc_hash = make_cthc_hash(
                    service_name=service_name,
                    api_version=api_version,
                    method=normalized_method,
                    path=normalized_path,
                )
                records = fetch_current_records_by_cthc_hash(conn, cthc_hash)
            else:
                rows = conn.execute(
                    """
                    SELECT DISTINCT cthc_hash
                    FROM api_specs
                    WHERE method = ?
                      AND path = ?
                      AND is_current = ?
                    ORDER BY cthc_hash
                    """,
                    (normalized_method, normalized_path, 1),
                ).fetchall()

                hashes = [row["cthc_hash"] for row in rows]

                if len(hashes) > 1:
                    return blocked_result(
                        "AMBIGUOUS_API_SPEC_REQUIRES_CTHC_POINTER",
                        [
                            "Multiple API specs matched method/path. Provide service_name/api_version or cthc_hash."
                        ],
                    )

                if not hashes:
                    return not_found_result("SPEC_NOT_FOUND")

                records = fetch_current_records_by_cthc_hash(conn, hashes[0])

        finally:
            conn.close()

        if not records:
            return not_found_result("SPEC_NOT_FOUND")

        resolved = resolve_canonical_candidate(records)

        if resolved.status == "found":
            return found_result(
                "API_SPEC_FOUND",
                resolved.data,
            )

        return resolved

    except ValueError as exc:
        return error_result("INVALID_METHOD_PATH_QUERY", [str(exc)])
    except sqlite3.Error as exc:
        return error_result("SQLITE_QUERY_FAILED", [str(exc)])


def history_by_cthc_hash(
    db_path: str | Path,
    cthc_hash: str,
) -> Result:
    if not isinstance(cthc_hash, str) or not cthc_hash.startswith("sha256:"):
        return error_result("INVALID_CTHC_HASH", ["cthc_hash must start with sha256:"])

    try:
        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            rows = conn.execute(
                """
                SELECT *
                FROM api_specs
                WHERE cthc_hash = ?
                ORDER BY spec_revision ASC, id ASC
                """,
                (cthc_hash,),
            ).fetchall()
        finally:
            conn.close()

        history = [row_to_record(row) for row in rows]

        if not history:
            return not_found_result("SPEC_NOT_FOUND")

        return found_result(
            "SPEC_HISTORY_FOUND",
            {
                "cthc_hash": cthc_hash,
                "history": history,
            },
        )

    except sqlite3.Error as exc:
        return error_result("SQLITE_QUERY_FAILED", [str(exc)])


def semantic_discovery(
    db_path: str | Path,
    query_text: str,
    *,
    limit: int = 10,
) -> Result:
    if not isinstance(query_text, str) or not query_text.strip():
        return error_result("INVALID_SEMANTIC_QUERY", ["query_text is required"])

    safe_limit = max(1, min(int(limit), 50))
    pattern = f"%{query_text.strip()}%"

    try:
        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            rows = conn.execute(
                """
                SELECT *
                FROM api_specs
                WHERE is_current = ?
                  AND (
                    summary LIKE ?
                    OR path LIKE ?
                    OR method LIKE ?
                    OR service_name LIKE ?
                  )
                ORDER BY authority_rank DESC, service_name ASC, path ASC
                LIMIT ?
                """,
                (1, pattern, pattern, pattern, pattern, safe_limit),
            ).fetchall()
        finally:
            conn.close()

        candidates = [row_to_record(row) for row in rows]

        if not candidates:
            return not_found_result("SPEC_NOT_FOUND")

        return semantic_discovery_result(candidates)

    except sqlite3.Error as exc:
        return error_result("SQLITE_QUERY_FAILED", [str(exc)])


def fetch_current_records_by_cthc_hash(
    conn: sqlite3.Connection,
    cthc_hash: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM api_specs
        WHERE cthc_hash = ?
          AND is_current = ?
        ORDER BY authority_rank DESC, spec_revision DESC, id DESC
        """,
        (cthc_hash, 1),
    ).fetchall()

    return [row_to_record(row) for row in rows]


def row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    record = dict(row)

    record["parameters"] = json.loads(record.pop("parameters_json"))
    record["responses"] = json.loads(record.pop("responses_json"))
    record["constraints"] = json.loads(record.pop("constraints_json"))

    return record
