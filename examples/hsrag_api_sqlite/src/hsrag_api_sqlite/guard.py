from __future__ import annotations

from typing import Any

from hsrag_api_sqlite.contracts import (
    Result,
    blocked_result,
    contains_secret_like_keys,
    error_result,
    found_result,
    not_found_result,
    ok_result,
    validate_authority_mapping,
    validate_method,
    validate_path,
    warning_result,
)


CANONICAL_LAYER = "L0"
CANONICAL_EVIDENCE_CLASS = "FHS"
CANONICAL_CONTRACT_ROLE = "core"


def validate_no_secret_like_fields(payload: Any) -> Result:
    findings = contains_secret_like_keys(payload)

    if findings:
        return error_result(
            "SECRET_LIKE_FIELD_REJECTED",
            [
                "Secret-like fields are not allowed in the v0.1 local-only demo.",
                f"findings: {findings}",
            ],
        )

    return ok_result("NO_SECRET_LIKE_FIELDS_FOUND", {"findings": []})


def validate_endpoint_guard_payload(endpoint: dict[str, Any]) -> Result:
    secret_result = validate_no_secret_like_fields(endpoint)
    if secret_result.status == "error":
        return secret_result

    method_result = validate_method(endpoint.get("method"))
    if method_result.status == "error":
        return method_result

    path_result = validate_path(endpoint.get("path"))
    if path_result.status == "error":
        return path_result

    authority_result = validate_authority_mapping(
        endpoint.get("tacl_layer"),
        endpoint.get("evidence_class"),
        endpoint.get("contract_role"),
    )
    if authority_result.status != "ok":
        return authority_result

    return ok_result(
        "ENDPOINT_GUARD_PAYLOAD_VALID",
        {
            "method": method_result.data["method"],
            "path": path_result.data["path"],
            "authority": authority_result.data,
        },
    )


def require_canonical_authority(record: dict[str, Any]) -> Result:
    authority_result = validate_authority_mapping(
        record.get("tacl_layer"),
        record.get("evidence_class"),
        record.get("contract_role"),
    )

    if authority_result.status != "ok":
        return authority_result

    data = authority_result.data
    layer = data["tacl_layer"]
    evidence = data["evidence_class"]
    role = data["contract_role"]

    if (
        layer == CANONICAL_LAYER
        and evidence == CANONICAL_EVIDENCE_CLASS
        and role == CANONICAL_CONTRACT_ROLE
    ):
        return ok_result("CANONICAL_AUTHORITY_CONFIRMED", data)

    if evidence == "EHS":
        return blocked_result(
            "UNVERIFIED_SPEC_CANNOT_BE_CANONICAL",
            [
                f"Canonical contract requires L0/FHS/core, got {layer}/{evidence}/{role}."
            ],
        )

    return blocked_result(
        "AUTHORITY_LAYER_TOO_LOW",
        [
            f"Canonical contract requires L0/FHS/core, got {layer}/{evidence}/{role}."
        ],
    )


def same_api_identity(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_hash = left.get("cthc_hash")
    right_hash = right.get("cthc_hash")

    if left_hash and right_hash:
        return str(left_hash) == str(right_hash)

    return (
        str(left.get("service_name", "")).lower().strip()
        == str(right.get("service_name", "")).lower().strip()
        and str(left.get("api_version", "")).strip()
        == str(right.get("api_version", "")).strip()
        and str(left.get("method", "")).upper().strip()
        == str(right.get("method", "")).upper().strip()
        and str(left.get("path", "")).strip()
        == str(right.get("path", "")).strip()
    )


def is_l0_fhs_core(record: dict[str, Any]) -> bool:
    result = require_canonical_authority(record)
    return result.status == "ok"


def prevent_lower_layer_override(
    existing_records: list[dict[str, Any]],
    incoming_record: dict[str, Any],
) -> Result:
    incoming_authority = validate_authority_mapping(
        incoming_record.get("tacl_layer"),
        incoming_record.get("evidence_class"),
        incoming_record.get("contract_role"),
    )

    if incoming_authority.status != "ok":
        return incoming_authority

    incoming_evidence = incoming_authority.data["evidence_class"]

    for existing in existing_records:
        if not same_api_identity(existing, incoming_record):
            continue

        if is_l0_fhs_core(existing) and not is_l0_fhs_core(incoming_record):
            if incoming_evidence == "CHS":
                return blocked_result(
                    "CHS_CONFLICTS_WITH_FHS",
                    ["CHS supplement cannot overwrite an existing L0/FHS/core contract."],
                )

            if incoming_evidence == "EHS":
                return blocked_result(
                    "EHS_CANNOT_OVERRIDE_FHS",
                    ["EHS candidate cannot overwrite an existing L0/FHS/core contract."],
                )

            return blocked_result(
                "LOWER_LAYER_OVERRIDE_BLOCKED",
                ["Lower authority layer cannot overwrite an existing canonical contract."],
            )

    return ok_result("NO_LOWER_LAYER_OVERRIDE", {"checked_records": len(existing_records)})


def semantic_discovery_result(candidates: list[dict[str, Any]]) -> Result:
    return warning_result(
        "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION",
        data={"candidates": candidates},
        warnings=[
            "Semantic discovery returns candidates only. Use cthc_hash for canonical lookup."
        ],
    )


def resolve_canonical_candidate(records: list[dict[str, Any]]) -> Result:
    canonical_records = [record for record in records if is_l0_fhs_core(record)]

    if len(canonical_records) > 1:
        return blocked_result(
            "EVIDENCE_LAYER_CONFLICT",
            ["Multiple L0/FHS/core records matched the same query."],
        )

    chs_records = [
        record
        for record in records
        if record.get("evidence_class") == "CHS"
        and record.get("contract_role") == "supplement"
    ]

    ehs_records = [
        record
        for record in records
        if record.get("evidence_class") == "EHS"
    ]

    if len(canonical_records) == 1:
        return found_result(
            "CANONICAL_SPEC_FOUND",
            {
                "canonical_contract": canonical_records[0],
                "supplements": chs_records,
                "candidates": ehs_records,
            },
        )

    if chs_records:
        return warning_result(
            "CHS_ONLY_SPEC_FOUND",
            data={"supplements": chs_records},
            warnings=[
                "Only CHS supplemental records matched. No L0/FHS/core canonical contract found."
            ],
        )

    if ehs_records:
        return warning_result(
            "EHS_UNVERIFIED_SPEC_FOUND",
            data={"candidates": ehs_records},
            warnings=[
                "Only EHS unverified records matched. This cannot be used as a canonical contract."
            ],
        )

    return not_found_result("SPEC_NOT_FOUND")
