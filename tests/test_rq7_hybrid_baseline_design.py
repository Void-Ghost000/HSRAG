from pathlib import Path


def test_rq7_hybrid_baseline_design_exists() -> None:
    path = Path("examples/hsrag_law/rq7_scale/RQ7_HYBRID_BASELINE_DESIGN.md")
    assert path.exists()

    text = path.read_text(encoding="utf-8")

    assert "# RQ7 Hybrid Baseline Design" in text
    assert "LOCAL_DETERMINISTIC_HYBRID" in text
    assert "HYBRID_BM25_VECTOR" in text
    assert "CTHC_PRUNED_HYBRID" in text
    assert "no external embedding API" in text
    assert "no network access" in text
    assert "no secrets" in text
    assert "hybrid_score = alpha * lexical_score + beta * vector_score" in text
    assert "This is not a state-of-the-art hybrid search engine." in text
    assert "RQ7-hybrid.2" in text
