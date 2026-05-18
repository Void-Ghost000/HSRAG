"""
Tests for HSRAG CTHC route detection.

These tests align with RQ5.5 and RQ6:
- stable legal identifiers can open routes
- generic legal wording cannot open routes
- fragmented U.S.C. citations are reconstructed
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hsrag.cthc import (
    conflict_query_signal,
    contains_unsupported_topic,
    detect_route_openers,
    detect_us_code_fragment_routes,
    generic_ambiguous_signal,
    normalize_text,
)


def test_detects_eu_ai_act_route_opener() -> None:
    assert detect_route_openers("Find EU AI Act Article 5 prohibited AI practices.") == [
        "EU_AI_ACT"
    ]


def test_detects_eu_dma_route_opener() -> None:
    assert detect_route_openers("Find EU DMA gatekeeper obligations.") == ["EU_DMA"]


def test_detects_us_cda230_fragmented_usc_citation() -> None:
    assert detect_us_code_fragment_routes("Under 47 U.S.C. 230, what rule is described?") == [
        "US_CDA230"
    ]


def test_detects_us_ftc_act5_fragmented_usc_citation() -> None:
    assert detect_us_code_fragment_routes("Under 15 U.S.C. 45, what rule is described?") == [
        "US_FTC_ACT5"
    ]


def test_generic_platform_law_does_not_open_route() -> None:
    assert detect_route_openers("What does the platform law say about online services?") == []
    assert generic_ambiguous_signal("What does the platform law say about online services?") is True


def test_unsupported_topic_is_detected() -> None:
    assert contains_unsupported_topic("What does Canada's PIPEDA require?") is True


def test_conflict_query_signal_detects_multiple_identifiers() -> None:
    detected = detect_route_openers(
        "Compare EU AI Act Article 5 with U.S. FTC Act Section 5."
    )

    assert "EU_AI_ACT" in detected
    assert "US_FTC_ACT5" in detected
    assert conflict_query_signal(
        "Compare EU AI Act Article 5 with U.S. FTC Act Section 5.",
        detected,
    ) is True


def test_normalize_text_handles_light_typos() -> None:
    assert "article" in normalize_text("Artcle 5")
    assert "section" in normalize_text("Secton 230")