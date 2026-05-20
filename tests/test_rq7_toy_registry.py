from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("examples/hsrag_law/rq7_scale")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_rq7_chunk_registry_exists_and_has_cthc_addresses() -> None:
    registry = load_json(ROOT / "02_input" / "chunk_registry.example.json")
    chunks = registry["chunks"]

    assert chunks

    for chunk in chunks:
        assert chunk["chunk_id"]
        assert chunk["domain"]
        assert chunk["jurisdiction"]
        assert chunk["corpus"]
        assert chunk["unit"]
        assert chunk["cthc_address"].startswith("cthc://")
        assert chunk["source_hash"].startswith("sha256:")
        assert chunk["text"]
