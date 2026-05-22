from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path("examples/hsrag_law/rq7_scale")
MODULE_PATH = ROOT / "scripts" / "local_hash_vector.py"


def load_module():
    spec = importlib.util.spec_from_file_location("local_hash_vector", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_hash_vectorizer_is_local_deterministic() -> None:
    module = load_module()

    assert module.LOCAL_ONLY is True
    assert module.ZERO_NETWORK is True
    assert module.ZERO_SECRET is True
    assert module.DETERMINISTIC is True

    a = module.vectorize_text("EU AI Act Article 5 prohibited AI practices")
    b = module.vectorize_text("EU AI Act Article 5 prohibited AI practices")

    assert a == b
    assert a


def test_local_hash_vectorizer_cosine_similarity_orders_relevant_doc() -> None:
    module = load_module()

    docs = [
        {
            "chunk_id": "irrelevant",
            "cthc_address": "cthc://LAW/US/US_CDA230/SECTION_230/irrelevant",
            "text": "interactive computer service platform liability section 230",
        },
        {
            "chunk_id": "target",
            "cthc_address": "cthc://LAW/EU/EU_AI_ACT/ARTICLE_5/target",
            "text": "EU AI Act Article 5 prohibited artificial intelligence practices",
        },
    ]

    ranked = module.rank_documents(
        "EU AI Act Article 5 prohibited AI practices",
        docs,
        top_k=2,
    )

    assert ranked[0]["document"]["chunk_id"] == "target"
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_local_hash_vectorizer_tie_break_is_deterministic() -> None:
    module = load_module()

    docs = [
        {
            "chunk_id": "b",
            "cthc_address": "cthc://LAW/EU/X/B",
            "text": "same same",
        },
        {
            "chunk_id": "a",
            "cthc_address": "cthc://LAW/EU/X/A",
            "text": "same same",
        },
    ]

    ranked_a = module.rank_documents("same", docs, top_k=2)
    ranked_b = module.rank_documents("same", docs, top_k=2)

    assert ranked_a == ranked_b
    assert [item["document"]["chunk_id"] for item in ranked_a] == ["a", "b"]


def test_local_hash_vectorizer_cli_runs_on_toy_registry(tmp_path: Path) -> None:
    registry = {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "chunks": [
            {
                "chunk_id": "eu_article_5",
                "cthc_address": "cthc://LAW/EU/EU_AI_ACT/ARTICLE_5/eu_article_5",
                "text": "EU AI Act Article 5 prohibited AI practices",
            },
            {
                "chunk_id": "us_230",
                "cthc_address": "cthc://LAW/US/US_CDA230/SECTION_230/us_230",
                "text": "Section 230 interactive computer service liability",
            },
        ],
    }

    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--query",
            "EU AI Act Article 5",
            "--registry",
            str(registry_path),
            "--top-k",
            "1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout)

    assert summary["status"] == "OK"
    assert summary["local_only"] is True
    assert summary["zero_network"] is True
    assert summary["zero_secret"] is True
    assert summary["deterministic"] is True
    assert summary["result_count"] == 1
    assert summary["results"][0]["document"]["chunk_id"] == "eu_article_5"


def test_local_hash_vectorizer_rejects_missing_registry(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--query",
            "EU AI Act",
            "--registry",
            str(tmp_path / "missing.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "REGISTRY_NOT_FOUND" in result.stderr or "REGISTRY_NOT_FOUND" in result.stdout
