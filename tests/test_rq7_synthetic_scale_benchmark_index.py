from pathlib import Path


def test_rq7_synthetic_scale_benchmark_indexed_from_root_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "## RQ7 Synthetic Scale Benchmark" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.md" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.json" in text
    assert "examples/hsrag_law/rq7_scale/05_reports/RQ7_SYNTHETIC_SCALE_BENCHMARK.csv" in text
    assert "Synthetic expansion is not new legal corpus." in text
    assert "run_rq7_synthetic_scale_benchmark.py --target-sizes 1000,5000,10000" in text


def test_rq7_synthetic_scale_benchmark_indexed_from_law_readme() -> None:
    text = Path("examples/hsrag_law/README.md").read_text(encoding="utf-8")

    assert "## RQ7 Synthetic Scale Benchmark" in text
    assert "RQ7_SYNTHETIC_SCALE_BENCHMARK.md" in text
    assert "1,000 chunks" in text
    assert "5,000 chunks" in text
    assert "10,000 chunks" in text
    assert "This is not a full-scale real-law corpus benchmark." in text


def test_rq7_synthetic_scale_benchmark_indexed_from_evidence_summary() -> None:
    text = Path("examples/hsrag_law/rq7_scale/RQ7_EVIDENCE_SUMMARY.md").read_text(encoding="utf-8")

    assert "## RQ7 Synthetic Scale Benchmark" in text
    assert "RQ7_SYNTHETIC_SCALE_BENCHMARK.csv" in text
    assert "Synthetic chunks are explicitly labeled." in text
    assert "This is a scale stress benchmark only." in text
    assert "Local deterministic vector / hybrid baselines are available; production embedding / vector database baselines are still pending." in text

