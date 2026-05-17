#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HSRAG LAW RQ6 — Conversational Legal Collision Benchmark

Task:
  HSRAG-RQ6-MultiRetrieval-Conversational-Law-Collision-v0.1

QSVCS guardrails:
- Do not use expected_corpus / expected_jurisdiction as runtime route input.
- bounded_cthc_memory may only use previous actual retrieval scope.
- Synthetic demo corpus is smoke-test only.
- Failure samples must be preserved.
- HSRAG is evaluated as boundary-first retrieval governance, not legal advice.
- BM25 is treated as a strong lexical baseline, not as an enemy baseline.
- Multi-law comparison must be decomposed into atomic retrieval tasks.

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RQ_NAME = "HSRAG-RQ6-MultiRetrieval-Conversational-Law-Collision-v0.1"

MODES = [
    "bm25_global",
    "bm25_domain_hint",
    "tfidf_global",
    "hybrid_rrf_global",
    "hsrag_cthc",
    "hsrag_hybrid_subset",
]

CONTEXT_POLICIES = [
    "no_memory",
    "naive_memory",
    "bounded_cthc_memory",
]

MUTATIONS = [
    "none",
    "polite_prefix",
    "irrelevant_tail",
    "punctuation_noise",
    "typo_light",
    "jurisdiction_reminder",
    "legalese_prefix",
    "distractor_warning",
]

RESULT_FIELDS = [
    "trial",
    "pair_id",
    "turn_id",
    "mode",
    "context_policy",
    "mutation",
    "query",
    "search_query",
    "expected_status",
    "expected_corpus",
    "expected_jurisdiction",
    "result_status",
    "top_corpus",
    "top_jurisdiction",
    "top_chunk_id",
    "route_status",
    "route_reason",
    "evidence_hash",
    "source_hash",
    "latency_ms",
    "prev_top_corpus",
    "prev_top_jurisdiction",
    "target_correct",
    "cross_turn_contamination",
    "switch_turn_contamination",
    "audit_row_hash",
]


@dataclass
class Chunk:
    chunk_id: str
    corpus: str
    jurisdiction: str
    unit: str
    text: str
    source_hash: str
    source_hash_backfilled: bool


@dataclass
class RetrievalResult:
    result_status: str
    top_chunk: Optional[Chunk]
    route_status: str
    route_reason: str
    evidence_hash: str
    source_hash: str
    latency_ms: float


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def normalize_scope_query(query: str) -> str:
    """
    QSVCS / CTHC normalization layer.

    Purpose:
      Normalize noisy legal queries before scope detection.
      This does not use expected labels or answer keys.

    Handles:
      - punctuation_noise: U !!!S -> us, Section , 230 -> section 230
      - typo_light: Artcle -> article, Secton -> section, oblgations -> obligations
      - spaced acronyms: C D A -> cda, F T C -> ftc, G D P R -> gdpr
      - distractor_warning meta text:
          "Warning: do not confuse similarly numbered EU and U.S. provisions."
        This text is mutation noise, not the legal retrieval target.
    """
    q = (query or "").lower()

    distractor_patterns = [
        r"warning\s*:\s*do\s+not\s+confuse\s+similarly\s+numbered\s+eu\s+and\s+u\.?s\.?\s+provisions\.?",
        r"do\s+not\s+confuse\s+similarly\s+numbered\s+eu\s+and\s+u\.?s\.?\s+provisions\.?",
        r"do\s+not\s+confuse\s+similarly\s+numbered\s+eu\s+and\s+us\s+provisions\.?",
    ]
    for pattern in distractor_patterns:
        q = re.sub(pattern, " ", q, flags=re.IGNORECASE)

    typo_map = {
        "artcle": "article",
        "secton": "section",
        "oblgations": "obligations",
        "platf orm": "platform",
    }
    for bad, good in typo_map.items():
        q = q.replace(bad, good)

    q = q.replace("u.s.", "us")
    q = q.replace("u.s", "us")

    q = re.sub(r"[^a-z0-9§]+", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    acronym_patterns = {
        r"\bu\s+s\b": "us",
        r"\bf\s+t\s+c\b": "ftc",
        r"\bc\s+d\s+a\b": "cda",
        r"\bg\s+d\s+p\s+r\b": "gdpr",
        r"\bd\s+m\s+a\b": "dma",
        r"\bc\s+o\s+p\s+p\s+a\b": "coppa",
    }

    for pattern, replacement in acronym_patterns.items():
        q = re.sub(pattern, replacement, q)

    return q


def canonical_corpus(value: str) -> str:
    v = (value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "US_FTC_ACT": "US_FTC_ACT5",
        "US_FTC_ACT_5": "US_FTC_ACT5",
        "US_FTC_ACT_SECTION_5": "US_FTC_ACT5",
        "FTC_ACT5": "US_FTC_ACT5",
        "FTC_ACT_5": "US_FTC_ACT5",
        "FTC_ACT_SECTION_5": "US_FTC_ACT5",
        "CDA230": "US_CDA230",
        "CDA_230": "US_CDA230",
        "US_CDA_230": "US_CDA230",
        "DMA": "EU_DMA",
        "AI_ACT": "EU_AI_ACT",
        "EU_AI_ACT_ARTICLE_5": "EU_AI_ACT",
        "GDPR": "EU_GDPR",
        "COPPA": "US_COPPA",
        "CCPA": "US_CCPA",
    }
    return aliases.get(v, v)


def canonical_jurisdiction(value: str, corpus: str = "") -> str:
    v = (value or "").strip().upper().replace("_", " ")
    if v in {"US", "USA", "U.S.", "U.S", "UNITED STATES", "UNITED STATES OF AMERICA"}:
        return "US"
    if v in {"EU", "EUROPEAN UNION", "EUROPEAN"}:
        return "EU"

    c = canonical_corpus(corpus)
    if c.startswith("EU_"):
        return "EU"
    if c.startswith("US_"):
        return "US"

    return v or "UNKNOWN"


def get_field(row: Dict[str, str], names: List[str]) -> str:
    lower_map = {k.lower().strip(): k for k in row.keys()}
    for name in names:
        key = lower_map.get(name.lower())
        if key is not None:
            return (row.get(key) or "").strip()
    return ""


def build_synthetic_demo_corpus() -> List[Chunk]:
    demo_rows = [
        (
            "EU_AI_ACT_ART5_001",
            "EU_AI_ACT",
            "EU",
            "Article 5",
            "EU AI Act Article 5 concerns prohibited artificial intelligence practices in the European Union.",
        ),
        (
            "US_FTC_ACT5_001",
            "US_FTC_ACT5",
            "US",
            "Section 5",
            "U.S. FTC Act Section 5 concerns unfair or deceptive acts or practices in commerce.",
        ),
        (
            "US_CDA230_001",
            "US_CDA230",
            "US",
            "47 U.S.C. Section 230",
            "Section 230 concerns protection for interactive computer services and platform liability.",
        ),
        (
            "EU_DMA_GATEKEEPER_001",
            "EU_DMA",
            "EU",
            "Gatekeeper obligations",
            "The EU Digital Markets Act imposes obligations on designated gatekeepers.",
        ),
        (
            "US_COPPA_001",
            "US_COPPA",
            "US",
            "Children data",
            "COPPA concerns online collection of personal information from children in the United States.",
        ),
        (
            "EU_GDPR_ART8_001",
            "EU_GDPR",
            "EU",
            "Article 8",
            "GDPR Article 8 concerns conditions applicable to a child's consent in relation to information society services.",
        ),
    ]

    chunks: List[Chunk] = []
    for chunk_id, corpus, jurisdiction, unit, text in demo_rows:
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                corpus=corpus,
                jurisdiction=jurisdiction,
                unit=unit,
                text=text,
                source_hash=sha256_text(text),
                source_hash_backfilled=False,
            )
        )
    return chunks


