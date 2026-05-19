from __future__ import annotations

import hashlib
import json
from typing import Any

from hsrag_api_sqlite.contracts import (
    validate_authority_mapping,
    validate_method,
    validate_path,
)


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except TypeError as exc:
        raise ValueError(f"value is not JSON serializable: {exc}") from exc


def sha256_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("sha256_text expects a string")

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_method(method: str) -> str:
    result = validate_method(method)
    if result.status == "error":
        raise ValueError("; ".join(result.errors))

    return result.data["method"]


def normalize_path(path: str) -> str:
    result = validate_path(path)
    if result.status == "error":
        raise ValueError("; ".join(result.errors))

    return result.data["path"]


def canonical_cthc_string(
    service_name: str,
    api_version: str,
    method: str,
    path: str,
) -> str:
    service = str(service_name).strip().lower()
    version = str(api_version).strip()
    normalized_method = normalize_method(method)
    normalized_path = normalize_path(path)

    if not service:
        raise ValueError("service_name is required")

    if not version:
        raise ValueError("api_version is required")

    return f"API|{service}|{version}|{normalized_method}|{normalized_path}"


def make_cthc_address(
    service_name: str,
    api_version: str,
    method: str,
    path: str,
) -> str:
    service = str(service_name).strip().lower()
    version = str(api_version).strip()
    normalized_method = normalize_method(method)
    normalized_path = normalize_path(path)

    if not service:
        raise ValueError("service_name is required")

    if not version:
        raise ValueError("api_version is required")

    return f"cthc://api/{service}/{version}/{normalized_method}{normalized_path}"


def make_cthc_hash(
    service_name: str,
    api_version: str,
    method: str,
    path: str,
) -> str:
    return sha256_text(
        canonical_cthc_string(
            service_name=service_name,
            api_version=api_version,
            method=method,
            path=path,
        )
    )


def canonical_authority_string(
    tacl_layer: str,
    evidence_class: str,
    contract_role: str,
) -> str:
    result = validate_authority_mapping(
        tacl_layer=tacl_layer,
        evidence_class=evidence_class,
        contract_role=contract_role,
    )

    if result.status != "ok":
        raise ValueError("; ".join(result.errors))

    data = result.data
    return f"TACL|{data['tacl_layer']}|{data['evidence_class']}|{data['contract_role']}"


def make_authority_hash(
    tacl_layer: str,
    evidence_class: str,
    contract_role: str,
) -> str:
    return sha256_text(
        canonical_authority_string(
            tacl_layer=tacl_layer,
            evidence_class=evidence_class,
            contract_role=contract_role,
        )
    )


def make_source_hash(endpoint_record: dict[str, Any]) -> str:
    return sha256_text(canonical_json(endpoint_record))
