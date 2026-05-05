"""
HSRAG LAW — RQ1 Verification Script
===================================

RQ1 = Publication-Grade Real Corpus Gate

This script verifies the frozen RQ1 publication-grade corpus gate result and
performs a cautious URL fetch smoke test for provenance reproducibility.

It does NOT claim to reproduce the full RQ2/RQ3 adversarial Monte Carlo tests.
RQ1 is a source-integrity / source-hash / real-corpus gate. Therefore MC cases
are marked as N/A unless a separate adversarial source-mutation benchmark is added.

QSVCS annotations:
- CTHC: classify evidence by corpus/source/provenance fields.
- QOIM: enforce acceptance gates and feasible provenance boundaries.
- SGF: run checks in fixed forward-only order.
- VPSM: represent benchmark state as structured vectors.
- Audit-S: produce an append-only hash chain for all verification events.

Run from repository root:

    python examples/hsrag_law/scripts/verify_rq1.py

Optional:

    python examples/hsrag_law/scripts/verify_rq1.py --skip-fetch
    python examples/hsrag_law/scripts/verify_rq1.py --strict-fetch
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# Path resolution
# =============================================================================

THIS_FILE = Path(__file__).resolve()

if THIS_FILE.parent.name == "scripts":
    EXAMPLE_ROOT = THIS_FILE.parent.parent
else:
    EXAMPLE_ROOT = THIS_FILE.parent

REPO_ROOT = EXAMPLE_ROOT.parents[1] if len(EXAMPLE_ROOT.parents) >= 2 else EXAMPLE_ROOT
RESULTS_DIR = EXAMPLE_ROOT / "results"
DATA_DIR = EXAMPLE_ROOT / "data"


# =============================================================================
# Frozen RQ1 reference result
# =============================================================================

RQ1_FROZEN_RESULT: Dict[str, Any] = {
    "name": "HSRAG-v0.40.2.3.3-SourceHashBackfill-PublicationGate",
    "decision": "RQ1_PUBLICATION_GRADE_PASS",
    "semantic_label": "REAL_PRIMARY_CORPUS_PUBLICATION_GATE",
    "corpus_count": 6,
    "real_primary_corpus_count": 6,
    "real_primary_corpus_rate": 1.0,
    "real_primary_chunk_rate": 1.0,
    "source_hash_final_present_rate": 1.0,
    "primary_real_rows": 1211,
    "primary_real_target_correct_rate": 1.0,
    "primary_real_wrong_collision_rate": 0.0,
    "sc1_regression_target_correct_rate": 1.0,
    "fail_count": 0,
    "warn_count": 0,
    "qsvcs_hash": "sha256:3ba8ac0785db02d01f5eda32aec9a5d6915488e5334f4af8a664c6450b242af8",
    "zip_sha256": "sha256:fc5f63c9fe53f7144f0c717190425f0070e3107739e1c0541814042612422fa3",
    "mc_cases": None,
    "mc_scope": "N/A",
    "mc_scope_reason": (
        "RQ1 is a source-integrity and publication-grade real-corpus gate, "
        "not an adversarial retrieval mutation benchmark. MC robustness is "
        "covered by RQ2/RQ3-style retrieval benchmarks."
    ),
}


# =============================================================================
# URL fetch smoke manifest
# =============================================================================

DEFAULT_SOURCE_MANIFEST: List[Dict[str, Any]] = [
    {
        "corpus_id": "EU_AI_ACT",
        "jurisdiction": "EU",
        "source_title": "Regulation (EU) 2024/1689 — Artificial Intelligence Act",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "EUR-Lex may return JS/bot-verification HTML in simple fetch environments.",
    },
    {
        "corpus_id": "EU_DMA",
        "jurisdiction": "EU",
        "source_title": "Regulation (EU) 2022/1925 — Digital Markets Act",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2022/1925/oj/eng",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "EUR-Lex may return JS/bot-verification HTML in simple fetch environments.",
    },
    {
        "corpus_id": "US_COPPA",
        "jurisdiction": "US",
        "source_title": "FTC — Children's Online Privacy Protection Rule",
        "source_url": "https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "FTC legal-library page for COPPA rule information.",
    },
    {
        "corpus_id": "US_CDA230",
        "jurisdiction": "US",
        "source_title": "47 U.S.C. Section 230",
        "source_url": "https://www.govinfo.gov/link/uscode/47/230",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "GovInfo U.S. Code link endpoint.",
    },
    {
        "corpus_id": "US_FTC_ACT5",
        "jurisdiction": "US",
        "source_title": "15 U.S.C. Section 45 — FTC Act Section 5",
        "source_url": "https://www.govinfo.gov/link/uscode/15/45",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "GovInfo U.S. Code link endpoint.",
    },
    {
        "corpus_id": "US_CCPA",
        "jurisdiction": "US-CA",
        "source_title": "California Attorney General — CCPA",
        "source_url": "https://oag.ca.gov/privacy/ccpa",
        "source_type": "OFFICIAL_REFERENCE_CANDIDATE",
        "hard_gate": False,
        "notes": "California Attorney General CCPA overview page.",
    },
]


# =============================================================================
# Data models
# =============================================================================

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


@dataclass
class FetchRecord:
    corpus_id: str
    jurisdiction: str
    source_title: str
    source_url: str
    source_type: str
    hard_gate: bool
    fetch_decision: str
    http_status: Optional[int]
    content_type: Optional[str]
    byte_length: int
    raw_sha256: Optional[str]
    normalized_text_sha256: Optional[str]
    normalized_text_length: int
    suspicious_captcha_or_js_gate: bool
    elapsed_ms: float
    error: Optional[str]


# =============================================================================
# Utility functions
# =============================================================================

def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def normalize_text_from_html_or_plain(raw: bytes, content_type: Optional[str]) -> str:
    text = raw.decode("utf-8", errors="replace")

    # Very lightweight extraction: enough for provenance smoke test,
    # not a production legal-text extractor.
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_suspicious_gate_page(text: str) -> bool:
    lowered = text.lower()
    patterns = [
        "javascript is disabled",
        "verify that you're not a robot",
        "captcha",
        "enable javascript",
        "access denied",
        "cloudflare",
        "bot",
    ]
    return any(pattern in lowered for pattern in patterns)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_or_create_source_manifest() -> List[Dict[str, Any]]:
    manifest_path = DATA_DIR / "rq1_source_manifest_template.json"

    if not manifest_path.exists():
        write_json(manifest_path, DEFAULT_SOURCE_MANIFEST)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {manifest_path}: {exc}") from exc

    if not isinstance(manifest, list):
        raise ValueError(f"{manifest_path} must contain a JSON list.")

    return manifest


# =============================================================================
# QOIM: RQ1 gate checks
# =============================================================================

def build_rq1_gate_checks(result: Dict[str, Any]) -> List[GateCheck]:
    checks = [
        GateCheck(
            gate_id="RQ1_DECISION",
            description="RQ1 frozen decision must be publication-grade pass.",
            expected="RQ1_PUBLICATION_GRADE_PASS",
            actual=result.get("decision"),
            passed=result.get("decision") == "RQ1_PUBLICATION_GRADE_PASS",
            severity="HARD",
        ),
        GateCheck(
            gate_id="REAL_PRIMARY_CORPUS_RATE",
            description="All corpora must be classified as real primary corpora.",
            expected=1.0,
            actual=result.get("real_primary_corpus_rate"),
            passed=result.get("real_primary_corpus_rate") == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="REAL_PRIMARY_CHUNK_RATE",
            description="All chunks must be tied to real primary corpus records.",
            expected=1.0,
            actual=result.get("real_primary_chunk_rate"),
            passed=result.get("real_primary_chunk_rate") == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="SOURCE_HASH_FINAL_PRESENT_RATE",
            description="Every chunk must have source_hash_final present.",
            expected=1.0,
            actual=result.get("source_hash_final_present_rate"),
            passed=result.get("source_hash_final_present_rate") == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="PRIMARY_REAL_TARGET_CORRECT",
            description="Primary real target correctness must equal 1.0.",
            expected=1.0,
            actual=result.get("primary_real_target_correct_rate"),
            passed=result.get("primary_real_target_correct_rate") == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="PRIMARY_REAL_WRONG_COLLISION",
            description="Primary real wrong collision rate must equal 0.0.",
            expected=0.0,
            actual=result.get("primary_real_wrong_collision_rate"),
            passed=result.get("primary_real_wrong_collision_rate") == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="SC1_REGRESSION_TARGET_CORRECT",
            description="SC1 regression target correctness must equal 1.0.",
            expected=1.0,
            actual=result.get("sc1_regression_target_correct_rate"),
            passed=result.get("sc1_regression_target_correct_rate") == 1.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="FAIL_COUNT_ZERO",
            description="fail_count must equal 0.",
            expected=0,
            actual=result.get("fail_count"),
            passed=result.get("fail_count") == 0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="WARN_COUNT_ZERO",
            description="warn_count must equal 0.",
            expected=0,
            actual=result.get("warn_count"),
            passed=result.get("warn_count") == 0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="QSVCS_HASH_PRESENT",
            description="QSVCS hash must be present for audit reproducibility.",
            expected="present sha256",
            actual=result.get("qsvcs_hash"),
            passed=isinstance(result.get("qsvcs_hash"), str)
            and str(result.get("qsvcs_hash")).startswith("sha256:"),
            severity="HARD",
        ),
        GateCheck(
            gate_id="ZIP_HASH_PRESENT",
            description="Package zip hash must be present for artifact reproducibility.",
            expected="present sha256",
            actual=result.get("zip_sha256"),
            passed=isinstance(result.get("zip_sha256"), str)
            and str(result.get("zip_sha256")).startswith("sha256:"),
            severity="HARD",
        ),
    ]

    return checks


def summarize_gate_checks(checks: Sequence[GateCheck]) -> Tuple[str, List[str]]:
    failures = [
        f"{check.gate_id}: expected={check.expected}, actual={check.actual}"
        for check in checks
        if check.severity == "HARD" and not check.passed
    ]

    if failures:
        return "RQ1_VERIFICATION_FAIL", failures

    return "RQ1_VERIFICATION_PASS", []


def evaluate_mc_scope(result: Dict[str, Any]) -> Dict[str, Any]:
    mc_cases = result.get("mc_cases")
    mc_scope = result.get("mc_scope")
    reason = result.get("mc_scope_reason")

    if mc_cases is None and mc_scope == "N/A":
        decision = "MC_NOT_REQUIRED_FOR_RQ1_PASS"
    else:
        decision = "MC_SCOPE_REVIEW_NEEDED"

    return {
        "decision": decision,
        "mc_cases": mc_cases,
        "mc_scope": mc_scope,
        "reason": reason,
        "recommendation": (
            "Keep MC as N/A for RQ1, and reserve adversarial mutation MC "
            "for RQ2/RQ3/RQ4/RQ5 retrieval or source-drift benchmarks."
        ),
    }


# =============================================================================
# Audit-S: hash chain
# =============================================================================

def build_audit_chain(
    checks: Sequence[GateCheck],
    mc_scope: Dict[str, Any],
    fetch_summary: Dict[str, Any],
) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous_hash = "GENESIS"

    payloads: List[Tuple[str, Dict[str, Any]]] = [
        ("RQ1_FROZEN_RESULT", RQ1_FROZEN_RESULT),
        ("RQ1_GATE_CHECKS", {"checks": [asdict(check) for check in checks]}),
        ("RQ1_MC_SCOPE", mc_scope),
        ("RQ1_FETCH_SUMMARY", fetch_summary),
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
        recomputed_hash = stable_json_hash(recompute_payload)

        if recomputed_hash != event.event_hash:
            return False

        expected_previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


# =============================================================================
# Source URL fetch smoke test
# =============================================================================

def fetch_url_smoke(
    source: Dict[str, Any],
    timeout_seconds: float,
) -> FetchRecord:
    started = time.perf_counter()

    corpus_id = str(source.get("corpus_id", "UNKNOWN"))
    jurisdiction = str(source.get("jurisdiction", "UNKNOWN"))
    source_title = str(source.get("source_title", "UNKNOWN"))
    source_url = str(source.get("source_url", ""))
    source_type = str(source.get("source_type", "UNKNOWN"))
    hard_gate = bool(source.get("hard_gate", False))

    if not source_url.startswith(("http://", "https://")):
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return FetchRecord(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            source_type=source_type,
            hard_gate=hard_gate,
            fetch_decision="FETCH_INVALID_URL",
            http_status=None,
            content_type=None,
            byte_length=0,
            raw_sha256=None,
            normalized_text_sha256=None,
            normalized_text_length=0,
            suspicious_captcha_or_js_gate=False,
            elapsed_ms=elapsed_ms,
            error="Invalid or empty source_url.",
        )

    request = urllib.request.Request(
        source_url,
        headers={
            "User-Agent": (
                "HSRAG-LAW-RQ1-SourceVerifier/0.1 "
                "(research provenance smoke test)"
            ),
            "Accept": "text/html,application/pdf,text/plain,*/*",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
            http_status = int(getattr(response, "status", 200))
            content_type = response.headers.get("Content-Type")

        normalized_text = normalize_text_from_html_or_plain(raw, content_type)
        suspicious_gate = is_suspicious_gate_page(normalized_text)

        if len(raw) == 0:
            decision = "FETCH_EMPTY"
        elif suspicious_gate:
            decision = "FETCH_WARN_GATE_PAGE"
        elif len(normalized_text) < 200:
            decision = "FETCH_WARN_SHORT_TEXT"
        else:
            decision = "FETCH_OK"

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return FetchRecord(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            source_type=source_type,
            hard_gate=hard_gate,
            fetch_decision=decision,
            http_status=http_status,
            content_type=content_type,
            byte_length=len(raw),
            raw_sha256=sha256_bytes(raw),
            normalized_text_sha256=stable_json_hash(
                {"normalized_text": normalized_text}
            ),
            normalized_text_length=len(normalized_text),
            suspicious_captcha_or_js_gate=suspicious_gate,
            elapsed_ms=elapsed_ms,
            error=None,
        )

    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return FetchRecord(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            source_type=source_type,
            hard_gate=hard_gate,
            fetch_decision="FETCH_HTTP_ERROR",
            http_status=exc.code,
            content_type=None,
            byte_length=0,
            raw_sha256=None,
            normalized_text_sha256=None,
            normalized_text_length=0,
            suspicious_captcha_or_js_gate=False,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return FetchRecord(
            corpus_id=corpus_id,
            jurisdiction=jurisdiction,
            source_title=source_title,
            source_url=source_url,
            source_type=source_type,
            hard_gate=hard_gate,
            fetch_decision="FETCH_ERROR",
            http_status=None,
            content_type=None,
            byte_length=0,
            raw_sha256=None,
            normalized_text_sha256=None,
            normalized_text_length=0,
            suspicious_captcha_or_js_gate=False,
            elapsed_ms=elapsed_ms,
            error=repr(exc),
        )


def run_fetch_smoke(
    manifest: Sequence[Dict[str, Any]],
    timeout_seconds: float,
    skip_fetch: bool,
) -> List[FetchRecord]:
    if skip_fetch:
        return []

    records: List[FetchRecord] = []
    for source in manifest:
        records.append(fetch_url_smoke(source, timeout_seconds=timeout_seconds))
    return records


def summarize_fetch_records(
    records: Sequence[FetchRecord],
    strict_fetch: bool,
) -> Dict[str, Any]:
    if not records:
        return {
            "decision": "FETCH_SKIPPED",
            "strict_fetch": strict_fetch,
            "fetch_count": 0,
            "fetch_ok_count": 0,
            "fetch_warn_count": 0,
            "fetch_error_count": 0,
            "hard_gate_failed_count": 0,
            "notes": [
                "URL fetch smoke test was skipped.",
                "RQ1 core verification does not depend on URL fetch in this script.",
            ],
        }

    ok_decisions = {"FETCH_OK"}
    warn_decisions = {"FETCH_WARN_GATE_PAGE", "FETCH_WARN_SHORT_TEXT", "FETCH_EMPTY"}
    error_decisions = {"FETCH_HTTP_ERROR", "FETCH_ERROR", "FETCH_INVALID_URL"}

    ok_count = sum(1 for r in records if r.fetch_decision in ok_decisions)
    warn_count = sum(1 for r in records if r.fetch_decision in warn_decisions)
    error_count = sum(1 for r in records if r.fetch_decision in error_decisions)
    hard_gate_failed_count = sum(
        1
        for r in records
        if r.hard_gate and r.fetch_decision != "FETCH_OK"
    )

    if strict_fetch and ok_count == 0:
        decision = "FETCH_STRICT_FAIL"
    elif hard_gate_failed_count > 0:
        decision = "FETCH_HARD_GATE_FAIL"
    elif ok_count > 0 and error_count == 0:
        decision = "FETCH_SMOKE_PASS"
    elif ok_count > 0:
        decision = "FETCH_SMOKE_PASS_WITH_WARN"
    else:
        decision = "FETCH_SMOKE_WARN"

    return {
        "decision": decision,
        "strict_fetch": strict_fetch,
        "fetch_count": len(records),
        "fetch_ok_count": ok_count,
        "fetch_warn_count": warn_count,
        "fetch_error_count": error_count,
        "hard_gate_failed_count": hard_gate_failed_count,
        "notes": [
            "URL fetch is a smoke test, not the RQ1 hard gate.",
            "Some official legal sources may block simple scripted fetches or return JS verification pages.",
            "For publication-grade reproduction, add a dedicated RQ4 official-source fetch pipeline.",
        ],
    }


# =============================================================================
# Output writers
# =============================================================================

def write_gate_checks_csv(path: Path, checks: Sequence[GateCheck]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(checks[0]).keys()))
        writer.writeheader()
        for check in checks:
            writer.writerow(asdict(check))


def write_fetch_records_csv(path: Path, records: Sequence[FetchRecord]) -> None:
    fieldnames = list(FetchRecord.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def build_consistency_matrix(
    core_decision: str,
    mc_scope: Dict[str, Any],
    fetch_summary: Dict[str, Any],
    audit_chain_complete: bool,
) -> List[Dict[str, Any]]:
    return [
        {
            "rq": "RQ1",
            "benchmark_role": "publication_grade_real_corpus_gate",
            "requires_mc": False,
            "mc_cases": "N/A",
            "mc_scope_decision": mc_scope["decision"],
            "source_hash_gate": core_decision,
            "url_fetch_smoke": fetch_summary["decision"],
            "audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
            "notes": (
                "RQ1 is a corpus/source/provenance gate. MC mutation robustness "
                "belongs to RQ2/RQ3 retrieval tests or future RQ4/RQ5 source-drift tests."
            ),
        }
    ]


def write_consistency_matrix_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown_summary(
    path: Path,
    core_decision: str,
    core_failures: Sequence[str],
    checks: Sequence[GateCheck],
    mc_scope: Dict[str, Any],
    fetch_summary: Dict[str, Any],
    fetch_records: Sequence[FetchRecord],
    audit_chain_complete: bool,
) -> None:
    passed_count = sum(1 for check in checks if check.passed)
    total_count = len(checks)

    lines = [
        "# RQ1 Verification Summary",
        "",
        f"Core decision: `{core_decision}`",
        f"Audit chain complete: `{1.0 if audit_chain_complete else 0.0}`",
        "",
        "## RQ1 Purpose",
        "",
        (
            "RQ1 verifies the publication-grade real-corpus gate before retrieval "
            "benchmarking begins. It checks source-hash completeness, real-primary "
            "corpus status, wrong-collision absence, SC1 regression status, and "
            "auditability."
        ),
        "",
        "## Core Gate Summary",
        "",
        f"- passed gates: `{passed_count}/{total_count}`",
        f"- real_primary_corpus_rate: `{RQ1_FROZEN_RESULT['real_primary_corpus_rate']}`",
        f"- real_primary_chunk_rate: `{RQ1_FROZEN_RESULT['real_primary_chunk_rate']}`",
        f"- source_hash_final_present_rate: `{RQ1_FROZEN_RESULT['source_hash_final_present_rate']}`",
        f"- primary_real_rows: `{RQ1_FROZEN_RESULT['primary_real_rows']}`",
        f"- primary_real_target_correct_rate: `{RQ1_FROZEN_RESULT['primary_real_target_correct_rate']}`",
        f"- primary_real_wrong_collision_rate: `{RQ1_FROZEN_RESULT['primary_real_wrong_collision_rate']}`",
        f"- fail_count: `{RQ1_FROZEN_RESULT['fail_count']}`",
        f"- warn_count: `{RQ1_FROZEN_RESULT['warn_count']}`",
        "",
        "## MC Scope",
        "",
        f"- decision: `{mc_scope['decision']}`",
        f"- mc_cases: `{mc_scope['mc_cases']}`",
        f"- reason: {mc_scope['reason']}",
        "",
        "## URL Fetch Smoke",
        "",
        f"- decision: `{fetch_summary['decision']}`",
        f"- fetch_count: `{fetch_summary['fetch_count']}`",
        f"- fetch_ok_count: `{fetch_summary['fetch_ok_count']}`",
        f"- fetch_warn_count: `{fetch_summary['fetch_warn_count']}`",
        f"- fetch_error_count: `{fetch_summary['fetch_error_count']}`",
        "",
        "Fetch records are written to `rq1_url_fetch_records.csv`.",
        "",
        "## Notes",
        "",
        "- This verifier does not reproduce the full RQ2/RQ3 MC benchmarks.",
        "- URL fetch smoke is intentionally not a hard gate unless `--strict-fetch` is used.",
        "- If official sites block scripted fetching, create a dedicated RQ4 fetch reproducibility pipeline.",
    ]

    if core_failures:
        lines.extend(["", "## Core Failures", ""])
        for failure in core_failures:
            lines.append(f"- {failure}")

    if fetch_records:
        lines.extend(["", "## Fetch Record Preview", ""])
        for record in fetch_records:
            lines.append(
                f"- `{record.corpus_id}`: `{record.fetch_decision}` "
                f"status=`{record.http_status}` bytes=`{record.byte_length}`"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    core_decision: str,
    core_failures: Sequence[str],
    mc_scope: Dict[str, Any],
    fetch_summary: Dict[str, Any],
    audit_chain_complete: bool,
) -> None:
    print("=" * 80)
    print("HSRAG LAW — RQ1 VERIFICATION")
    print("=" * 80)
    print(f"core_decision: {core_decision}")
    print(f"audit_chain_complete: {1.0 if audit_chain_complete else 0.0}")
    print("")
    print("RQ1 frozen gates:")
    print(f"  decision: {RQ1_FROZEN_RESULT['decision']}")
    print(f"  corpus_count: {RQ1_FROZEN_RESULT['corpus_count']}")
    print(f"  real_primary_corpus_rate: {RQ1_FROZEN_RESULT['real_primary_corpus_rate']}")
    print(f"  real_primary_chunk_rate: {RQ1_FROZEN_RESULT['real_primary_chunk_rate']}")
    print(f"  source_hash_final_present_rate: {RQ1_FROZEN_RESULT['source_hash_final_present_rate']}")
    print(f"  primary_real_rows: {RQ1_FROZEN_RESULT['primary_real_rows']}")
    print(f"  primary_real_target_correct_rate: {RQ1_FROZEN_RESULT['primary_real_target_correct_rate']}")
    print(f"  primary_real_wrong_collision_rate: {RQ1_FROZEN_RESULT['primary_real_wrong_collision_rate']}")
    print(f"  sc1_regression_target_correct_rate: {RQ1_FROZEN_RESULT['sc1_regression_target_correct_rate']}")
    print(f"  fail_count: {RQ1_FROZEN_RESULT['fail_count']}")
    print(f"  warn_count: {RQ1_FROZEN_RESULT['warn_count']}")
    print("")
    print("MC scope:")
    print(f"  decision: {mc_scope['decision']}")
    print(f"  mc_cases: {mc_scope['mc_cases']}")
    print("")
    print("URL fetch smoke:")
    print(f"  decision: {fetch_summary['decision']}")
    print(f"  fetch_count: {fetch_summary['fetch_count']}")
    print(f"  fetch_ok_count: {fetch_summary['fetch_ok_count']}")
    print(f"  fetch_warn_count: {fetch_summary['fetch_warn_count']}")
    print(f"  fetch_error_count: {fetch_summary['fetch_error_count']}")
    print(f"  strict_fetch: {fetch_summary['strict_fetch']}")

    if core_failures:
        print("")
        print("Core failures:")
        for failure in core_failures:
            print(f"  - {failure}")

    print("")
    print(f"results_dir: {RESULTS_DIR}")
    print("=" * 80)


# =============================================================================
# Main
# =============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify HSRAG LAW RQ1 publication-grade corpus gate."
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip URL fetch smoke test.",
    )
    parser.add_argument(
        "--strict-fetch",
        action="store_true",
        help="Make URL fetch smoke failure affect process exit.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="HTTP timeout seconds for each URL fetch.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    ensure_dirs()

    source_manifest = load_or_create_source_manifest()

    # SGF step 1: core gate checks
    checks = build_rq1_gate_checks(RQ1_FROZEN_RESULT)
    core_decision, core_failures = summarize_gate_checks(checks)

    # SGF step 2: MC scope check
    mc_scope = evaluate_mc_scope(RQ1_FROZEN_RESULT)

    # SGF step 3: URL fetch smoke
    fetch_records = run_fetch_smoke(
        source_manifest,
        timeout_seconds=args.timeout,
        skip_fetch=args.skip_fetch,
    )
    fetch_summary = summarize_fetch_records(
        fetch_records,
        strict_fetch=args.strict_fetch,
    )

    # SGF step 4: audit chain
    audit_chain = build_audit_chain(checks, mc_scope, fetch_summary)
    audit_chain_complete = verify_audit_chain(audit_chain)

    # SGF step 5: consistency matrix
    consistency_matrix = build_consistency_matrix(
        core_decision=core_decision,
        mc_scope=mc_scope,
        fetch_summary=fetch_summary,
        audit_chain_complete=audit_chain_complete,
    )

    summary_payload = {
        "name": "HSRAG-LAW-RQ1-Verifier",
        "core_decision": core_decision,
        "core_failures": list(core_failures),
        "rq1_frozen_result": RQ1_FROZEN_RESULT,
        "gate_checks": [asdict(check) for check in checks],
        "mc_scope": mc_scope,
        "fetch_summary": fetch_summary,
        "audit_chain_complete": 1.0 if audit_chain_complete else 0.0,
        "consistency_matrix": consistency_matrix,
        "outputs": {
            "summary_json": "rq1_verification_summary.json",
            "summary_md": "rq1_verification_summary.md",
            "gate_checks_csv": "rq1_gate_checks.csv",
            "fetch_records_csv": "rq1_url_fetch_records.csv",
            "audit_chain_jsonl": "rq1_audit_chain.jsonl",
            "consistency_matrix_csv": "rq1_consistency_matrix.csv",
        },
    }

    # Outputs
    write_json(RESULTS_DIR / "rq1_verification_summary.json", summary_payload)
    write_gate_checks_csv(RESULTS_DIR / "rq1_gate_checks.csv", checks)
    write_fetch_records_csv(RESULTS_DIR / "rq1_url_fetch_records.csv", fetch_records)
    write_audit_chain(RESULTS_DIR / "rq1_audit_chain.jsonl", audit_chain)
    write_consistency_matrix_csv(
        RESULTS_DIR / "rq1_consistency_matrix.csv",
        consistency_matrix,
    )
    write_markdown_summary(
        RESULTS_DIR / "rq1_verification_summary.md",
        core_decision=core_decision,
        core_failures=core_failures,
        checks=checks,
        mc_scope=mc_scope,
        fetch_summary=fetch_summary,
        fetch_records=fetch_records,
        audit_chain_complete=audit_chain_complete,
    )

    print_summary(
        core_decision=core_decision,
        core_failures=core_failures,
        mc_scope=mc_scope,
        fetch_summary=fetch_summary,
        audit_chain_complete=audit_chain_complete,
    )

    hard_fail = False

    if core_decision != "RQ1_VERIFICATION_PASS":
        hard_fail = True

    if not audit_chain_complete:
        hard_fail = True

    if args.strict_fetch and fetch_summary["decision"] in {
        "FETCH_STRICT_FAIL",
        "FETCH_HARD_GATE_FAIL",
    }:
        hard_fail = True

    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())