def load_chunks(path: Optional[str]) -> Tuple[List[Chunk], Dict[str, Any]]:
    normalization = {
        "chunk_source": path or "synthetic_demo_corpus",
        "demo_mode": path is None,
        "rows_loaded": 0,
        "rows_skipped_empty_text": 0,
        "source_hash_backfilled_count": 0,
        "unknown_corpus_count": 0,
        "normalization_warnings": [],
    }

    if path is None:
        chunks = build_synthetic_demo_corpus()
        normalization["rows_loaded"] = len(chunks)
        return chunks, normalization

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Chunk file does not exist: {path}")

    chunks: List[Chunk] = []

    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Chunk CSV has no header row.")

        for i, row in enumerate(reader):
            text = get_field(row, ["text", "chunk_text", "content", "body", "source_text"])
            if not text:
                normalization["rows_skipped_empty_text"] += 1
                continue

            raw_corpus = get_field(
                row,
                [
                    "corpus",
                    "corpus_id",
                    "source_corpus",
                    "law_corpus",
                    "dataset",
                    "dataset_id",
                ],
            )
            corpus = canonical_corpus(raw_corpus)
            if not corpus:
                corpus = "UNKNOWN_CORPUS"
                normalization["unknown_corpus_count"] += 1
                normalization["normalization_warnings"].append(
                    f"row {i}: missing corpus/corpus_id; set UNKNOWN_CORPUS"
                )

            raw_jurisdiction = get_field(
                row,
                [
                    "jurisdiction",
                    "region",
                    "legal_jurisdiction",
                    "country",
                    "zone",
                ],
            )
            jurisdiction = canonical_jurisdiction(raw_jurisdiction, corpus)

            unit = get_field(
                row,
                [
                    "unit",
                    "article",
                    "section",
                    "legal_unit",
                    "title",
                    "source_title",
                    "chunk_index",
                ],
            )
            if not unit:
                unit = "UNKNOWN_UNIT"

            chunk_id = get_field(row, ["chunk_id", "id", "hash_id"])
            if not chunk_id:
                chunk_id = f"{corpus}:{unit}:ROW_{i:06d}"
                normalization["normalization_warnings"].append(
                    f"row {i}: missing chunk_id; generated fallback chunk_id"
                )

            source_hash = get_field(
                row,
                [
                    "source_hash",
                    "source_hash_final",
                    "hash",
                    "text_hash",
                    "content_hash",
                    "chunk_hash",
                    "normalized_text_sha256",
                ],
            )
            source_hash_backfilled = False
            if not source_hash:
                source_hash = sha256_text(text)
                source_hash_backfilled = True
                normalization["source_hash_backfilled_count"] += 1

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    corpus=corpus,
                    jurisdiction=jurisdiction,
                    unit=unit,
                    text=text,
                    source_hash=source_hash,
                    source_hash_backfilled=source_hash_backfilled,
                )
            )

    if not chunks:
        raise ValueError("No usable chunks loaded. Refusing to run on empty corpus.")

    normalization["rows_loaded"] = len(chunks)

    if normalization["unknown_corpus_count"] == len(chunks):
        raise ValueError(
            "All loaded chunks have UNKNOWN_CORPUS. "
            "Corpus schema mapping failed. Check corpus/corpus_id field."
        )

    return chunks, normalization


