from pathlib import Path


def test_rq7_readme_explains_qoim_and_csp_directories() -> None:
    readme = Path("examples/hsrag_law/rq7_scale/README.md")
    text = readme.read_text(encoding="utf-8")

    assert "## Directory Map" in text
    assert "00_qoim" in text
    assert "01_csp" in text
    assert "experiment intent" in text
    assert "causal skeleton" in text
    assert "Global search must not use domain salt for pruning" in text
    assert "Full-scale RQ7 benchmark: not implemented yet" in text
