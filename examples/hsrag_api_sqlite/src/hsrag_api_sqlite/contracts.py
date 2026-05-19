from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_STATUSES = {
    "ok",
    "found",
    "found_with_warning",
    "blocked",
    "error",
    "not_found",
}

VALID_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

VALID_EVIDENCE_CLASSES = {
    "FHS",
    "CHS",
    "EHS",
}

VALID_TACL_LAYERS = {
    "L0",
    "L1",
    "L2",
    "L3",
    "L4",
}

VALID_CONTRACT_ROLES = {
    "core",
    "supplement",
    "candidate",
    "discovery",
}

AUTHORITY_RANKS = {
    "L0": 100,
    "L1": 80,
    "L2": 60,
    "L3": 30,
    "L4": 10,
}

VALID_AUTHORITY_MAPPINGS = {
    ("L0", "FHS", "core"),
    ("L1", "CHS", "supplement"),
    ("L2", "CHS", "supplement"),
    ("L3", "EHS", "candidate"),
    ("L4", "EHS", "discovery"),
}

SECRET_LIKE_KEY_MARKERS = {
    "authorization",
    "api_key",
    "api-key",
    "apikey",
    "secret",
    "token",
    "bearer",
    "password",
    "access_token",
    "refresh_token",
}


@dataclass
class Result:
    status: str
    reason_code: str
    retryable: bool = False
    data: Any | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid result status: {self.status}")
        if not self.reason_code:
            raise ValueError("reason_code is required")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_result(
    status: str,
    reason_code: str,
    *,
    retryable: bool = False,
    data: Any | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> Result:
    return Result(
        status=status,
        reason_code=reason_code,
        retryable=retryable,
        data=data,
        errors=errors or [],
        warnings=warnings or [],
    )


def ok_result(reason_code: str, data: Any | None = None) -> Result:
    return make_result("ok", reason_code, data=data)


def found_result(reason_code: str, data: Any | None = None) -> Result:
    return make_result("found", reason_code, data=data)


def warning_result(
    reason_code: str,
    data: Any | None = None,
    warnings: list[str] | None = None,
) -> Result:
    return make_result(
        "found_with_warning",
        reason_code,
        data=data,
        warnings=warnings or [],
    )


def blocked_result(reason_code: str, errors: list[str] | None = None) -> Result:
    return make_result(
        "blocked",
        reason_code,
        retryable=False,
        errors=errors or [],
    )


def error_result(reason_code: str, errors: list[str] | None = None) -> Result:
    return make_result(
        "error",
        reason_code,
        retryable=False,
        errors=errors or [],
    )


def not_found_result(reason_code: str, warnings: list[str] | None = None) -> Result:
    return make_result(
        "not_found",
        reason_code,
        retryable=False,
        warnings=warnings or [],
    )


def validate_method(method: Any) -> Result:
    if not isinstance(method, str):
        return error_result("INVALID_API_METHOD", ["method must be a string"])

    normalized = method.upper().strip()
    if normalized not in VALID_METHODS:
        return error_result(
            "INVALID_API_METHOD",
            [f"method must be one of {sorted(VALID_METHODS)}"],
        )

    return ok_result("VALID_API_METHOD", {"method": normalized})


def validate_path(path: Any) -> Result:
    if not isinstance(path, str):
        return error_result("INVALID_API_PATH", ["path must be a string"])

    normalized = path.strip()
    if not normalized.startswith("/"):
        return error_result("INVALID_API_PATH", ["path must start with /"])

    return ok_result("VALID_API_PATH", {"path": normalized})


def validate_evidence_class(evidence_class: Any) -> Result:
    if not isinstance(evidence_class, str):
        return error_result("INVALID_EVIDENCE_CLASS", ["evidence_class must be a string"])

    normalized = evidence_class.upper().strip()
    if normalized not in VALID_EVIDENCE_CLASSES:
        return error_result(
            "INVALID_EVIDENCE_CLASS",
            [f"evidence_class must be one of {sorted(VALID_EVIDENCE_CLASSES)}"],
        )

    return ok_result("VALID_EVIDENCE_CLASS", {"evidence_class": normalized})


def validate_tacl_layer(tacl_layer: Any) -> Result:
    if not isinstance(tacl_layer, str):
        return error_result("INVALID_TACL_LAYER", ["tacl_layer must be a string"])

    normalized = tacl_layer.upper().strip()
    if normalized not in VALID_TACL_LAYERS:
        return error_result(
            "INVALID_TACL_LAYER",
            [f"tacl_layer must be one of {sorted(VALID_TACL_LAYERS)}"],
        )

    return ok_result("VALID_TACL_LAYER", {"tacl_layer": normalized})


def validate_contract_role(contract_role: Any) -> Result:
    if not isinstance(contract_role, str):
        return error_result("INVALID_CONTRACT_ROLE", ["contract_role must be a string"])

    normalized = contract_role.lower().strip()
    if normalized not in VALID_CONTRACT_ROLES:
        return error_result(
            "INVALID_CONTRACT_ROLE",
            [f"contract_role must be one of {sorted(VALID_CONTRACT_ROLES)}"],
        )

    return ok_result("VALID_CONTRACT_ROLE", {"contract_role": normalized})


def validate_authority_mapping(
    tacl_layer: Any,
    evidence_class: Any,
    contract_role: Any,
) -> Result:
    layer_result = validate_tacl_layer(tacl_layer)
    if layer_result.status == "error":
        return layer_result

    evidence_result = validate_evidence_class(evidence_class)
    if evidence_result.status == "error":
        return evidence_result

    role_result = validate_contract_role(contract_role)
    if role_result.status == "error":
        return role_result

    layer = layer_result.data["tacl_layer"]
    evidence = evidence_result.data["evidence_class"]
    role = role_result.data["contract_role"]

    mapping = (layer, evidence, role)
    if mapping not in VALID_AUTHORITY_MAPPINGS:
        return blocked_result(
            "INVALID_AUTHORITY_MAPPING",
            [f"invalid authority mapping: {layer}/{evidence}/{role}"],
        )

    return ok_result(
        "VALID_AUTHORITY_MAPPING",
        {
            "tacl_layer": layer,
            "evidence_class": evidence,
            "contract_role": role,
            "authority_rank": AUTHORITY_RANKS[layer],
        },
    )


def contains_secret_like_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []

    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            current_path = f"{path}.{key_text}"

            if any(marker in lowered for marker in SECRET_LIKE_KEY_MARKERS):
                findings.append(current_path)

            findings.extend(contains_secret_like_keys(nested, current_path))

    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(contains_secret_like_keys(nested, f"{path}[{index}]"))

    return findings