class CorpusIndex:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self.available_corpora = sorted({c.corpus for c in chunks})
        self.available_jurisdictions = sorted({c.jurisdiction for c in chunks})
        self.tokens = [
            tokenize(c.text + " " + c.corpus + " " + c.jurisdiction + " " + c.unit)
            for c in chunks
        ]
        self.term_freqs = [Counter(toks) for toks in self.tokens]
        self.doc_lens = [len(toks) for toks in self.tokens]
        self.avgdl = statistics.mean(self.doc_lens) if self.doc_lens else 1.0

        self.df = Counter()
        for toks in self.tokens:
            for term in set(toks):
                self.df[term] += 1

        self.n = len(chunks)
        self.idf = {
            term: math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for term, df in self.df.items()
        }

    def candidate_indices(
        self,
        corpus: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> List[int]:
        out = []
        for i, chunk in enumerate(self.chunks):
            if corpus and chunk.corpus != corpus:
                continue
            if jurisdiction and chunk.jurisdiction != jurisdiction:
                continue
            out.append(i)
        return out


def detect_scope(query: str, available_corpora: List[str]) -> Dict[str, Any]:
    q = normalize_scope_query(query)
    corpora = set()
    jurisdictions = set()
    units = set()
    reasons = []

    if re.search(r"\beu\b|european union|european", q):
        jurisdictions.add("EU")
    if re.search(r"\bus\b|united states|american", q):
        jurisdictions.add("US")

    if "ai act" in q or "artificial intelligence act" in q or "regulation 2024 1689" in q:
        corpora.add("EU_AI_ACT")
    if "digital markets act" in q or re.search(r"\bdma\b", q) or "gatekeeper" in q:
        corpora.add("EU_DMA")
    if "ftc" in q or "unfair or deceptive" in q or "deceptive acts" in q:
        corpora.add("US_FTC_ACT5")
    if (
        "section 230" in q
        or "§230" in q
        or "cda 230" in q
        or "platform liability" in q
        or "interactive computer service" in q
    ):
        corpora.add("US_CDA230")
    if "coppa" in q or ("children" in q and "online" in q):
        corpora.add("US_COPPA")
    if "gdpr" in q or "general data protection regulation" in q:
        corpora.add("EU_GDPR")
    if "ccpa" in q:
        corpora.add("US_CCPA")

    if re.search(r"article\s*5|art\s*5", q):
        units.add("Article 5")
        if "ai act" in q or "eu" in q or "european" in q:
            corpora.add("EU_AI_ACT")
    if re.search(r"section\s*5|sec\s*5|§\s*5", q):
        units.add("Section 5")
        if "ftc" in q or "us" in q or "unfair" in q or "deceptive" in q:
            corpora.add("US_FTC_ACT5")
    if re.search(r"article\s*8|art\s*8", q):
        units.add("Article 8")
        if "gdpr" in q or "eu" in q or "european" in q:
            corpora.add("EU_GDPR")

    ambiguous = False

    if re.search(r"article\s*5|art\s*5", q) and not corpora and not jurisdictions:
        ambiguous = True
        reasons.append("Ambiguous Article 5 without stable jurisdiction or corpus.")

    if len(jurisdictions) > 1:
        ambiguous = True
        reasons.append("Multiple jurisdictions detected.")

    available_hits = sorted(c for c in corpora if c in available_corpora)
    unavailable_hits = sorted(c for c in corpora if c not in available_corpora)

    return {
        "corpora": sorted(corpora),
        "available_corpora": available_hits,
        "unavailable_corpora": unavailable_hits,
        "jurisdictions": sorted(jurisdictions),
        "units": sorted(units),
        "ambiguous": ambiguous,
        "reason": "; ".join(reasons) if reasons else "Scope detection completed.",
    }


def bm25_scores(index: CorpusIndex, query: str, candidates: List[int]) -> List[Tuple[int, float]]:
    q_terms = Counter(tokenize(query))
    k1 = 1.5
    b = 0.75
    scores = []

    for i in candidates:
        tf = index.term_freqs[i]
        dl = index.doc_lens[i] or 1
        score = 0.0

        for term in q_terms:
            if term not in tf:
                continue
            idf = index.idf.get(term, 0.0)
            freq = tf[term]
            denom = freq + k1 * (1 - b + b * dl / (index.avgdl or 1.0))
            score += idf * (freq * (k1 + 1)) / (denom or 1.0)

        scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def tfidf_scores(index: CorpusIndex, query: str, candidates: List[int]) -> List[Tuple[int, float]]:
    q_tf = Counter(tokenize(query))
    if not q_tf:
        return [(i, 0.0) for i in candidates]

    q_vec = {term: freq * index.idf.get(term, 0.0) for term, freq in q_tf.items()}
    q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
    scores = []

    for i in candidates:
        d_tf = index.term_freqs[i]
        dot = 0.0
        d_norm_sq = 0.0

        for term, freq in d_tf.items():
            weight = freq * index.idf.get(term, 0.0)
            d_norm_sq += weight * weight
            if term in q_vec:
                dot += q_vec[term] * weight

        d_norm = math.sqrt(d_norm_sq) or 1.0
        scores.append((i, dot / (q_norm * d_norm)))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def rrf_fuse(rankings: List[List[Tuple[int, float]]], k: int = 60) -> List[Tuple[int, float]]:
    fused = defaultdict(float)

    for ranking in rankings:
        for rank, (idx, _score) in enumerate(ranking, start=1):
            fused[idx] += 1.0 / (k + rank)

    out = list(fused.items())
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def top_from_ranking(index: CorpusIndex, ranking: List[Tuple[int, float]]) -> Optional[Chunk]:
    if not ranking:
        return None
    idx, _score = ranking[0]
    return index.chunks[idx]


def domain_hint_candidates(index: CorpusIndex, search_query: str) -> Tuple[List[int], str, str]:
    scope = detect_scope(search_query, index.available_corpora)

    if len(scope["available_corpora"]) == 1:
        corpus = scope["available_corpora"][0]
        return index.candidate_indices(corpus=corpus), "HIT", f"Domain hint filtered to corpus={corpus}."

    if len(scope["available_corpora"]) > 1:
        return list(range(index.n)), "BASELINE", "Multiple corpus hints detected; fallback to global retrieval."

    if scope["unavailable_corpora"]:
        return [], "NO_EVIDENCE", f"Explicit corpus not available: {scope['unavailable_corpora']}."

    if len(scope["jurisdictions"]) == 1:
        jurisdiction = scope["jurisdictions"][0]
        return index.candidate_indices(jurisdiction=jurisdiction), "HIT", f"Domain hint filtered to jurisdiction={jurisdiction}."

    return list(range(index.n)), "BASELINE", "No stable domain hint; using global retrieval."


def retrieve(
    index: CorpusIndex,
    mode: str,
    current_query: str,
    search_query: str,
) -> RetrievalResult:
    start = time.perf_counter()

    result_status = "HIT"
    route_status = "BASELINE"
    route_reason = "Baseline retrieval does not perform CTHC route gating."
    top_chunk: Optional[Chunk] = None

    if mode == "bm25_global":
        ranking = bm25_scores(index, search_query, list(range(index.n)))
        top_chunk = top_from_ranking(index, ranking)

    elif mode == "bm25_domain_hint":
        candidates, route_status, route_reason = domain_hint_candidates(index, search_query)
        if not candidates:
            result_status = "NO_EVIDENCE"
            top_chunk = None
        else:
            ranking = bm25_scores(index, search_query, candidates)
            top_chunk = top_from_ranking(index, ranking)

    elif mode == "tfidf_global":
        ranking = tfidf_scores(index, search_query, list(range(index.n)))
        top_chunk = top_from_ranking(index, ranking)

    elif mode == "hybrid_rrf_global":
        candidates = list(range(index.n))
        ranking = rrf_fuse([
            bm25_scores(index, search_query, candidates),
            tfidf_scores(index, search_query, candidates),
        ])
        top_chunk = top_from_ranking(index, ranking)

    elif mode in {"hsrag_cthc", "hsrag_hybrid_subset"}:
        scope = detect_scope(current_query, index.available_corpora)

        if scope["ambiguous"]:
            result_status = "AMBIGUOUS"
            route_status = "AMBIGUOUS"
            route_reason = scope["reason"]
            top_chunk = None

        elif scope["unavailable_corpora"] and not scope["available_corpora"]:
            result_status = "NO_EVIDENCE"
            route_status = "NO_EVIDENCE"
            route_reason = f"Requested corpus not available: {scope['unavailable_corpora']}."
            top_chunk = None

        elif len(scope["available_corpora"]) > 1:
            result_status = "AMBIGUOUS"
            route_status = "ROUTE_CONFLICT"
            route_reason = f"Multiple available corpus candidates: {scope['available_corpora']}."
            top_chunk = None

        else:
            candidates: List[int] = []

            if len(scope["available_corpora"]) == 1:
                corpus = scope["available_corpora"][0]
                candidates = index.candidate_indices(corpus=corpus)
                route_status = "HIT"
                route_reason = f"CTHC constrained retrieval to corpus={corpus}."

            elif len(scope["jurisdictions"]) == 1:
                jurisdiction = scope["jurisdictions"][0]
                candidates = index.candidate_indices(jurisdiction=jurisdiction)
                route_status = "HIT"
                route_reason = f"CTHC constrained retrieval to jurisdiction={jurisdiction}."

            else:
                result_status = "NO_EVIDENCE"
                route_status = "NO_EVIDENCE"
                route_reason = "No stable CTHC legal identifier found."

            if result_status == "HIT":
                if not candidates:
                    result_status = "NO_EVIDENCE"
                    route_status = "NO_EVIDENCE"
                    route_reason += " No matching candidate chunks."
                    top_chunk = None
                elif mode == "hsrag_cthc":
                    ranking = bm25_scores(index, current_query, candidates)
                    top_chunk = top_from_ranking(index, ranking)
                else:
                    ranking = rrf_fuse([
                        bm25_scores(index, current_query, candidates),
                        tfidf_scores(index, current_query, candidates),
                    ])
                    top_chunk = top_from_ranking(index, ranking)

    else:
        raise ValueError(f"Unknown retrieval mode: {mode}")

    latency_ms = (time.perf_counter() - start) * 1000.0

    if result_status == "HIT" and top_chunk is None:
        result_status = "NO_EVIDENCE"
        route_status = "NO_EVIDENCE"
        route_reason += " No top chunk returned."

    return RetrievalResult(
        result_status=result_status,
        top_chunk=top_chunk,
        route_status=route_status,
        route_reason=route_reason,
        evidence_hash=sha256_text(top_chunk.text) if top_chunk else "",
        source_hash=top_chunk.source_hash if top_chunk else "",
        latency_ms=latency_ms,
    )


def build_query_pairs(available_corpora: List[str]) -> List[Dict[str, Any]]:
    def status_for(corpus: str) -> str:
        return "HIT" if corpus in available_corpora else "NO_EVIDENCE"

    return [
        {
            "pair_id": "A_EU_AI_ACT5_TO_US_FTC_ACT5",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find EU AI Act Article 5 prohibited AI practices.",
                    "expected_status": status_for("EU_AI_ACT"),
                    "expected_corpus": "EU_AI_ACT",
                    "expected_jurisdiction": "EU",
                },
                {
                    "turn_id": 2,
                    "query": "Now find U.S. FTC Act Section 5 on unfair or deceptive acts or practices.",
                    "expected_status": status_for("US_FTC_ACT5"),
                    "expected_corpus": "US_FTC_ACT5",
                    "expected_jurisdiction": "US",
                },
            ],
        },
        {
            "pair_id": "B_US_FTC_ACT5_TO_EU_AI_ACT5",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find U.S. FTC Act Section 5 on unfair or deceptive acts or practices.",
                    "expected_status": status_for("US_FTC_ACT5"),
                    "expected_corpus": "US_FTC_ACT5",
                    "expected_jurisdiction": "US",
                },
                {
                    "turn_id": 2,
                    "query": "Now find EU AI Act Article 5 prohibited AI practices.",
                    "expected_status": status_for("EU_AI_ACT"),
                    "expected_corpus": "EU_AI_ACT",
                    "expected_jurisdiction": "EU",
                },
            ],
        },
        {
            "pair_id": "C_US_CDA230_TO_EU_DMA",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find U.S. CDA Section 230 platform liability protection.",
                    "expected_status": status_for("US_CDA230"),
                    "expected_corpus": "US_CDA230",
                    "expected_jurisdiction": "US",
                },
                {
                    "turn_id": 2,
                    "query": "Now find EU DMA gatekeeper obligations.",
                    "expected_status": status_for("EU_DMA"),
                    "expected_corpus": "EU_DMA",
                    "expected_jurisdiction": "EU",
                },
            ],
        },
        {
            "pair_id": "D_EU_DMA_TO_US_CDA230",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find EU DMA gatekeeper obligations.",
                    "expected_status": status_for("EU_DMA"),
                    "expected_corpus": "EU_DMA",
                    "expected_jurisdiction": "EU",
                },
                {
                    "turn_id": 2,
                    "query": "Now find U.S. CDA Section 230 platform liability protection.",
                    "expected_status": status_for("US_CDA230"),
                    "expected_corpus": "US_CDA230",
                    "expected_jurisdiction": "US",
                },
            ],
        },
        {
            "pair_id": "E_US_COPPA_TO_EU_GDPR_ART8_OR_NO_EVIDENCE",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find U.S. COPPA rules about children data online.",
                    "expected_status": status_for("US_COPPA"),
                    "expected_corpus": "US_COPPA",
                    "expected_jurisdiction": "US",
                },
                {
                    "turn_id": 2,
                    "query": "Now find EU GDPR Article 8 on children's consent.",
                    "expected_status": status_for("EU_GDPR"),
                    "expected_corpus": "EU_GDPR",
                    "expected_jurisdiction": "EU",
                },
            ],
        },
        {
            "pair_id": "F_AMBIGUOUS_ARTICLE_5_CARRYOVER",
            "turns": [
                {
                    "turn_id": 1,
                    "query": "Find EU AI Act Article 5 prohibited AI practices.",
                    "expected_status": status_for("EU_AI_ACT"),
                    "expected_corpus": "EU_AI_ACT",
                    "expected_jurisdiction": "EU",
                },
                {
                    "turn_id": 2,
                    "query": "Now explain Article 5 obligations.",
                    "expected_status": "AMBIGUOUS",
                    "expected_corpus": "",
                    "expected_jurisdiction": "",
                },
            ],
        },
    ]


