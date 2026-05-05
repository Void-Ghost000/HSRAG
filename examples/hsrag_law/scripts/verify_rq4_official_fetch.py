"""
HSRAG LAW — RQ4.1 Official/Public Source Fetch & Rebuild
========================================================

RQ4.1 = Official/Public Legal Source Fetch & Rebuild Smoke Test

This script attempts to fetch official or public legal source URLs, normalize
their text, produce source hashes, chunk hashes, and an auditable source rebuild
manifest.

RQ4.1 patch notes:
- Adds multiple candidate URLs per corpus.
- Distinguishes live fetch success from source rebuild success.
- Treats extractable warning pages as rebuild-usable when they produce text,
  chunks, source hashes, normalized-text hashes, and chunk hashes.
- Keeps EUR-Lex / official fetch gate warnings visible instead of pretending
  that every official URL is directly script-fetchable.
- Uses public legal references as fallback candidates where official pages
  are difficult for simple urllib clients.

QSVCS annotations:
- CTHC: classify each source by corpus_id / jurisdiction / source_type.
- QOIM: enforce source rebuild feasibility gates.
- SGF: execute fetch -> normalize -> chunk -> audit in fixed forward order.
- VPSM: represent each source and chunk as structured verification vectors.
- Audit-S: write append-only hash chain over the source rebuild process.

Run from repository root:

    python examples/hsrag_law/scripts/verify_rq4_official_fetch.py --min-ok 2

Strict command:

    python examples/hsrag_law/scripts/verify_rq4_official_fetch.py --strict
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


# =============================================================================
# Path resolution
# =============================================================================

THIS_FILE = Path(__file__).resolve()

if THIS_FILE.parent.name == "scripts":
    EXAMPLE_ROOT = THIS_FILE.parent.parent
else:
    EXAMPLE_ROOT = THIS_FILE.parent

REPO_ROOT = EXAMPLE_ROOT.parents[1] if len(EXAMPLE_ROOT.parents) >= 2 else EXAMPLE_ROOT
DATA_DIR = EXAMPLE_ROOT / "data"
RESULTS_DIR = EXAMPLE_ROOT / "results"


# =============================================================================
# Source manifest
# =============================================================================

DEFAULT_RQ4_SOURCE_MANIFEST: List[Dict[str, Any]] = [
    {
        "corpus_id": "EU_AI_ACT",
        "jurisdiction": "EU",
        "source_title": "Regulation (EU) 2024/1689 — Artificial Intelligence Act",
        "source_type": "OFFICIAL_EU_EUR_LEX_ELI_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng",
                "candidate_type": "OFFICIAL_EU_EUR_LEX_ELI",
                "notes": "Official EUR-Lex ELI URL; may return JavaScript / robot verification page in simple fetch clients.",
            },
            {
                "url": "https://artificialintelligenceact.eu/the-act/",
                "candidate_type": "PUBLIC_REFERENCE_AI_ACT_EXPLORER",
                "notes": "Public reference fallback for extractability smoke test.",
            },
        ],
    },
    {
        "corpus_id": "EU_DMA",
        "jurisdiction": "EU",
        "source_title": "Regulation (EU) 2022/1925 — Digital Markets Act",
        "source_type": "OFFICIAL_EU_EUR_LEX_ELI_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://eur-lex.europa.eu/eli/reg/2022/1925/oj/eng",
                "candidate_type": "OFFICIAL_EU_EUR_LEX_ELI",
                "notes": "Official EUR-Lex ELI URL; may return JavaScript / robot verification page in simple fetch clients.",
            },
            {
                "url": "https://digital-markets-act.ec.europa.eu/about-dma_en",
                "candidate_type": "OFFICIAL_EC_PUBLIC_REFERENCE",
                "notes": "European Commission public reference page, not full legal text.",
            },
        ],
    },
    {
        "corpus_id": "US_COPPA",
        "jurisdiction": "US",
        "source_title": "16 CFR Part 312 — Children's Online Privacy Protection Rule",
        "source_type": "OFFICIAL_US_ECFR_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312",
                "candidate_type": "OFFICIAL_US_ECFR",
                "notes": "Official eCFR page for COPPA Rule.",
            },
            {
                "url": "https://www.law.cornell.edu/cfr/text/16/part-312",
                "candidate_type": "PUBLIC_REFERENCE_CORNELL_LII_CFR",
                "notes": "Cornell LII CFR reference fallback.",
            },
        ],
    },
    {
        "corpus_id": "US_CDA230",
        "jurisdiction": "US",
        "source_title": "47 U.S.C. Section 230",
        "source_type": "OFFICIAL_US_CODE_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title47-section230&num=0&edition=prelim",
                "candidate_type": "OFFICIAL_US_CODE_HOUSE",
                "notes": "U.S. Code House page; simple urllib may fail on some machines.",
            },
            {
                "url": "https://www.law.cornell.edu/uscode/text/47/230",
                "candidate_type": "PUBLIC_REFERENCE_CORNELL_LII_USCODE",
                "notes": "Cornell LII U.S. Code reference fallback.",
            },
        ],
    },
    {
        "corpus_id": "US_FTC_ACT5",
        "jurisdiction": "US",
        "source_title": "15 U.S.C. Section 45 — FTC Act Section 5",
        "source_type": "OFFICIAL_US_CODE_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title15-section45&num=0&edition=prelim",
                "candidate_type": "OFFICIAL_US_CODE_HOUSE",
                "notes": "U.S. Code House page; simple urllib may fail on some machines.",
            },
            {
                "url": "https://www.law.cornell.edu/uscode/text/15/45",
                "candidate_type": "PUBLIC_REFERENCE_CORNELL_LII_USCODE",
                "notes": "Cornell LII U.S. Code reference fallback.",
            },
        ],
    },
    {
        "corpus_id": "US_CCPA",
        "jurisdiction": "US-CA",
        "source_title": "California Consumer Privacy Act / CCPA",
        "source_type": "OFFICIAL_CA_REFERENCE_WITH_PUBLIC_REFERENCE_FALLBACK",
        "hard_gate": False,
        "candidate_urls": [
            {
                "url": "https://oag.ca.gov/privacy/ccpa",
                "candidate_type": "OFFICIAL_CA_OAG_REFERENCE",
                "notes": "California Attorney General CCPA public reference page.",
            },
            {
                "url": "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5",
                "candidate_type": "OFFICIAL_CA_LEGINFO_REFERENCE",
                "notes": "California Legislative Information CCPA code page; may be dynamic.",
            },
        ],
    },
]


# =============================================================================
# Data models
# =============================================================================

@dataclass
class FetchAttempt:
    corpus_id: str
    jurisdiction: str
    source_title: str
    source_url: str
    candidate_type: str
    fetch_decision: str
    http_status: Optional[int]
    content_type: Optional[str]
    byte_length: int
    raw_sha256: Optional[str]
    normalized_text_sha256: Optional[str]
    normalized_text_length: int
    chunk_count: int
    legal_signal_score: int
    suspicious_gate_page: bool
    elapsed_ms: float
    error: Optional[str]


@dataclass
class SourceRecord:
    corpus_id: str
    jurisdiction: str
    source_title: str
    selected_source_url: str
    selected_candidate_type: str
    source_type: str
    hard_gate: bool
    fetch_decision: str
    rebuild_usable: bool
    http_status: Optional[int]
    content_type: Optional[str]
    byte_length: int
    raw_sha256: Optional[str]
    normalized_text_sha256: Optional[str]
    normalized_text_length: int
    chunk_count: int
    legal_signal_score: int
    suspicious_gate_page: bool
    elapsed_ms: float
    error: Optional[str]


@dataclass
class ChunkRecord:
    chunk_id: str
    corpus_id: str
    jurisdiction: str
    source_title: str
    source_url: str
    candidate_type: str
    source_hash: str
    normalized_text_sha256: str
    chunk_index: int
    chunk_hash: str
    char_start: int
    char_end: int
    text: str


@dataclass
class GateCheck:
    gate_id: str
    description: str
    expected: Any
    actual: Any
    passed: bool
    severity: str


@dataclass
class AuditEvent:
    index: int
    event_type: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str


# =============================================================================
# Utility functions
# =============================================================================

def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_dataclass_csv(path: Path, rows: Sequence[Any]) -> None:
    if not rows:
        # Still create an empty marker file for audit visibility.
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def normalize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit(parsed)


def load_or_create_manifest() -> List[Dict[str, Any]]:
    manifest_path = DATA_DIR / "rq4_source_manifest.json"

    if not manifest_path.exists():
        write_json(manifest_path, DEFAULT_RQ4_SOURCE_MANIFEST)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    if not isinstance(payload, list):
        raise ValueError("rq4_source_manifest.json must contain a JSON list.")

    # Backward compatibility: if an older manifest uses source_url, transform it.
    normalized: List[Dict[str, Any]] = []
    for item in payload:
        if "candidate_urls" not in item and "source_url" in item:
            item = dict(item)
            item["candidate_urls"] = [
                {
                    "url": item["source_url"],
                    "candidate_type": item.get("source_type", "LEGACY_SINGLE_URL"),
                    "notes": "Legacy single URL converted to candidate_urls.",
                }
            ]
        normalized.append(item)

    return normalized


# =============================================================================
# Fetch
# =============================================================================

def read_limited(response: Any, max_bytes: int) -> bytes:
    chunks: List[bytes] = []
    remaining = max_bytes

    while remaining > 0:
        block = response.read(min(65536, remaining))
        if not block:
            break
        chunks.append(block)
        remaining -= len(block)

    return b"".join(chunks)


def fetch_raw(url: str, timeout: float, max_bytes: int) -> Tuple[str, Optional[int], Optional[str], bytes, Optional[str], float]:
    started = time.perf_counter()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 HSRAG-LAW-RQ4.1-SourceRebuild/0.1 "
                "(research source rebuild smoke test)"
            ),
            "Accept": "text/html,application/xhtml+xml,text/plain,application/xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            content_type = response.headers.get("Content-Type")
            raw = read_limited(response, max_bytes=max_bytes)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return "FETCH_RAW_OK", status, content_type, raw, None, elapsed_ms

    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return "FETCH_HTTP_ERROR", exc.code, None, b"", str(exc), elapsed_ms

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return "FETCH_ERROR", None, None, b"", repr(exc), elapsed_ms


# =============================================================================
# Normalize / detect
# =============================================================================

def strip_html_to_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")

    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", text)
    text = re.sub(r"(?is)<svg.*?>.*?</svg>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)

    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(raw: bytes, content_type: Optional[str]) -> str:
    lowered = (content_type or "").lower()

    if "pdf" in lowered:
        # stdlib-only script: no PDF extraction here.
        return ""

    return strip_html_to_text(raw)


def is_suspicious_gate_page(text: str) -> bool:
    lowered = text.lower()

    gate_patterns = [
        "javascript is disabled",
        "verify that you're not a robot",
        "verify you are human",
        "enable javascript",
        "captcha",
        "access denied",
        "cloudflare",
        "bot verification",
        "robot verification",
    ]

    return any(pattern in lowered for pattern in gate_patterns)


def legal_signal_score(corpus_id: str, text: str) -> int:
    lowered = text.lower()

    common_signals = [
        "section",
        "article",
        "regulation",
        "code",
        "shall",
        "law",
        "consumer",
        "provider",
        "commission",
    ]

    corpus_signals = {
        "EU_AI_ACT": [
            "artificial intelligence",
            "high-risk",
            "ai system",
            "risk management",
            "regulation (eu) 2024/1689",
        ],
        "EU_DMA": [
            "digital markets act",
            "gatekeeper",
            "core platform services",
            "regulation (eu) 2022/1925",
        ],
        "US_COPPA": [
            "children's online privacy",
            "coppa",
            "parental consent",
            "operator",
            "child",
        ],
        "US_CDA230": [
            "section 230",
            "interactive computer service",
            "publisher",
            "information content provider",
        ],
        "US_FTC_ACT5": [
            "unfair or deceptive",
            "federal trade commission",
            "section 45",
            "competition",
        ],
        "US_CCPA": [
            "california consumer",
            "personal information",
            "consumer privacy",
            "ccpa",
        ],
    }

    score = 0
    for signal in common_signals:
        if signal in lowered:
            score += 1

    for signal in corpus_signals.get(corpus_id, []):
        if signal in lowered:
            score += 2

    return score


# =============================================================================
# Chunk
# =============================================================================

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[Tuple[int, int, str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0:
        raise ValueError("overlap must be non-negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    cleaned = re.sub(r"\s+", " ", text).strip()

    if not cleaned:
        return []

    chunks: List[Tuple[int, int, str]] = []
    start = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append((start, end, chunk))

        if end >= len(cleaned):
            break

        start = max(0, end - overlap)

    return chunks


def build_chunks_for_attempt(
    source: Dict[str, Any],
    attempt: FetchAttempt,
    normalized_text: str,
    chunk_size: int,
    overlap: int,
) -> List[ChunkRecord]:
    if not attempt.raw_sha256 or not attempt.normalized_text_sha256:
        return []

    source_chunks = chunk_text(normalized_text, chunk_size=chunk_size, overlap=overlap)
    output: List[ChunkRecord] = []

    for index, (char_start, char_end, text) in enumerate(source_chunks):
        chunk_payload = {
            "corpus_id": attempt.corpus_id,
            "jurisdiction": attempt.jurisdiction,
            "source_url": attempt.source_url,
            "candidate_type": attempt.candidate_type,
            "source_hash": attempt.raw_sha256,
            "normalized_text_sha256": attempt.normalized_text_sha256,
            "chunk_index": index,
            "text": text,
        }
        chunk_hash = stable_json_hash(chunk_payload)

        output.append(
            ChunkRecord(
                chunk_id=f"{attempt.corpus_id}_RQ4_CHUNK_{index:04d}",
                corpus_id=attempt.corpus_id,
                jurisdiction=attempt.jurisdiction,
                source_title=attempt.source_title,
                source_url=attempt.source_url,
                candidate_type=attempt.candidate_type,
                source_hash=attempt.raw_sha256,
                normalized_text_sha256=attempt.normalized_text_sha256,
                chunk_index=index,
                chunk_hash=chunk_hash,
                char_start=char_start,
                char_end=char_end,
                text=text,
            )
        )

    return output


# =============================================================================
# Classify attempt / select best
# =============================================================================

def classify_fetch_decision(
    raw_decision: str,
    normalized_text: str,
    suspicious_gate: bool,
    min_text_chars: int,
    chunk_count: int,
    signal_score: int,
) -> str:
    if raw_decision != "FETCH_RAW_OK":
        return raw_decision

    if len(normalized_text) < min_text_chars:
        return "FETCH_WARN_SHORT_TEXT"

    if chunk_count <= 0:
        return "FETCH_WARN_NO_CHUNKS"

    if suspicious_gate and signal_score < 2:
        return "FETCH_WARN_GATE_PAGE"

    if suspicious_gate and signal_score >= 2:
        return "FETCH_WARN_EXTRACTABLE"

    if signal_score < 2:
        return "FETCH_WARN_LOW_LEGAL_SIGNAL"

    return "FETCH_OK"


def is_rebuild_usable(decision: str, chunk_count: int, normalized_text_len: int) -> bool:
    return (
        decision in {"FETCH_OK", "FETCH_WARN_EXTRACTABLE", "FETCH_WARN_LOW_LEGAL_SIGNAL"}
        and chunk_count > 0
        and normalized_text_len > 0
    )


def run_candidate_attempt(
    source: Dict[str, Any],
    candidate: Dict[str, Any],
    timeout: float,
    max_bytes: int,
    min_text_chars: int,
    chunk_size: int,
    overlap: int,
) -> Tuple[FetchAttempt, List[ChunkRecord]]:
    corpus_id = str(source.get("corpus_id", "UNKNOWN"))
    jurisdiction = str(source.get("jurisdiction", "UNKNOWN"))
    source_title = str(source.get("source_title", "UNKNOWN"))

    source_url = normalize_url(str(candidate.get("url", "")))
    candidate_type = str(candidate.get("candidate_type", "UNKNOWN_CANDIDATE"))

    if not source_url.startswith(("http://", "https://")):
        attempt = FetchAttempt(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            candidate_type=candidate_type,
            fetch_decision="FETCH_INVALID_URL",
            http_status=None,
            content_type=None,
            byte_length=0,
            raw_sha256=None,
            normalized_text_sha256=None,
            normalized_text_length=0,
            chunk_count=0,
            legal_signal_score=0,
            suspicious_gate_page=False,
            elapsed_ms=0.0,
            error="Invalid URL.",
        )
        return attempt, []

    raw_decision, status, content_type, raw, error, elapsed_ms = fetch_raw(
        source_url,
        timeout=timeout,
        max_bytes=max_bytes,
    )

    normalized = ""
    normalized_hash: Optional[str] = None
    raw_hash: Optional[str] = None
    suspicious = False
    signal_score = 0
    chunks: List[ChunkRecord] = []

    if raw:
        raw_hash = sha256_bytes(raw)
        normalized = normalize_text(raw, content_type)
        suspicious = is_suspicious_gate_page(normalized)
        signal_score = legal_signal_score(corpus_id, normalized)
        normalized_hash = stable_json_hash(
            {
                "corpus_id": corpus_id,
                "source_url": source_url,
                "candidate_type": candidate_type,
                "normalized_text": normalized,
            }
        )

        provisional_attempt = FetchAttempt(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            candidate_type=candidate_type,
            fetch_decision="PROVISIONAL",
            http_status=status,
            content_type=content_type,
            byte_length=len(raw),
            raw_sha256=raw_hash,
            normalized_text_sha256=normalized_hash,
            normalized_text_length=len(normalized),
            chunk_count=0,
            legal_signal_score=signal_score,
            suspicious_gate_page=suspicious,
            elapsed_ms=elapsed_ms,
            error=error,
        )

        chunks = build_chunks_for_attempt(
            source=source,
            attempt=provisional_attempt,
            normalized_text=normalized,
            chunk_size=chunk_size,
            overlap=overlap,
        )

    final_decision = classify_fetch_decision(
        raw_decision=raw_decision,
        normalized_text=normalized,
        suspicious_gate=suspicious,
        min_text_chars=min_text_chars,
        chunk_count=len(chunks),
        signal_score=signal_score,
    )

    attempt = FetchAttempt(
        corpus_id=corpus_id,
        jurisdiction=jurisdiction,
        source_title=source_title,
        source_url=source_url,
        candidate_type=candidate_type,
        fetch_decision=final_decision,
        http_status=status,
        content_type=content_type,
        byte_length=len(raw),
        raw_sha256=raw_hash,
        normalized_text_sha256=normalized_hash,
        normalized_text_length=len(normalized),
        chunk_count=len(chunks),
        legal_signal_score=signal_score,
        suspicious_gate_page=suspicious,
        elapsed_ms=elapsed_ms,
        error=error,
    )

    return attempt, chunks


def attempt_rank(attempt: FetchAttempt) -> Tuple[int, int, int, int]:
    decision_rank = {
        "FETCH_OK": 5,
        "FETCH_WARN_EXTRACTABLE": 4,
        "FETCH_WARN_LOW_LEGAL_SIGNAL": 3,
        "FETCH_WARN_GATE_PAGE": 2,
        "FETCH_WARN_SHORT_TEXT": 1,
        "FETCH_WARN_NO_CHUNKS": 1,
        "FETCH_RAW_OK": 1,
        "FETCH_HTTP_ERROR": 0,
        "FETCH_ERROR": 0,
        "FETCH_INVALID_URL": 0,
    }.get(attempt.fetch_decision, 0)

    return (
        decision_rank,
        attempt.chunk_count,
        attempt.normalized_text_length,
        attempt.legal_signal_score,
    )


def process_source(
    source: Dict[str, Any],
    timeout: float,
    max_bytes: int,
    min_text_chars: int,
    chunk_size: int,
    overlap: int,
) -> Tuple[SourceRecord, List[FetchAttempt], List[ChunkRecord]]:
    attempts: List[FetchAttempt] = []
    chunks_by_url: Dict[str, List[ChunkRecord]] = {}

    candidates = source.get("candidate_urls", [])
    if not isinstance(candidates, list) or not candidates:
        candidates = []

    for candidate in candidates:
        attempt, chunks = run_candidate_attempt(
            source=source,
            candidate=candidate,
            timeout=timeout,
            max_bytes=max_bytes,
            min_text_chars=min_text_chars,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        attempts.append(attempt)
        chunks_by_url[attempt.source_url] = chunks

        if is_rebuild_usable(
            attempt.fetch_decision,
            attempt.chunk_count,
            attempt.normalized_text_length,
        ):
            break

    if not attempts:
        empty_attempt = FetchAttempt(
            corpus_id=str(source.get("corpus_id", "UNKNOWN")),
            jurisdiction=str(source.get("jurisdiction", "UNKNOWN")),
            source_title=str(source.get("source_title", "UNKNOWN")),
            source_url="",
            candidate_type="NO_CANDIDATE",
            fetch_decision="FETCH_INVALID_URL",
            http_status=None,
            content_type=None,
            byte_length=0,
            raw_sha256=None,
            normalized_text_sha256=None,
            normalized_text_length=0,
            chunk_count=0,
            legal_signal_score=0,
            suspicious_gate_page=False,
            elapsed_ms=0.0,
            error="No candidate URLs.",
        )
        attempts.append(empty_attempt)
        chunks_by_url[""] = []

    best_attempt = sorted(attempts, key=attempt_rank, reverse=True)[0]
    best_chunks = chunks_by_url.get(best_attempt.source_url, [])

    source_record = SourceRecord(
        corpus_id=best_attempt.corpus_id,
        jurisdiction=best_attempt.jurisdiction,
        source_title=best_attempt.source_title,
        selected_source_url=best_attempt.source_url,
        selected_candidate_type=best_attempt.candidate_type,
        source_type=str(source.get("source_type", "UNKNOWN")),
        hard_gate=bool(source.get("hard_gate", False)),
        fetch_decision=best_attempt.fetch_decision,
        rebuild_usable=is_rebuild_usable(
            best_attempt.fetch_decision,
            best_attempt.chunk_count,
            best_attempt.normalized_text_length,
        ),
        http_status=best_attempt.http_status,
        content_type=best_attempt.content_type,
        byte_length=best_attempt.byte_length,
        raw_sha256=best_attempt.raw_sha256,
        normalized_text_sha256=best_attempt.normalized_text_sha256,
        normalized_text_length=best_attempt.normalized_text_length,
        chunk_count=best_attempt.chunk_count,
        legal_signal_score=best_attempt.legal_signal_score,
        suspicious_gate_page=best_attempt.suspicious_gate_page,
        elapsed_ms=sum(a.elapsed_ms for a in attempts),
        error=best_attempt.error,
    )

    return source_record, attempts, best_chunks


# =============================================================================
# QOIM gates
# =============================================================================

def build_gate_checks(
    source_records: Sequence[SourceRecord],
    chunks: Sequence[ChunkRecord],
    min_ok: int,
    strict: bool,
    audit_chain_complete: bool,
) -> List[GateCheck]:
    fetch_ok_count = sum(1 for r in source_records if r.fetch_decision == "FETCH_OK")
    rebuild_ok_count = sum(1 for r in source_records if r.rebuild_usable)

    hard_gate_fail_count = sum(
        1 for r in source_records if r.hard_gate and not r.rebuild_usable
    )

    all_chunks_have_hashes = all(
        bool(c.source_hash and c.normalized_text_sha256 and c.chunk_hash)
        for c in chunks
    )

    checks = [
        GateCheck(
            gate_id="RQ4_REBUILD_OK_MINIMUM",
            description="At least min_ok sources must be rebuild-usable.",
            expected=f">= {min_ok}",
            actual=rebuild_ok_count,
            passed=rebuild_ok_count >= min_ok,
            severity="HARD",
        ),
        GateCheck(
            gate_id="RQ4_CHUNK_COUNT_POSITIVE",
            description="Rebuild must produce at least one chunk.",
            expected="> 0",
            actual=len(chunks),
            passed=len(chunks) > 0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="RQ4_CHUNK_HASH_COMPLETENESS",
            description="All rebuilt chunks must have source_hash, normalized_text_sha256, and chunk_hash.",
            expected=True,
            actual=all_chunks_have_hashes,
            passed=all_chunks_have_hashes,
            severity="HARD",
        ),
        GateCheck(
            gate_id="RQ4_AUDIT_CHAIN_COMPLETE",
            description="RQ4 audit chain must verify.",
            expected=1.0,
            actual=1.0 if audit_chain_complete else 0.0,
            passed=audit_chain_complete,
            severity="HARD",
        ),
        GateCheck(
            gate_id="RQ4_HARD_GATE_SOURCES",
            description="Any hard_gate source must be rebuild-usable.",
            expected=0,
            actual=hard_gate_fail_count,
            passed=hard_gate_fail_count == 0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="RQ4_FETCH_OK_OBSERVATION",
            description="Number of clean FETCH_OK sources. Informational, not required.",
            expected="informational",
            actual=fetch_ok_count,
            passed=True,
            severity="SOFT",
        ),
    ]

    if strict:
        checks.append(
            GateCheck(
                gate_id="RQ4_STRICT_ALL_SOURCES_REBUILD_USABLE",
                description="Strict mode requires every listed source to be rebuild-usable.",
                expected=len(source_records),
                actual=rebuild_ok_count,
                passed=rebuild_ok_count == len(source_records),
                severity="HARD",
            )
        )

    return checks


def summarize_gate_checks(checks: Sequence[GateCheck]) -> Tuple[str, List[str]]:
    hard_failures = [
        f"{check.gate_id}: expected={check.expected}, actual={check.actual}"
        for check in checks
        if check.severity == "HARD" and not check.passed
    ]

    if hard_failures:
        return "RQ4_SOURCE_REBUILD_FAIL", hard_failures

    return "RQ4_SOURCE_REBUILD_PASS", []


# =============================================================================
# Audit-S
# =============================================================================

def build_audit_chain(
    source_records: Sequence[SourceRecord],
    attempts: Sequence[FetchAttempt],
    chunks: Sequence[ChunkRecord],
    pre_gate_payload: Dict[str, Any],
) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous_hash = "GENESIS"

    payloads: List[Tuple[str, Dict[str, Any]]] = [
        (
            "RQ4_SOURCE_RECORDS",
            {"records": [asdict(record) for record in source_records]},
        ),
        (
            "RQ4_FETCH_ATTEMPTS",
            {"attempts": [asdict(attempt) for attempt in attempts]},
        ),
        (
            "RQ4_CHUNK_INDEX",
            {
                "chunk_count": len(chunks),
                "chunk_hashes": [chunk.chunk_hash for chunk in chunks],
            },
        ),
        (
            "RQ4_PRE_GATE_PAYLOAD",
            pre_gate_payload,
        ),
    ]

    for index, (event_type, payload) in enumerate(payloads):
        event_payload = {
            "index": index,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        event_hash = stable_json_hash(event_payload)

        events.append(
            AuditEvent(
                index=index,
                event_type=event_type,
                payload=payload,
                previous_hash=previous_hash,
                event_hash=event_hash,
            )
        )

        previous_hash = event_hash

    return events


def verify_audit_chain(events: Sequence[AuditEvent]) -> bool:
    expected_previous = "GENESIS"

    for event in events:
        if event.previous_hash != expected_previous:
            return False

        recompute_payload = {
            "index": event.index,
            "event_type": event.event_type,
            "payload": event.payload,
            "previous_hash": event.previous_hash,
        }

        if stable_json_hash(recompute_payload) != event.event_hash:
            return False

        expected_previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


# =============================================================================
# Output
# =============================================================================

def build_rebuilt_manifest(
    source_records: Sequence[SourceRecord],
    attempts: Sequence[FetchAttempt],
    chunks: Sequence[ChunkRecord],
) -> Dict[str, Any]:
    sources: List[Dict[str, Any]] = []

    for record in source_records:
        source_chunks = [c for c in chunks if c.source_url == record.selected_source_url]
        source_attempts = [a for a in attempts if a.corpus_id == record.corpus_id]

        sources.append(
            {
                "corpus_id": record.corpus_id,
                "jurisdiction": record.jurisdiction,
                "source_title": record.source_title,
                "selected_source_url": record.selected_source_url,
                "selected_candidate_type": record.selected_candidate_type,
                "source_type": record.source_type,
                "fetch_decision": record.fetch_decision,
                "rebuild_usable": record.rebuild_usable,
                "http_status": record.http_status,
                "raw_sha256": record.raw_sha256,
                "normalized_text_sha256": record.normalized_text_sha256,
                "normalized_text_length": record.normalized_text_length,
                "chunk_count": len(source_chunks),
                "chunk_hashes": [c.chunk_hash for c in source_chunks],
                "attempts": [asdict(a) for a in source_attempts],
            }
        )

    return {
        "name": "HSRAG-LAW-RQ4.1-Rebuilt-Source-Manifest",
        "source_count": len(source_records),
        "attempt_count": len(attempts),
        "chunk_count": len(chunks),
        "sources": sources,
    }


def write_markdown_summary(
    path: Path,
    decision: str,
    failures: Sequence[str],
    source_records: Sequence[SourceRecord],
    attempts: Sequence[FetchAttempt],
    chunks: Sequence[ChunkRecord],
    checks: Sequence[GateCheck],
    audit_chain_complete: bool,
    min_ok: int,
    strict: bool,
) -> None:
    fetch_ok_count = sum(1 for r in source_records if r.fetch_decision == "FETCH_OK")
    rebuild_ok_count = sum(1 for r in source_records if r.rebuild_usable)
    warn_count = sum(1 for r in source_records if r.fetch_decision.startswith("FETCH_WARN"))
    error_count = sum(
        1
        for r in source_records
        if r.fetch_decision in {"FETCH_ERROR", "FETCH_HTTP_ERROR", "FETCH_INVALID_URL"}
    )

    lines = [
        "# RQ4.1 Official/Public Source Fetch & Rebuild Summary",
        "",
        f"Core decision: `{decision}`",
        f"Audit chain complete: `{1.0 if audit_chain_complete else 0.0}`",
        "",
        "## Purpose",
        "",
        (
            "RQ4.1 tests whether HSRAG LAW can fetch official or public legal sources, "
            "normalize text, generate stable source hashes, rebuild chunks, and write "
            "an auditable source manifest. It distinguishes clean fetch success from "
            "rebuild-usable warning cases."
        ),
        "",
        "## Summary",
        "",
        f"- source_count: `{len(source_records)}`",
        f"- attempt_count: `{len(attempts)}`",
        f"- fetch_ok_count: `{fetch_ok_count}`",
        f"- rebuild_ok_count: `{rebuild_ok_count}`",
        f"- fetch_warn_count: `{warn_count}`",
        f"- fetch_error_count: `{error_count}`",
        f"- rebuilt_chunk_count: `{len(chunks)}`",
        f"- min_ok: `{min_ok}`",
        f"- strict: `{strict}`",
        "",
        "## Source Records",
        "",
        "| corpus_id | jurisdiction | selected_candidate_type | fetch_decision | rebuild_usable | status | text_len | chunks |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]

    for record in source_records:
        lines.append(
            f"| {record.corpus_id} | {record.jurisdiction} | "
            f"{record.selected_candidate_type} | `{record.fetch_decision}` | "
            f"`{record.rebuild_usable}` | {record.http_status} | "
            f"{record.normalized_text_length} | {record.chunk_count} |"
        )

    lines.extend(
        [
            "",
            "## Gate Checks",
            "",
            "| gate_id | passed | expected | actual |",
            "|---|---:|---|---|",
        ]
    )

    for check in checks:
        lines.append(
            f"| {check.gate_id} | `{check.passed}` | `{check.expected}` | `{check.actual}` |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `FETCH_OK` means clean fetch + enough text + legal signal + chunks.",
            "- `FETCH_WARN_EXTRACTABLE` means the fetch had a warning but still produced rebuild-usable text and chunks.",
            "- EUR-Lex may return JavaScript / robot verification pages in simple fetch clients.",
            "- Public legal references are used as fallback candidates for reproducibility smoke testing.",
            "- This is not yet RQ4-full. A future version can add browser automation and PDF extraction.",
        ]
    )

    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(f"- {failure}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    decision: str,
    failures: Sequence[str],
    source_records: Sequence[SourceRecord],
    attempts: Sequence[FetchAttempt],
    chunks: Sequence[ChunkRecord],
    audit_chain_complete: bool,
    min_ok: int,
    strict: bool,
) -> None:
    fetch_ok_count = sum(1 for r in source_records if r.fetch_decision == "FETCH_OK")
    rebuild_ok_count = sum(1 for r in source_records if r.rebuild_usable)
    warn_count = sum(1 for r in source_records if r.fetch_decision.startswith("FETCH_WARN"))
    error_count = sum(
        1
        for r in source_records
        if r.fetch_decision in {"FETCH_ERROR", "FETCH_HTTP_ERROR", "FETCH_INVALID_URL"}
    )

    print("=" * 80)
    print("HSRAG LAW — RQ4.1 OFFICIAL/PUBLIC SOURCE FETCH & REBUILD")
    print("=" * 80)
    print(f"core_decision: {decision}")
    print(f"audit_chain_complete: {1.0 if audit_chain_complete else 0.0}")
    print("")
    print("Scope:")
    print(f"  source_count: {len(source_records)}")
    print(f"  attempt_count: {len(attempts)}")
    print(f"  fetch_ok_count: {fetch_ok_count}")
    print(f"  rebuild_ok_count: {rebuild_ok_count}")
    print(f"  fetch_warn_count: {warn_count}")
    print(f"  fetch_error_count: {error_count}")
    print(f"  rebuilt_chunk_count: {len(chunks)}")
    print(f"  min_ok: {min_ok}")
    print(f"  strict: {strict}")
    print("")
    print("Sources:")
    for record in source_records:
        print(
            f"  {record.corpus_id}: {record.fetch_decision} "
            f"rebuild_usable={record.rebuild_usable} "
            f"candidate={record.selected_candidate_type} "
            f"status={record.http_status} text_len={record.normalized_text_length} "
            f"chunks={record.chunk_count}"
        )

    if failures:
        print("")
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")

    print("")
    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 80)


# =============================================================================
# Main
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RQ4.1 official/public legal source fetch and rebuild smoke test."
    )
    parser.add_argument(
        "--min-ok",
        type=int,
        default=2,
        help="Minimum number of sources that must be rebuild-usable.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require every source to be rebuild-usable.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Fetch timeout in seconds per URL.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=2_000_000,
        help="Maximum bytes to read per source.",
    )
    parser.add_argument(
        "--min-text-chars",
        type=int,
        default=500,
        help="Minimum normalized text length required for FETCH_OK or rebuild-usable warning.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Chunk size in characters.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=120,
        help="Chunk overlap in characters.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    ensure_dirs()

    manifest = load_or_create_manifest()

    source_records: List[SourceRecord] = []
    attempt_records: List[FetchAttempt] = []
    chunk_records: List[ChunkRecord] = []

    for source in manifest:
        source_record, attempts, chunks = process_source(
            source=source,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
            min_text_chars=args.min_text_chars,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
        source_records.append(source_record)
        attempt_records.extend(attempts)
        chunk_records.extend(chunks)

    pre_gate_payload = {
        "source_count": len(source_records),
        "attempt_count": len(attempt_records),
        "chunk_count": len(chunk_records),
        "min_ok": args.min_ok,
        "strict": args.strict,
        "fetch_decisions": {
            record.corpus_id: record.fetch_decision for record in source_records
        },
        "rebuild_usable": {
            record.corpus_id: record.rebuild_usable for record in source_records
        },
    }

    audit_chain = build_audit_chain(
        source_records=source_records,
        attempts=attempt_records,
        chunks=chunk_records,
        pre_gate_payload=pre_gate_payload,
    )
    audit_chain_complete = verify_audit_chain(audit_chain)

    checks = build_gate_checks(
        source_records=source_records,
        chunks=chunk_records,
        min_ok=args.min_ok,
        strict=args.strict,
        audit_chain_complete=audit_chain_complete,
    )
    decision, failures = summarize_gate_checks(checks)

    rebuilt_manifest = build_rebuilt_manifest(source_records, attempt_records, chunk_records)

    summary_payload = {
        "name": "HSRAG-LAW-RQ4.1-Official-Public-Source-Fetch-Rebuild",
        "core_decision": decision,
        "failures": list(failures),
        "source_count": len(source_records),
        "attempt_count": len(attempt_records),
        "rebuilt_chunk_count": len(chunk_records),
        "min_ok": args.min_ok,
        "strict": args.strict,
        "source_records": [asdict(record) for record in source_records],
        "attempt_records": [asdict(attempt) for attempt in attempt_records],
        "gate_checks": [asdict(check) for check in checks],
        "audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
        "outputs": {
            "summary_json": "rq4_source_rebuild_summary.json",
            "summary_md": "rq4_source_rebuild_summary.md",
            "source_records_csv": "rq4_source_records.csv",
            "fetch_attempts_csv": "rq4_fetch_attempts.csv",
            "rebuilt_chunks_csv": "rq4_rebuilt_chunks.csv",
            "gate_checks_csv": "rq4_gate_checks.csv",
            "rebuilt_manifest_json": "rq4_rebuilt_source_manifest.json",
            "audit_chain_jsonl": "rq4_source_rebuild_audit_chain.jsonl",
        },
    }

    write_json(RESULTS_DIR / "rq4_source_rebuild_summary.json", summary_payload)
    write_json(RESULTS_DIR / "rq4_rebuilt_source_manifest.json", rebuilt_manifest)
    write_dataclass_csv(RESULTS_DIR / "rq4_source_records.csv", source_records)
    write_dataclass_csv(RESULTS_DIR / "rq4_fetch_attempts.csv", attempt_records)
    write_dataclass_csv(RESULTS_DIR / "rq4_rebuilt_chunks.csv", chunk_records)
    write_dataclass_csv(RESULTS_DIR / "rq4_gate_checks.csv", checks)
    write_audit_chain(RESULTS_DIR / "rq4_source_rebuild_audit_chain.jsonl", audit_chain)
    write_markdown_summary(
        RESULTS_DIR / "rq4_source_rebuild_summary.md",
        decision=decision,
        failures=failures,
        source_records=source_records,
        attempts=attempt_records,
        chunks=chunk_records,
        checks=checks,
        audit_chain_complete=audit_chain_complete,
        min_ok=args.min_ok,
        strict=args.strict,
    )

    print_summary(
        decision=decision,
        failures=failures,
        source_records=source_records,
        attempts=attempt_records,
        chunks=chunk_records,
        audit_chain_complete=audit_chain_complete,
        min_ok=args.min_ok,
        strict=args.strict,
    )

    return 0 if decision == "RQ4_SOURCE_REBUILD_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())