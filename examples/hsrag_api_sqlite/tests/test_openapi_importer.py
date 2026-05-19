from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hsrag_api_sqlite.db import connect_db
from hsrag_api_sqlite.openapi_importer import (
    import_openapi_json_file,
    normalize_openapi_json,
)
from hsrag_api_sqlite.query import query_by_method_path, semantic_discovery


def openapi_sample_path() -> Path:
    return Path(__file__).resolve().parents[1] / "input" / "openapi_petstore_minimal.json"


def load_openapi_sample() -> dict:
    return json.loads(openapi_sample_path().read_text(encoding="utf-8"))


def test_openapi_sample_json_is_valid_and_non_empty() -> None:
    payload = load_openapi_sample()

    assert payload["openapi"] == "3.0.3"
    assert "paths" in payload
    assert len(payload["paths"]) == 2


def test_normalize_openapi_json_to_hsrag_spec() -> None:
    result = normalize_openapi_json(
        load_openapi_sample(),
        service_name="petstore-openapi",
        api_version="v1",
        source_type="sample_openapi_json",
        evidence_class="FHS",
        tacl_layer="L0",
        contract_role="core",
    )

    assert result.status == "ok"
    assert result.reason_code == "OPENAPI_NORMALIZED"
    assert result.data["endpoint_count"] == 3

    spec = result.data["normalized_spec"]

    assert spec["service_name"] == "petstore-openapi"
    assert spec["evidence_class"] == "FHS"
    assert spec["tacl_layer"] == "L0"
    assert spec["contract_role"] == "core"
    assert len(spec["endpoints"]) == 3


def test_import_openapi_json_file_ingests_records(tmp_path: Path) -> None:
    db_path = tmp_path / "openapi.sqlite3"
    normalized_output = tmp_path / "openapi_normalized.json"

    result = import_openapi_json_file(
        openapi_sample_path(),
        db_path=db_path,
        service_name="petstore-openapi",
        api_version="v1",
        source_type="sample_openapi_json",
        evidence_class="FHS",
        tacl_layer="L0",
        contract_role="core",
        normalized_output_path=normalized_output,
    )

    assert result.status == "ok"
    assert result.reason_code == "OPENAPI_IMPORTED"
    assert result.data["endpoint_count"] == 3
    assert normalized_output.exists()

    conn = connect_db(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM api_specs").fetchone()
    finally:
        conn.close()

    assert row["count"] == 3


def test_query_imported_openapi_endpoint_by_method_path(tmp_path: Path) -> None:
    db_path = tmp_path / "openapi.sqlite3"

    import_openapi_json_file(
        openapi_sample_path(),
        db_path=db_path,
        service_name="petstore-openapi",
        api_version="v1",
        source_type="sample_openapi_json",
        evidence_class="FHS",
        tacl_layer="L0",
        contract_role="core",
    )

    result = query_by_method_path(
        db_path,
        method="GET",
        path="/pet/{petId}",
        service_name="petstore-openapi",
        api_version="v1",
    )

    assert result.status == "found"
    assert result.reason_code == "API_SPEC_FOUND"
    assert result.data["canonical_contract"]["path"] == "/pet/{petId}"


def test_semantic_discovery_for_imported_openapi_is_candidates_only(tmp_path: Path) -> None:
    db_path = tmp_path / "openapi.sqlite3"

    import_openapi_json_file(
        openapi_sample_path(),
        db_path=db_path,
        service_name="petstore-openapi",
        api_version="v1",
        source_type="sample_openapi_json",
        evidence_class="FHS",
        tacl_layer="L0",
        contract_role="core",
    )

    result = semantic_discovery(db_path, "pet")

    assert result.status == "found_with_warning"
    assert result.reason_code == "SEMANTIC_DISCOVERY_REQUIRES_POINTER_CONFIRMATION"


def test_openapi_importer_defaults_to_ehs_candidate() -> None:
    result = normalize_openapi_json(
        load_openapi_sample(),
        service_name="petstore-openapi",
        api_version="v1",
    )

    assert result.status == "ok"

    spec = result.data["normalized_spec"]

    assert spec["evidence_class"] == "EHS"
    assert spec["tacl_layer"] == "L3"
    assert spec["contract_role"] == "candidate"


def test_openapi_importer_rejects_missing_paths() -> None:
    result = normalize_openapi_json(
        {"openapi": "3.0.3", "info": {"title": "bad"}},
        service_name="bad",
        api_version="v1",
    )

    assert result.status == "error"
    assert result.reason_code == "OPENAPI_PATHS_MISSING"


def test_openapi_importer_rejects_remote_url() -> None:
    result = import_openapi_json_file(
        "https://example.com/openapi.json",
        db_path=":memory:",
        service_name="remote",
        api_version="v1",
    )

    assert result.status == "error"
    assert result.reason_code == "OPENAPI_FILE_READ_FAILED"


def test_openapi_importer_cli_runs_end_to_end(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "src" / "hsrag_api_sqlite" / "openapi_importer.py"
    db_path = tmp_path / "openapi_cli.sqlite3"
    normalized_output = tmp_path / "openapi_cli_normalized.json"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(openapi_sample_path()),
            "--db",
            str(db_path),
            "--service-name",
            "petstore-openapi",
            "--api-version",
            "v1",
            "--source-type",
            "sample_openapi_json",
            "--evidence-class",
            "FHS",
            "--tacl-layer",
            "L0",
            "--contract-role",
            "core",
            "--normalized-output",
            str(normalized_output),
        ],
        cwd=str(project_root),
        text=True,
        capture_output=True,
        check=True,
    )

    assert db_path.exists(), result.stdout + result.stderr
    assert normalized_output.exists(), result.stdout + result.stderr

    report = json.loads(result.stdout)

    assert report["status"] == "ok"
    assert report["reason_code"] == "OPENAPI_IMPORTED"
    assert report["data"]["endpoint_count"] == 3