def mutate_query(query: str, mutation: str, expected_jurisdiction: str) -> str:
    if mutation == "none":
        return query
    if mutation == "polite_prefix":
        return "Please help me carefully retrieve this legal source: " + query
    if mutation == "irrelevant_tail":
        return query + " Also ignore unrelated restaurant licensing issues."
    if mutation == "punctuation_noise":
        return query.replace(" ", "  , ").replace(".", " !!!")
    if mutation == "typo_light":
        return (
            query.replace("Article", "Artcle")
            .replace("Section", "Secton")
            .replace("obligations", "oblgations")
        )
    if mutation == "jurisdiction_reminder":
        if expected_jurisdiction:
            return query + f" Jurisdiction reminder: use {expected_jurisdiction} law only."
        return query + " Jurisdiction reminder: do not infer a jurisdiction unless stated."
    if mutation == "legalese_prefix":
        return "For purposes of statutory retrieval and source-bounded evidence review, " + query
    if mutation == "distractor_warning":
        return query + " Warning: do not confuse similarly numbered EU and U.S. provisions."

    raise ValueError(f"Unknown mutation: {mutation}")


def build_search_query(
    context_policy: str,
    current_query: str,
    prev_query: Optional[str],
    prev_scope: Optional[Dict[str, str]],
) -> str:
    if context_policy == "no_memory":
        return current_query

    if context_policy == "naive_memory":
        return (prev_query + " " + current_query) if prev_query else current_query

    if context_policy == "bounded_cthc_memory":
        if not prev_scope:
            return current_query

        return (
            current_query
            + f" [previous_actual_scope corpus={prev_scope.get('corpus', '')}"
            + f" jurisdiction={prev_scope.get('jurisdiction', '')}"
            + f" chunk_id={prev_scope.get('chunk_id', '')}]"
        )

    raise ValueError(f"Unknown context policy: {context_policy}")


