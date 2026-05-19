from __future__ import annotations

import json
from pathlib import Path


def test_sample_api_spec_json_is_valid_and_non_empty() -> None:
    sample_path = Path(__file__).resolve().parents[1] / "input" / "api_spec.example.json"

    raw = sample_path.read_text(encoding="utf-8")

    assert raw.strip(), "input/api_spec.example.json must not be empty"

    payload = json.loads(raw)

    assert payload["service_name"] == "demo-user-service"
    assert payload["api_version"] == "v1"
    assert payload["evidence_class"] == "FHS"
    assert payload["tacl_layer"] == "L0"
    assert payload["contract_role"] == "core"
    assert isinstance(payload["endpoints"], list)
    assert len(payload["endpoints"]) == 2
