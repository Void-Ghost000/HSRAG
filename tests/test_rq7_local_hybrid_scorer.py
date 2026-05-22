from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path("examples/hsrag_law/rq7_scale/scripts/local_hybrid_scorer.py")


def load_module():
    spec = importlib.util.spec_from_file_location("local_hybrid_scorer", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_hybrid_scorer_is_local_deterministic() -> None:
    module = load_module()

    assert module.LOCAL_ONLY is True
    assert module.ZERO_NETWORK is True
    assert module.ZERO_SECRET is True
    assert module.DETERMINISTIC is True

    a = module.hybrid_score("EU AI Act Article 5", "EU AI Act Article 5 prohibited AI practices")
    b = module.hybrid_score("EU AI Act Article 5", "EU AI Act Article 5 prohibited AI practices")

    assert a == b
    assert a["hybrid_score"] > 0


def test_local_hybrid_scorer_orders_relevant_document() -> None:
    module = load_module()

    docs = [
        {"chunk_id": "bad", "cthc_address": "b", "text": "Section 230 platform liability"},
        {"chunk_id": "good", "cthc_address": "a", "text": "EU AI Act Article 5 prohibited AI practices"},
    ]

    ranked = module.rank_documents("EU AI Act Article 5 prohibited practices", docs, top_k=2)

    assert ranked[0]["document"]["chunk_id"] == "good"


def test_local_hybrid_scorer_rejects_invalid_weights() -> None:
    module = load_module()

    try:
        module.hybrid_score("query", "doc", alpha=0, beta=0)
    except ValueError as exc:
        assert "INVALID_HYBRID_WEIGHTS" in str(exc)
    else:
        raise AssertionError("Expected INVALID_HYBRID_WEIGHTS")