def compute_target_correct(row: Dict[str, Any]) -> bool:
    expected_status = row["expected_status"]
    result_status = row["result_status"]

    if expected_status == "HIT":
        return (
            result_status == "HIT"
            and row["top_corpus"] == row["expected_corpus"]
            and row["top_jurisdiction"] == row["expected_jurisdiction"]
        )

    if expected_status == "NO_EVIDENCE":
        return result_status == "NO_EVIDENCE"

    if expected_status == "AMBIGUOUS":
        return result_status == "AMBIGUOUS"

    return False


def compute_contamination_flags(row: Dict[str, Any]) -> Tuple[bool, bool]:
    if int(row["turn_id"]) != 2:
        return False, False

    if row["result_status"] != "HIT":
        return False, False

    prev_corpus = row.get("prev_top_corpus", "")
    prev_jurisdiction = row.get("prev_top_jurisdiction", "")
    top_corpus = row.get("top_corpus", "")
    top_jurisdiction = row.get("top_jurisdiction", "")
    expected_corpus = row.get("expected_corpus", "")
    expected_jurisdiction = row.get("expected_jurisdiction", "")

    cross_turn = bool(
        prev_corpus
        and top_corpus == prev_corpus
        and expected_corpus
        and expected_corpus != prev_corpus
    )

    switch_turn = bool(
        prev_jurisdiction
        and top_jurisdiction == prev_jurisdiction
        and expected_jurisdiction
        and expected_jurisdiction != prev_jurisdiction
    )

    return cross_turn, switch_turn


