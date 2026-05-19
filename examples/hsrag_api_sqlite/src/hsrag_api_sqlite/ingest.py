from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hsrag_api_sqlite.contracts import (
    Result,
    error_result,
    ok_result,
    validate_authority_mapping,
)
from hsrag_api_sqlite.db import apply_schema, connect_db
from hsrag_api_sqlite.guard import (
    prevent_lower_layer_override,
    validate_endpoint_guard_payload,
    validate_no_secret_like_fields,
)
from hsrag_api_sqlite.hashing import (
    canonical_json,
    make_authority_hash,
    make_cthc_address,
    make_cthc_hash,
    make_source_hash,
    sha256_text,
)


def utc_now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    return json.loads(file_path.read_text(encoding="utf-8"))


def ingest_api_spec_file(path: str | Path, db_path: str | Path = ":memory:") -> Result:
    try:
        payload = load_json_file(path)
    except json.JSONDecodeError as exc:
        return error_result("INVALID_JSON_INPUT", [str(exc)])
    except OSError as exc:
        return error_result("INPUT_FILE_READ_FAILED", [str(exc)])

    return ingest_api_spec(payload, db_path=db_path)


def ingest_api_spec(payload: dict[str, Any], db_path: str | Path = ":memory:") -> Result:
    event_time_utc = utc_now_z()

    validation = validate_api_spec_payload(payload)
    if validation.status != "ok":
        return validation

    try:
        input_hash = sha256_text(canonical_json(payload))
        event_hash = sha256_text(
            canonical_json(
                {
                    "event_type": "API_SPEC_INGEST",
                    "input_hash": input_hash,
                    "created_at_utc": event_time_utc,
                }
            )
        )

        normalized_endpoints = normalize_api_spec_payload(payload)

        conn = connect_db(db_path)
        try:
            apply_schema(conn)
            conn.execute("BEGIN")

            endpoint_results: list[dict[str, Any]] = []
            inserted_count = 0
            revision_count = 0
            idempotent_count = 0

            for endpoint in normalized_endpoints:
                operation = insert_or_revision_endpoint(
                    conn=conn,
                    endpoint=endpoint,
                    event_time_utc=event_time_utc,
                )
                endpoint_results.append(operation)

                if operation["operation"] == "inserted":
                    inserted_count += 1
                elif operation["operation"] == "revision_created":
                    revision_count += 1
                elif operation["operation"] == "idempotent":
                    idempotent_count += 1

                append_guard_decision(
                    conn=conn,
                    event_hash=event_hash,
                    gate_name="INGEST_GUARD",
                    decision="ALLOW",
                    reason_code=operation["reason_code"],
                    details={
                        "cthc_hash": operation["cthc_hash"],
                        "source_hash": operation["source_hash"],
                        "operation": operation["operation"],
                    },
                    created_at_utc=event_time_utc,
                )

            append_ingest_event(
                conn=conn,
                event_hash=event_hash,
                input_hash=input_hash,
                status="ok",
                reason_code=select_ingest_reason_code(
                    inserted_count=inserted_count,
                    revision_count=revision_count,
                    idempotent_count=idempotent_count,
                ),
                endpoint_count=len(normalized_endpoints),
                created_at_utc=event_time_utc,
            )

            append_audit_log(
                conn=conn,
                event_hash=event_hash,
                event_type="API_SPEC_INGEST",
                payload_hash=sha256_text(canonical_json(endpoint_results)),
                created_at_utc=event_time_utc,
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return ok_result(
            select_ingest_reason_code(
                inserted_count=inserted_count,
                revision_count=revision_count,
                idempotent_count=idempotent_count,
            ),
            {
                "event_hash": event_hash,
                "input_hash": input_hash,
                "created_at_utc": event_time_utc,
                "endpoint_count": len(normalized_endpoints),
                "inserted_count": inserted_count,
                "revision_count": revision_count,
                "idempotent_count": idempotent_count,
                "endpoints": endpoint_results,
            },
        )

    except sqlite3.Error as exc:
        return error_result("SQLITE_INGEST_FAILED", [str(exc)])
    except ValueError as exc:
        return error_result("INGEST_VALIDATION_FAILED", [str(exc)])


def validate_api_spec_payload(payload: Any) -> Result:
    if not isinstance(payload, dict):
        return error_result("INVALID_API_SPEC_INPUT", ["payload must be a JSON object"])

    secret_result = validate_no_secret_like_fields(payload)
    if secret_result.status == "error":
        return secret_result

    service_name = payload.get("service_name")
    api_version = payload.get("api_version")
    endpoints = payload.get("endpoints")

    if not isinstance(service_name, str) or not service_name.strip():
        return error_result("MISSING_SERVICE_NAME", ["service_name is required"])

    if not isinstance(api_version, str) or not api_version.strip():
        return error_result("MISSING_API_VERSION", ["api_version is required"])

    if not isinstance(endpoints, list) or not endpoints:
        return error_result("INVALID_ENDPOINTS", ["endpoints must be a non-empty list"])

    for index, raw_endpoint in enumerate(endpoints):
        if not isinstance(raw_endpoint, dict):
            return error_result(
                "INVALID_ENDPOINT_RECORD",
                [f"endpoints[{index}] must be an object"],
            )

        endpoint = merge_endpoint_defaults(payload, raw_endpoint)
        guard_result = validate_endpoint_guard_payload(endpoint)
        if guard_result.status != "ok":
            return guard_result

    return ok_result("API_SPEC_PAYLOAD_VALID")


def normalize_api_spec_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []

    for raw_endpoint in payload["endpoints"]:
        endpoint = merge_endpoint_defaults(payload, raw_endpoint)

        authority_result = validate_authority_mapping(
            endpoint["tacl_layer"],
            endpoint["evidence_class"],
            endpoint["contract_role"],
        )
        if authority_result.status != "ok":
            raise ValueError("; ".join(authority_result.errors))

        authority_data = authority_result.data

        source_record = {
            "service_name": endpoint["service_name"].strip().lower(),
            "api_version": endpoint["api_version"].strip(),
            "source_type": endpoint["source_type"].strip(),
            "evidence_class": authority_data["evidence_class"],
            "tacl_layer": authority_data["tacl_layer"],
            "contract_role": authority_data["contract_role"],
            "method": endpoint["method"].upper().strip(),
            "path": endpoint["path"].strip(),
            "summary": str(endpoint.get("summary", "")).strip(),
            "parameters": endpoint.get("parameters", {}),
            "responses": endpoint.get("responses", {}),
            "constraints": endpoint.get("constraints", {}),
        }

        cthc_address = make_cthc_address(
            source_record["service_name"],
            source_record["api_version"],
            source_record["method"],
            source_record["path"],
        )
        cthc_hash = make_cthc_hash(
            source_record["service_name"],
            source_record["api_version"],
            source_record["method"],
            source_record["path"],
        )
        authority_hash = make_authority_hash(
            source_record["tacl_layer"],
            source_record["evidence_class"],
            source_record["contract_role"],
        )
        source_hash = make_source_hash(source_record)

        endpoints.append(
            {
                **source_record,
                "cthc_address": cthc_address,
                "cthc_hash": cthc_hash,
                "authority_hash": authority_hash,
                "source_hash": source_hash,
                "authority_rank": authority_data["authority_rank"],
            }
        )

    return endpoints


def merge_endpoint_defaults(
    payload: dict[str, Any],
    endpoint: dict[str, Any],
) -> dict[str, Any]:
    return {
        "service_name": endpoint.get("service_name", payload.get("service_name")),
        "api_version": endpoint.get("api_version", payload.get("api_version")),
        "source_type": endpoint.get("source_type", payload.get("source_type", "unknown")),
        "evidence_class": endpoint.get("evidence_class", payload.get("evidence_class")),
        "tacl_layer": endpoint.get("tacl_layer", payload.get("tacl_layer")),
        "contract_role": endpoint.get("contract_role", payload.get("contract_role")),
        "method": endpoint.get("method"),
        "path": endpoint.get("path"),
        "summary": endpoint.get("summary", ""),
        "parameters": endpoint.get("parameters", {}),
        "responses": endpoint.get("responses", {}),
        "constraints": endpoint.get("constraints", {}),
    }


def insert_or_revision_endpoint(
    conn: sqlite3.Connection,
    endpoint: dict[str, Any],
    event_time_utc: str,
) -> dict[str, Any]:
    exact_existing = conn.execute(
        """
        SELECT *
        FROM api_specs
        WHERE cthc_hash = ?
          AND source_hash = ?
        ORDER BY spec_revision DESC
        LIMIT 1
        """,
        (endpoint["cthc_hash"], endpoint["source_hash"]),
    ).fetchone()

    if exact_existing is not None:
        return {
            "operation": "idempotent",
            "reason_code": "INGEST_IDEMPOTENT_ALREADY_EXISTS",
            "cthc_hash": endpoint["cthc_hash"],
            "source_hash": endpoint["source_hash"],
            "spec_revision": int(exact_existing["spec_revision"]),
            "id": int(exact_existing["id"]),
        }

    existing_current = fetch_current_records_by_cthc_hash(conn, endpoint["cthc_hash"])

    override_result = prevent_lower_layer_override(
        existing_records=existing_current,
        incoming_record=endpoint,
    )
    if override_result.status != "ok":
        raise ValueError(override_result.reason_code + ": " + "; ".join(override_result.errors))

    latest_revision = fetch_latest_revision(conn, endpoint["cthc_hash"])

    if latest_revision == 0:
        spec_revision = 1
        operation = "inserted"
        reason_code = "API_SPEC_INGESTED"
    else:
        spec_revision = latest_revision + 1
        operation = "revision_created"
        reason_code = "NEW_SPEC_REVISION_CREATED"

        conn.execute(
            """
            UPDATE api_specs
            SET is_current = ?,
                updated_at_utc = ?,
                superseded_at_utc = ?
            WHERE cthc_hash = ?
              AND is_current = ?
            """,
            (0, event_time_utc, event_time_utc, endpoint["cthc_hash"], 1),
        )

    cursor = conn.execute(
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
            endpoint["cthc_address"],
            endpoint["cthc_hash"],
            endpoint["authority_hash"],
            endpoint["source_hash"],
            endpoint["service_name"],
            endpoint["api_version"],
            spec_revision,
            endpoint["method"],
            endpoint["path"],
            endpoint["summary"],
            canonical_json(endpoint["parameters"]),
            canonical_json(endpoint["responses"]),
            canonical_json(endpoint["constraints"]),
            endpoint["evidence_class"],
            endpoint["tacl_layer"],
            endpoint["contract_role"],
            endpoint["authority_rank"],
            endpoint["source_type"],
            1,
            event_time_utc,
            event_time_utc,
            None,
        ),
    )

    return {
        "operation": operation,
        "reason_code": reason_code,
        "cthc_address": endpoint["cthc_address"],
        "cthc_hash": endpoint["cthc_hash"],
        "source_hash": endpoint["source_hash"],
        "spec_revision": spec_revision,
        "id": int(cursor.lastrowid),
    }


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
        ORDER BY authority_rank DESC, spec_revision DESC
        """,
        (cthc_hash, 1),
    ).fetchall()

    return [dict(row) for row in rows]


def fetch_latest_revision(conn: sqlite3.Connection, cthc_hash: str) -> int:
    row = conn.execute(
        """
        SELECT MAX(spec_revision) AS latest_revision
        FROM api_specs
        WHERE cthc_hash = ?
        """,
        (cthc_hash,),
    ).fetchone()

    if row is None or row["latest_revision"] is None:
        return 0

    return int(row["latest_revision"])


def append_ingest_event(
    conn: sqlite3.Connection,
    event_hash: str,
    input_hash: str,
    status: str,
    reason_code: str,
    endpoint_count: int,
    created_at_utc: str,
) -> None:
    conn.execute(
        """
        INSERT INTO ingest_events (
            event_hash,
            input_hash,
            status,
            reason_code,
            endpoint_count,
            created_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_hash,
            input_hash,
            status,
            reason_code,
            endpoint_count,
            created_at_utc,
        ),
    )


