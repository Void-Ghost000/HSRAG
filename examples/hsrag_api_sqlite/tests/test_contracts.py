from __future__ import annotations

from hsrag_api_sqlite.contracts import (
    Result,
    contains_secret_like_keys,
    validate_authority_mapping,
    validate_contract_role,
    validate_evidence_class,
    validate_method,
    validate_path,
    validate_tacl_layer,
)


def test_result_contract_shape() -> None:
    result = Result(
        status="ok",
        reason_code="TEST_OK",
        data={"value": 1},
    )

    assert result.as_dict() == {
        "status": "ok",
        "reason_code": "TEST_OK",
        "retryable": False,
        "data": {"value": 1},
        "errors": [],
        "warnings": [],
    }


def test_invalid_result_status_is_rejected() -> None:
    try:
        Result(status="maybe", reason_code="BAD")
    except ValueError as exc:
        assert "Invalid result status" in str(exc)
    else:
        raise AssertionError("invalid result status should fail")


def test_validate_method_accepts_allowed_methods() -> None:
    result = validate_method("get")

    assert result.status == "ok"
    assert result.data["method"] == "GET"


def test_validate_method_rejects_invalid_method() -> None:
    result = validate_method("FETCH")

    assert result.status == "error"
    assert result.reason_code == "INVALID_API_METHOD"


def test_validate_path_requires_leading_slash() -> None:
    result = validate_path("users/{id}")

    assert result.status == "error"
    assert result.reason_code == "INVALID_API_PATH"


def test_validate_evidence_class() -> None:
    result = validate_evidence_class("fhs")

    assert result.status == "ok"
    assert result.data["evidence_class"] == "FHS"


def test_validate_tacl_layer() -> None:
    result = validate_tacl_layer("l0")

    assert result.status == "ok"
    assert result.data["tacl_layer"] == "L0"


def test_validate_contract_role() -> None:
    result = validate_contract_role("Core")

    assert result.status == "ok"
    assert result.data["contract_role"] == "core"


def test_validate_authority_mapping_allows_l0_fhs_core() -> None:
    result = validate_authority_mapping("L0", "FHS", "core")

    assert result.status == "ok"
    assert result.data["authority_rank"] == 100


def test_validate_authority_mapping_blocks_ehs_as_l0_core() -> None:
    result = validate_authority_mapping("L0", "EHS", "core")

    assert result.status == "blocked"
    assert result.reason_code == "INVALID_AUTHORITY_MAPPING"


def test_contains_secret_like_keys_detects_nested_secret_fields() -> None:
    payload = {
        "service_name": "demo",
        "constraints": {
            "auth_required": True,
            "Authorization": "Bearer fake",
        },
        "items": [
            {
                "api_key": "fake-key"
            }
        ],
    }

    findings = contains_secret_like_keys(payload)

    assert "$.constraints.Authorization" in findings
    assert "$.items[0].api_key" in findings