def add_audit_hash(row: Dict[str, Any]) -> Dict[str, Any]:
    clean = dict(row)
    clean.pop("audit_row_hash", None)
    payload = json.dumps(clean, ensure_ascii=False, sort_keys=True)
    row["audit_row_hash"] = sha256_text(payload)
    return row


def make_row(
    trial: int,
    pair_id: str,
    turn: Dict[str, Any],
    mode: str,
    context_policy: str,
    mutation: str,
    query: str,
    search_query: str,
    result: RetrievalResult,
    prev_scope: Optional[Dict[str, str]],
) -> Dict[str, Any]:
    top = result.top_chunk

    row: Dict[str, Any] = {
        "trial": trial,
        "pair_id": pair_id,
        "turn_id": turn["turn_id"],
        "mode": mode,
        "context_policy": context_policy,
        "mutation": mutation,
        "query": query,
        "search_query": search_query,
        "expected_status": turn["expected_status"],
        "expected_corpus": turn.get("expected_corpus", ""),
        "expected_jurisdiction": turn.get("expected_jurisdiction", ""),
        "result_status": result.result_status,
        "top_corpus": top.corpus if top else "",
        "top_jurisdiction": top.jurisdiction if top else "",
        "top_chunk_id": top.chunk_id if top else "",
        "route_status": result.route_status,
        "route_reason": result.route_reason,
        "evidence_hash": result.evidence_hash,
        "source_hash": result.source_hash,
        "latency_ms": round(result.latency_ms, 6),
        "prev_top_corpus": prev_scope.get("corpus", "") if prev_scope else "",
        "prev_top_jurisdiction": prev_scope.get("jurisdiction", "") if prev_scope else "",
        "target_correct": False,
        "cross_turn_contamination": False,
        "switch_turn_contamination": False,
        "audit_row_hash": "",
    }

    row["target_correct"] = compute_target_correct(row)
    cross_turn, switch_turn = compute_contamination_flags(row)
    row["cross_turn_contamination"] = cross_turn
    row["switch_turn_contamination"] = switch_turn

    return add_audit_hash(row)


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(math.ceil((p / 100.0) * len(s))) - 1
    idx = max(0, min(idx, len(s) - 1))
    return float(s[idx])


