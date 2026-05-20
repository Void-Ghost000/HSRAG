from pathlib import Path


def test_rq7_is_indexed_from_law_readme() -> None:
    path = Path("examples/hsrag_law/README.md")
    text = path.read_text(encoding="utf-8")

    assert "## RQ7 Scale Benchmark" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py" in text
    assert "salted toy-real retrieval pipeline: verified" in text
    assert "full-scale RQ7 benchmark: not implemented yet" in text
    assert "It does not claim that HSRAG replaces all RAG systems." in text


def test_rq7_is_indexed_from_root_readme() -> None:
    path = Path("README.md")
    text = path.read_text(encoding="utf-8")

    assert "## HSRAG RQ7 Scale Benchmark" in text
    assert "examples/hsrag_law/rq7_scale/" in text
    assert "python examples/hsrag_law/rq7_scale/scripts/verify_rq7.py" in text
    assert "full-scale benchmark pending" in text
