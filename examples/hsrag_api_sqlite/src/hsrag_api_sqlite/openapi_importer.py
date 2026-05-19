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


from hsrag_api_sqlite.contracts import (
    Result,
    error_result,
    ok_result,
    validate_authority_mapping,
)
from hsrag_api_sqlite.ingest import ingest_api_spec
from hsrag_api_sqlite.hashing import canonical_json


OPENAPI_METHODS = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}


def load_openapi_json(path: str | Path) -> Result:
    file_path = Path(path)

    if str(file_path).lower().startswith(("http://", "https://")):
        return error_result(
            "REMOTE_OPENAPI_URL_FORBIDDEN",
            ["v0.1 importer only accepts local JSON files."],
        )

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return error_result("INVALID_OPENAPI_JSON", [str(exc)])
    except OSError as exc:
        return error_result("OPENAPI_FILE_READ_FAILED", [str(exc)])

    if not isinstance(payload, dict):
        return error_result("INVALID_OPENAPI_INPUT", ["OpenAPI JSON must be an object"])

    return ok_result("OPENAPI_JSON_LOADED", payload)


def normalize_openapi_json(
    openapi_payload: dict[str, Any],
    *,
    service_name: str,
    api_version: str,
    source_type: str = "local_openapi_json",
    evidence_class: str = "EHS",
    tacl_layer: str = "L3",
    contract_role: str = "candidate",
) -> Result:
    authority = validate_authority_mapping(
        tacl_layer=tacl_layer,
        evidence_class=evidence_class,
        contract_role=contract_role,
    )

    if authority.status != "ok":
        return authority

    if not isinstance(openapi_payload, dict):
        return error_result("INVALID_OPENAPI_INPUT", ["OpenAPI JSON must be an object"])

    paths = openapi_payload.get("paths")
    if not isinstance(paths, dict) or not paths:
        return error_result("OPENAPI_PATHS_MISSING", ["OpenAPI JSON must contain non-empty paths object"])

    if not isinstance(service_name, str) or not service_name.strip():
        return error_result("MISSING_SERVICE_NAME", ["service_name is required"])

    if not isinstance(api_version, str) or not api_version.strip():
        return error_result("MISSING_API_VERSION", ["api_version is required"])

    endpoints: list[dict[str, Any]] = []

    for raw_path, path_item in sorted(paths.items(), key=lambda item: item[0]):
        if not isinstance(raw_path, str) or not raw_path.startswith("/"):
            return error_result("INVALID_OPENAPI_PATH", [f"invalid path: {raw_path}"])

        if not isinstance(path_item, dict):
            return error_result("INVALID_OPENAPI_PATH_ITEM", [f"path item must be object: {raw_path}"])

        for method_key, operation in sorted(path_item.items(), key=lambda item: item[0]):
            lowered_method = str(method_key).lower().strip()
            if lowered_method not in OPENAPI_METHODS:
                continue

            if not isinstance(operation, dict):
                return error_result(
                    "INVALID_OPENAPI_OPERATION",
                    [f"operation must be object: {raw_path} {method_key}"],
                )

            method = OPENAPI_METHODS[lowered_method]
            summary = str(
                operation.get("summary")
                or operation.get("description")
                or f"{method} {raw_path}"
            ).strip()

            parameters: dict[str, Any] = {}
            if isinstance(operation.get("parameters"), list):
                parameters["openapi_parameters"] = operation["parameters"]

            if "requestBody" in operation:
                parameters["requestBody"] = operation["requestBody"]

            responses = operation.get("responses", {})
            if not isinstance(responses, dict) or not responses:
                responses = {
                    "default": {
                        "description": "No explicit OpenAPI responses provided."
                    }
                }

            constraints = {
                "openapi_imported": True,
                "operation_id": operation.get("operationId"),
                "tags": operation.get("tags", []),
                "deprecated": bool(operation.get("deprecated", False)),
                "sample_only": source_type.startswith("sample") or "sample" in source_type,
            }

            endpoints.append(
                {
                    "method": method,
                    "path": raw_path,
                    "summary": summary,
                    "parameters": parameters,
                    "responses": responses,
                    "constraints": constraints,
                }
            )

    if not endpoints:
        return error_result("OPENAPI_NO_SUPPORTED_OPERATIONS", ["No GET/POST/PUT/PATCH/DELETE operations found"])

    normalized = {
        "service_name": service_name.strip(),
        "api_version": api_version.strip(),
        "source_type": source_type.strip() or "local_openapi_json",
        "evidence_class": authority.data["evidence_class"],
        "tacl_layer": authority.data["tacl_layer"],
        "contract_role": authority.data["contract_role"],
        "endpoints": endpoints,
    }

    return ok_result(
        "OPENAPI_NORMALIZED",
        {
            "normalized_spec": normalized,
            "endpoint_count": len(endpoints),
        },
    )


def import_openapi_json_file(
    openapi_path: str | Path,
    *,
    db_path: str | Path,
    service_name: str,
    api_version: str,
    source_type: str = "local_openapi_json",
    evidence_class: str = "EHS",
    tacl_layer: str = "L3",
    contract_role: str = "candidate",
    normalized_output_path: str | Path | None = None,
) -> Result:
    loaded = load_openapi_json(openapi_path)
    if loaded.status != "ok":
        return loaded

    normalized = normalize_openapi_json(
        loaded.data,
        service_name=service_name,
        api_version=api_version,
        source_type=source_type,
        evidence_class=evidence_class,
        tacl_layer=tacl_layer,
        contract_role=contract_role,
    )
    if normalized.status != "ok":
        return normalized

    normalized_spec = normalized.data["normalized_spec"]

    if normalized_output_path is not None:
        output_path = Path(normalized_output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            canonical_json(normalized_spec),
            encoding="utf-8",
        )

    ingest_result = ingest_api_spec(normalized_spec, db_path=db_path)

    if ingest_result.status != "ok":
        return ingest_result

    return ok_result(
        "OPENAPI_IMPORTED",
        {
            "openapi_path": str(openapi_path),
            "db_path": str(db_path),
            "service_name": service_name,
            "api_version": api_version,
            "endpoint_count": normalized.data["endpoint_count"],
            "normalized_output_path": None if normalized_output_path is None else str(normalized_output_path),
            "ingest": ingest_result.as_dict(),
        },
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    parser = argparse.ArgumentParser(
        description="Local OpenAPI JSON importer for HSRAG API SQLite."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root / "input" / "openapi_petstore_minimal.json",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=project_root / "data" / "openapi_import.sqlite3",
    )
    parser.add_argument(
        "--service-name",
        default="petstore-openapi",
    )
    parser.add_argument(
        "--api-version",
        default="v1",
    )
    parser.add_argument(
        "--source-type",
        default="sample_openapi_json",
    )
    parser.add_argument(
        "--evidence-class",
        default="FHS",
    )
    parser.add_argument(
        "--tacl-layer",
        default="L0",
    )
    parser.add_argument(
        "--contract-role",
        default="core",
    )
    parser.add_argument(
        "--normalized-output",
        type=Path,
        default=project_root / "data" / "openapi_normalized.json",
    )

    args = parser.parse_args()

    result = import_openapi_json_file(
        args.input,
        db_path=args.db,
        service_name=args.service_name,
        api_version=args.api_version,
        source_type=args.source_type,
        evidence_class=args.evidence_class,
        tacl_layer=args.tacl_layer,
        contract_role=args.contract_role,
        normalized_output_path=args.normalized_output,
    )

    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))

    if result.status != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