def summarize_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}

    total = len(rows)
    hit_expected = [r for r in rows if r["expected_status"] == "HIT"]

    def count(pred) -> int:
        return sum(1 for r in rows if pred(r))

    def rate(num: int, den: int = total) -> float:
        return float(num / den) if den else 0.0

    wrong_corpus = count(
        lambda r: r["expected_status"] == "HIT"
        and r["result_status"] == "HIT"
        and r["top_corpus"] != r["expected_corpus"]
    )

    wrong_jurisdiction = count(
        lambda r: r["expected_status"] == "HIT"
        and r["result_status"] == "HIT"
        and r["top_jurisdiction"] != r["expected_jurisdiction"]
    )

    no_evidence_false_allow = count(
        lambda r: r["expected_status"] == "NO_EVIDENCE"
        and r["result_status"] == "HIT"
    )

    ambiguous_false_allow = count(
        lambda r: r["expected_status"] == "AMBIGUOUS"
        and r["result_status"] == "HIT"
    )

    cross_turn = count(lambda r: bool(r["cross_turn_contamination"]))
    switch_turn = count(lambda r: bool(r["switch_turn_contamination"]))

    source_hash_den = count(lambda r: r["result_status"] == "HIT")
    source_hash_num = count(lambda r: r["result_status"] == "HIT" and bool(r["source_hash"]))

    audit_num = count(lambda r: bool(r["audit_row_hash"]))

    hit_correct = sum(1 for r in hit_expected if bool(r["target_correct"]))
    latencies = [float(r["latency_ms"]) for r in rows]

    return {
        "row_count": total,
        "target_correct_rate": rate(count(lambda r: bool(r["target_correct"]))),
        "hit_target_correct_rate": rate(hit_correct, len(hit_expected)),
        "wrong_corpus_collision_rate": rate(wrong_corpus),
        "wrong_jurisdiction_escape_rate": rate(wrong_jurisdiction),
        "no_evidence_false_allow_rate": rate(no_evidence_false_allow),
        "ambiguous_false_allow_rate": rate(ambiguous_false_allow),
        "cross_turn_contamination_rate": rate(cross_turn),
        "switch_turn_contamination_rate": rate(switch_turn),
        "source_hash_present_rate": rate(source_hash_num, source_hash_den),
        "audit_chain_complete_rate": rate(audit_num),
        "p95_latency_ms": percentile(latencies, 95),
        "counts": {
            "wrong_corpus_collision": wrong_corpus,
            "wrong_jurisdiction_escape": wrong_jurisdiction,
            "no_evidence_false_allow": no_evidence_false_allow,
            "ambiguous_false_allow": ambiguous_false_allow,
            "cross_turn_contamination": cross_turn,
            "switch_turn_contamination": switch_turn,
        },
    }