def append_guard_decision(
    conn: sqlite3.Connection,
    event_hash: str,
    gate_name: str,
    decision: str,
    reason_code: str,
    details: dict[str, Any],
    created_at_utc: str,
) -> None:
    conn.execute(
        """
        INSERT INTO guard_decisions (
            event_hash,
            gate_name,
            decision,
            reason_code,
            details_json,
            created_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_hash,
            gate_name,
            decision,
            reason_code,
            canonical_json(details),
            created_at_utc,
        ),
    )


def append_audit_log(
    conn: sqlite3.Connection,
    event_hash: str,
    event_type: str,
    payload_hash: str,
    created_at_utc: str,
) -> None:
    previous = conn.execute(
        """
        SELECT event_hash
        FROM audit_log
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    prev_event_hash = None if previous is None else previous["event_hash"]

    conn.execute(
        """
        INSERT INTO audit_log (
            event_hash,
            prev_event_hash,
            event_type,
            payload_hash,
            created_at_utc
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_hash,
            prev_event_hash,
            event_type,
            payload_hash,
            created_at_utc,
        ),
    )


def select_ingest_reason_code(
    *,
    inserted_count: int,
    revision_count: int,
    idempotent_count: int,
) -> str:
    if revision_count > 0:
        return "NEW_SPEC_REVISION_CREATED"

    if inserted_count > 0:
        return "API_SPEC_INGESTED"

    if idempotent_count > 0:
        return "INGEST_IDEMPOTENT_ALREADY_EXISTS"

    return "API_SPEC_INGESTED"
