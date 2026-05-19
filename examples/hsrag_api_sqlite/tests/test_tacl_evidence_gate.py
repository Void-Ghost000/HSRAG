from __future__ import annotations

from copy import deepcopy

from hsrag_api_sqlite.guard import (
    prevent_lower_layer_override,
    require_canonical_authority,
    resolve_canonical_candidate,
    semantic_discovery_result,
    validate_endpoint_guard_payload,
    validate_no_secret_like_fields,
)


def fhs_record() -> dict:
    return {
        "cthc_hash": "sha256:same-api",
        "service_name": "demo-service",
        "api_version": "v1",
        "method": "GET",
        "path": "/users/{id}",
        "evidence_class": "FHS",
        "tacl_layer": "L0",
        "contract_role": "core",
        "summary": "Canonical user lookup endpoint.",
    }


def chs_record() -> dict:
    record = deepcopy(fhs_record())
    record.update(
        {
            "evidence_class": "CHS",
            "tacl_layer": "L1",
            "contract_role": "supplement",
            "summary": "Supplemental usage note.",
        }
    )
    return record


def ehs_record() -> dict:
    record = deepcopy(fhs_record())
    record.update(
        {
            "evidence_class": "EHS",
            "tacl_layer": "L3",
            "contract_role": "candidate",
            "summary": "Unverified candidate endpoint.",
        }
    )
    return record


def test_validate_no_secret_like_fields_allows_clean_payload() -> None:
    result = validate_no_secret_like_fields(
        {
            "service_name": "demo",
            "constraints": {
                "auth_required": True
            },
        }
    )

    assert result.status == "ok"
    assert result.reason_code == "NO_SECRET_LIKE_FIELDS_FOUND"


def test_validate_no_secret_like_fields_rejects_secret_keys() -> None:
    result = validate_no_secret_like_fields(
        {
            "Authorization": "Bearer fake",
            "nested": {
                "api_key": "fake"
            },
        }
    )

    assert result.status == "error"
    assert result.reason_code == "SECRET_LIKE_FIELD_REJECTED"


def test_endpoint_guard_payload_accepts_valid_fhs_core() -> None:
    result = validate_endpoint_guard_payload(fhs_record())

    assert result.status == "ok"
    assert result.reason_code == "ENDPOINT_GUARD_PAYLOAD_VALID"
    assert result.data["method"] == "GET"
    assert result.data["path"] == "/users/{id}"


def test_endpoint_guard_payload_rejects_invalid_method() -> None:
    record = fhs_record()
    record["method"] = "FETCH"

    result = validate_endpoint_guard_payload(record)

    assert result.status == "error"
    assert result.reason_code == "INVALID_API_METHOD"


def test_l0_fhs_core_can_be_canonical() -> None:
    result = require_canonical_authority(fhs_record())

    assert result.status == "ok"
    assert result.reason_code == "CANONICAL_AUTHORITY_CONFIRMED"


def test_l1_chs_cannot_satisfy_l0_requirement() -> None:
    result = require_canonical_authority(chs_record())

    assert result.status == "blocked"
    assert result.reason_code == "AUTHORITY_LAYER_TOO_LOW"


def test_l3_ehs_cannot_satisfy_canonical_lookup() -> None:
    result = require_canonical_authority(ehs_record())

    assert result.status == "blocked"
    assert result.reason_code == "UNVERIFIED_SPEC_CANNOT_BE_CANONICAL"


def test_fhs_not_overwritten_by_chs() -> None:
    result = prevent_lower_layer_override(
        existing_records=[fhs_record()],
        incoming_record=chs_record(),
    )

    assert result.status == "blocked"
    assert result.reason_code == "CHS_CONFLICTS_WITH_FHS"


def test_fhs_not_overwritten_by_ehs() -> None:
    result = prevent_lower_layer_override(
        existing_records=[fhs_record()],
        incoming_record=ehs_record(),
    )

    assert result.status == "blocked"
    assert result.reason_code == "EHS_CANNOT_OVERRIDE_FHS"


def test_chs_allowed_when_no_fhs_exists() -> None:
    result = prevent_lower_layer_override(
        existing_records=[],
        incoming_record=chs_record(),
    )

    assert result.status == "ok"
    assert result.reason_code == "NO_LOWER_LAYER_OVERRIDE"


def test_semantic_discovery_returns_candidates_only() -> None:
    result = semantic_discovery_result([ehs_record()])

    assert result.status == "found_with_warning"
    assert result.reason_code == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION"
    assert result.data["candidates"]


def test_query_prefers_fhs_over_chs_and_ehs() -> None:
    result = resolve_canonical_candidate(
        [
            ehs_record(),
            chs_record(),
            fhs_record(),
        ]
    )

    assert result.status == "found"
    assert result.reason_code == "CANONICAL_SPEC_FOUND"
    assert result.data["canonical_contract"]["evidence_class"] == "FHS"
    assert len(result.data["supplements"]) == 1
    assert len(result.data["candidates"]) == 1


def test_chs_only_result_has_warning() -> None:
    result = resolve_canonical_candidate([chs_record()])

    assert result.status == "found_with_warning"
    assert result.reason_code == "CHS_ONLY_SPEC_FOUND"


def test_ehs_only_result_has_unverified_warning() -> None:
    result = resolve_canonical_candidate([ehs_record()])

    assert result.status == "found_with_warning"
    assert result.reason_code == "EHS_UNVERIFIED_SPEC_FOUND"


def test_multiple_fhs_records_return_conflict() -> None:
    first = fhs_record()
    second = fhs_record()
    second["source_hash"] = "sha256:different"

    result = resolve_canonical_candidate([first, second])

    assert result.status == "blocked"
    assert result.reason_code == "EVIDENCE_LAYER_CONFLICT"
