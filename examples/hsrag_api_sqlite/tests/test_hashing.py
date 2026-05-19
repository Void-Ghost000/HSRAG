from __future__ import annotations

import pytest

from hsrag_api_sqlite.hashing import (
    canonical_authority_string,
    canonical_cthc_string,
    canonical_json,
    make_authority_hash,
    make_cthc_address,
    make_cthc_hash,
    make_source_hash,
    sha256_text,
)


def test_canonical_json_is_deterministic() -> None:
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}

    assert canonical_json(a) == canonical_json(b)


def test_sha256_text_is_deterministic() -> None:
    first = sha256_text("hello")
    second = sha256_text("hello")

    assert first == second
    assert first.startswith("sha256:")


def test_canonical_cthc_string_normalizes_method_and_service() -> None:
    cthc = canonical_cthc_string(
        service_name="Demo-Service",
        api_version="v1",
        method="get",
        path="/users/{id}",
    )

    assert cthc == "API|demo-service|v1|GET|/users/{id}"


def test_make_cthc_address_is_deterministic() -> None:
    first = make_cthc_address("Demo-Service", "v1", "get", "/users/{id}")
    second = make_cthc_address("demo-service", "v1", "GET", "/users/{id}")

    assert first == second
    assert first == "cthc://api/demo-service/v1/GET/users/{id}"


def test_make_cthc_hash_is_deterministic() -> None:
    first = make_cthc_hash("Demo-Service", "v1", "get", "/users/{id}")
    second = make_cthc_hash("demo-service", "v1", "GET", "/users/{id}")

    assert first == second
    assert first.startswith("sha256:")


def test_canonical_authority_string() -> None:
    value = canonical_authority_string("l0", "fhs", "Core")

    assert value == "TACL|L0|FHS|core"


def test_make_authority_hash_is_deterministic() -> None:
    first = make_authority_hash("l0", "fhs", "Core")
    second = make_authority_hash("L0", "FHS", "core")

    assert first == second
    assert first.startswith("sha256:")


def test_make_authority_hash_rejects_invalid_mapping() -> None:
    with pytest.raises(ValueError):
        make_authority_hash("L0", "EHS", "core")


def test_source_hash_is_deterministic_for_key_order() -> None:
    a = {
        "method": "GET",
        "path": "/users/{id}",
        "responses": {
            "200": {"description": "ok"},
            "404": {"description": "missing"},
        },
    }
    b = {
        "responses": {
            "404": {"description": "missing"},
            "200": {"description": "ok"},
        },
        "path": "/users/{id}",
        "method": "GET",
    }

    assert make_source_hash(a) == make_source_hash(b)


def test_source_hash_changes_when_contract_changes() -> None:
    old = {
        "method": "GET",
        "path": "/users/{id}",
        "responses": {
            "200": {"description": "ok"},
        },
    }
    new = {
        "method": "GET",
        "path": "/users/{id}",
        "responses": {
            "200": {"description": "ok"},
            "404": {"description": "missing"},
        },
    }

    assert make_source_hash(old) != make_source_hash(new)