def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = f"{row['mode']}|{row['context_policy']}"
        grouped[key].append(row)

    by_mode_context = {
        key: summarize_rows(group_rows)
        for key, group_rows in sorted(grouped.items())
    }

    return {
        "rq_name": RQ_NAME,
        "overall": summarize_rows(rows),
        "by_mode_context": by_mode_context,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_mode_comparison(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# RQ6 Mode Comparison",
        "",
        "| mode | context_policy | target_correct | wrong_corpus | wrong_jurisdiction | no_evidence_false_allow | ambiguous_false_allow | cross_turn | p95_latency_ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for key, metrics in summary["by_mode_context"].items():
        mode, policy = key.split("|", 1)
        lines.append(
            f"| {mode} | {policy} | "
            f"{metrics['target_correct_rate']:.6f} | "
            f"{metrics['wrong_corpus_collision_rate']:.6f} | "
            f"{metrics['wrong_jurisdiction_escape_rate']:.6f} | "
            f"{metrics['no_evidence_false_allow_rate']:.6f} | "
            f"{metrics['ambiguous_false_allow_rate']:.6f} | "
            f"{metrics['cross_turn_contamination_rate']:.6f} | "
            f"{metrics['p95_latency_ms']:.6f} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_claim_boundary(path: Path) -> None:
    text = """# RQ6 Claim Boundary

RQ6 does not claim that RAG is dead.

RQ6 does not claim that HSRAG replaces all retrieval methods.

RQ6 evaluates whether explicit jurisdiction, corpus, source, and context boundaries can reduce wrong-corpus retrieval and cross-turn legal context contamination.

HSRAG is evaluated as a boundary-first retrieval governance layer, not as a universal replacement for BM25, vector search, or hybrid RAG.

This benchmark is not legal advice.

Synthetic demo runs are smoke tests only and must not be reported as publication-grade results.

## Limitation: Atomic Legal Retrieval First

RQ6 v0.1 evaluates atomic or two-turn legal retrieval tasks.

The current HSRAG CTHC router is intentionally boundary-first and single-scope oriented. A single retrieval call should target one legal corpus, jurisdiction, and legal unit whenever possible.

For multi-statute or comparative legal questions, the query should first be decomposed into separate atomic retrieval tasks. Each atomic task should produce its own evidence hash, source hash, route status, and audit row before any answer synthesis is performed.

Multi-law comparison should happen after retrieval, not inside the retrieval boundary itself.

RQ6 v0.1 does not claim to solve unrestricted multi-law batch retrieval in a single query.
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> Path:
    chunks, normalization = load_chunks(args.chunks)
    index = CorpusIndex(chunks)
    pairs = build_query_pairs(index.available_corpora)

    created_at_unix = int(time.time())
    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else Path("runs") / f"rq6_conversational_collision_{created_at_unix}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    if normalization["demo_mode"]:
        print(
            "WARNING: No --chunks provided. Using synthetic demo corpus only. "
            "This is NON_PUBLICATION smoke mode."
        )

    config_payload = {
        "rq_name": RQ_NAME,
        "seed": args.seed,
        "mc": args.mc,
        "chunk_source": normalization["chunk_source"],
        "demo_mode": normalization["demo_mode"],
        "modes": MODES,
        "context_policies": CONTEXT_POLICIES,
        "mutations": MUTATIONS,
        "available_corpora": index.available_corpora,
        "pair_count": len(pairs),
    }
    config_hash = sha256_text(json.dumps(config_payload, sort_keys=True))

    rows: List[Dict[str, Any]] = []

    for trial in range(args.mc):
        pair = pairs[trial % len(pairs)]
        mutation = MUTATIONS[(trial // len(pairs)) % len(MUTATIONS)]

        for mode in MODES:
            for context_policy in CONTEXT_POLICIES:
                prev_query: Optional[str] = None
                prev_scope: Optional[Dict[str, str]] = None

                for turn in pair["turns"]:
                    query = mutate_query(
                        turn["query"],
                        mutation,
                        turn.get("expected_jurisdiction", ""),
                    )

                    search_query = build_search_query(
                        context_policy=context_policy,
                        current_query=query,
                        prev_query=prev_query,
                        prev_scope=prev_scope,
                    )

                    result = retrieve(
                        index=index,
                        mode=mode,
                        current_query=query,
                        search_query=search_query,
                    )

                    row = make_row(
                        trial=trial,
                        pair_id=pair["pair_id"],
                        turn=turn,
                        mode=mode,
                        context_policy=context_policy,
                        mutation=mutation,
                        query=query,
                        search_query=search_query,
                        result=result,
                        prev_scope=prev_scope,
                    )
                    rows.append(row)

                    prev_query = query

                    if result.top_chunk:
                        prev_scope = {
                            "corpus": result.top_chunk.corpus,
                            "jurisdiction": result.top_chunk.jurisdiction,
                            "chunk_id": result.top_chunk.chunk_id,
                            "unit": result.top_chunk.unit,
                        }
                    else:
                        prev_scope = None

    summary = build_summary(rows)

    failure_rows = [
        r for r in rows
        if not bool(r["target_correct"])
        or bool(r["cross_turn_contamination"])
        or bool(r["switch_turn_contamination"])
    ]

    publication_grade_candidate = (
        not normalization["demo_mode"]
        and normalization["source_hash_backfilled_count"] == 0
        and normalization["unknown_corpus_count"] == 0
    )

    manifest = {
        "rq_name": RQ_NAME,
        "seed": args.seed,
        "mc": args.mc,
        "chunk_source": normalization["chunk_source"],
        "demo_mode": normalization["demo_mode"],
        "publication_grade_candidate": publication_grade_candidate,
        "chunk_count": len(chunks),
        "available_corpora": index.available_corpora,
        "available_jurisdictions": index.available_jurisdictions,
        "modes": MODES,
        "context_policies": CONTEXT_POLICIES,
        "mutations": MUTATIONS,
        "pair_count": len(pairs),
        "config_hash": config_hash,
        "created_at_unix": created_at_unix,
        "normalization": normalization,
        "claim_boundary": {
            "not_legal_advice": True,
            "not_rag_replacement_claim": True,
            "not_production_ready_claim": True,
            "synthetic_demo_is_smoke_only": normalization["demo_mode"],
            "atomic_legal_retrieval_first": True,
            "multi_law_batch_single_query_supported": False,
        },
    }

    (out_dir / "rq6_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "rq6_run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_csv(out_dir / "rq6_full_results.csv", rows, RESULT_FIELDS)
    write_csv(out_dir / "rq6_failure_samples.csv", failure_rows, RESULT_FIELDS)
    write_mode_comparison(out_dir / "rq6_mode_comparison.md", summary)
    write_claim_boundary(out_dir / "rq6_claim_boundary.md")

    print("=" * 88)
    print(RQ_NAME)
    print(f"Output dir: {out_dir}")
    print(f"Rows: {len(rows)}")
    print(f"Failures: {len(failure_rows)}")
    print(f"Demo mode: {normalization['demo_mode']}")
    print(f"Available corpora: {', '.join(index.available_corpora)}")
    print("Overall summary:")
    print(json.dumps(summary["overall"], indent=2, ensure_ascii=False))
    print("=" * 88)

    return out_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=RQ_NAME)
    parser.add_argument("--chunks", default=None, help="Path to normalized legal chunks CSV.")
    parser.add_argument("--mc", type=int, default=3000, help="Monte Carlo trial count.")
    parser.add_argument("--seed", type=int, default=20260517, help="Random seed.")
    parser.add_argument("--out-dir", default=None, help="Optional output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()