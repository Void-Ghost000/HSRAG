from pathlib import Path


def test_rq7_vector_baseline_design_exists() -> None:
    path = Path("examples/hsrag_law/rq7_scale/RQ7_VECTOR_BASELINE_DESIGN.md")
    assert path.exists()

    text = path.read_text(encoding="utf-8")

    assert "# RQ7 Vector Baseline Design" in text
    assert "LOCAL_DETERMINISTIC_VECTOR" in text
    assert "no external embedding API" in text
    assert "no network access" in text
    assert "no secrets" in text
    assert "VECTOR_GLOBAL" in text
    assert "CTHC_PRUNED_VECTOR" in text
    assert "This baseline is not a state-of-the-art vector search engine." in text
    assert "RQ7-vector.2" in text
