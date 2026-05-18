"""
Tests for HSRAG salted hash routing.

These tests align with RQ5.5:
CTHC typed route + salted domain hash retrieval.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hsrag.hash_router import (
    BENCHMARK_SALT,
    default_cthc_code,
    route_key_for_corpus,
    salted_domain_hash,
)


def test_salted_domain_hash_is_deterministic() -> None:
    code = default_cthc_code(corpus_id="EU_AI_ACT")

    h1 = salted_domain_hash(code, salt=BENCHMARK_SALT)
    h2 = salted_domain_hash(code, salt=BENCHMARK_SALT)

    assert h1 == h2
    assert h1.startswith("sha256:")


def test_different_corpus_produces_different_domain_hash() -> None:
    eu_ai = route_key_for_corpus(corpus_id="EU_AI_ACT")
    eu_dma = route_key_for_corpus(corpus_id="EU_DMA")

    assert eu_ai != eu_dma


def test_different_jurisdiction_produces_different_domain_hash() -> None:
    us_ccpa_default = route_key_for_corpus(corpus_id="US_CCPA")
    us_ccpa_forced_us = route_key_for_corpus(corpus_id="US_CCPA", jurisdiction="US")

    assert us_ccpa_default != us_ccpa_forced_us


def test_different_salt_produces_different_domain_hash() -> None:
    code = default_cthc_code(corpus_id="US_CDA230")

    h1 = salted_domain_hash(code, salt="salt-a")
    h2 = salted_domain_hash(code, salt="salt-b")

    assert h1 != h2


def test_default_cthc_code_path_matches_legal_boundary() -> None:
    code = default_cthc_code(corpus_id="US_FTC_ACT5")

    assert code.domain == "LEGAL"
    assert code.source_type == "PUBLIC_LEGAL_TEXT"
    assert code.jurisdiction == "US"
    assert code.corpus_id == "US_FTC_ACT5"
    assert code.path() == "LEGAL.PUBLIC_LEGAL_TEXT.US.US_FTC_ACT5.GENERAL"