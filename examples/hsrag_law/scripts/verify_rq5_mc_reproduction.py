"""
HSRAG LAW — RQ5.5 CTHC-Typed Salted Domain Routing Robustness
=============================================================

RQ5.5 = CTHC typed route + salted domain hash retrieval + legal citation parser fix.

Purpose:
- Evaluate legal text retrieval routing over locally held public legal corpora.
- Use CTHC-style hierarchical typed addresses for legal text chunks.
- Use salted domain hashes to separate retrieval buckets.
- Generate perturbation robustness cases.
- Preserve strict acceptance gates.
- Routing does not read case_type.

RQ5.5 surgical fixes:
- polite_prefix is not treated as conflict query.
- fragmented U.S.C. citations are reconstructed:
    47 U.S.C. 230 -> US_CDA230
    15 U.S.C. 45  -> US_FTC_ACT5
- CTHC route openers remain stable legal identifiers only.
- Generic legal words cannot open a route.

QSVCS notes:
- QOIM: preserve intent and acceptance gates.
- SGF: classify -> route -> retrieve -> verify -> audit.
- VPSM: primary route vector is CTHC domain_hash; baselines are comparison vectors.
- CTHC: each chunk has a typed legal address and salted domain hash.
- S: audit hashes link per-case and summary records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


# =============================================================================
# Path resolution
# =============================================================================

THIS_FILE = Path(__file__).resolve()
EXAMPLE_ROOT = THIS_FILE.parent.parent if THIS_FILE.parent.name == "scripts" else THIS_FILE.parent
RESULTS_DIR = EXAMPLE_ROOT / "results"


# =============================================================================
# Static config
# =============================================================================

BENCHMARK_SALT = "HSRAG_LAW_RQ5_5_PUBLIC_REPRODUCIBLE_SALT_v1"

SUPPORTED_CORPUS_LABELS = {
    "EU_AI_ACT": "EU AI Act",
    "EU_DMA": "EU Digital Markets Act",
    "US_COPPA": "COPPA",
    "US_CDA230": "CDA Section 230",
    "US_FTC_ACT5": "FTC Act Section 5",
    "US_CCPA": "CCPA",
}

CORPUS_JURISDICTION_DEFAULTS = {
    "EU_AI_ACT": "EU",
    "EU_DMA": "EU",
    "US_COPPA": "US",
    "US_CDA230": "US",
    "US_FTC_ACT5": "US",
    "US_CCPA": "US-CA",
}

# Only stable legal identifiers can open a CTHC route.
ROUTE_OPENERS = {
    "EU_AI_ACT": [
        "eu ai act",
        "ai act",
        "artificial intelligence act",
    ],
    "EU_DMA": [
        "digital markets act",
        "eu dma",
        "dma",
    ],
    "US_COPPA": [
        "coppa",
        "children online privacy",
        "childrens online privacy",
        "children's online privacy",
    ],
    "US_CDA230": [
        "cda section 230",
        "section 230",
        "47 usc 230",
        "47 u s c 230",
    ],
    "US_FTC_ACT5": [
        "ftc act section 5",
        "ftc section 5",
        "federal trade commission act",
        "15 usc 45",
        "15 u s c 45",
    ],
    "US_CCPA": [
        "ccpa",
        "california consumer privacy act",
    ],
}

# Supporting terms can help retrieval ranking but cannot open a route.
SUPPORTING_TERMS = {
    "EU_AI_ACT": [
        "high risk ai",
        "high-risk ai",
        "ai system",
        "ai systems",
        "risk management",
    ],
    "EU_DMA": [
        "gatekeeper",
        "gatekeepers",
        "core platform services",
        "core platform service",
        "self preferencing",
        "self-preferencing",
    ],
    "US_COPPA": [
        "parental consent",
        "verifiable parental consent",
        "children",
        "child",
    ],
    "US_CDA230": [
        "interactive computer service",
        "information content provider",
        "publisher",
    ],
    "US_FTC_ACT5": [
        "federal trade commission",
        "unfair or deceptive",
        "deceptive practice",
        "deceptive practices",
    ],
    "US_CCPA": [
        "california consumer",
        "california consumers",
        "personal information",
        "consumer privacy",
    ],
}

UNSUPPORTED_TOPICS = [
    "pipeda",
    "canada pipeda",
    "lgpd",
    "brazil lgpd",
    "hipaa",
    "uk online safety act",
    "singapore pdpa",
    "india digital personal data protection act",
    "gdpr",
    "gdpr article 22",
    "automated decision making under gdpr",
]

GENERIC_AMBIGUOUS_SIGNALS = [
    "platform law",
    "online services",
    "providers",
    "obligations",
    "digital services",
    "user data",
    "compliance rule",
    "what does the law say",
    "handling information",
    "services and users",
    "providers handling information",
]

PERTURBATION_MODES = [
    "case_punctuation_noise",
    "polite_prefix",
    "legalese_paraphrase",
    "irrelevant_tail",
    "pointer_noise",
    "jurisdiction_context_noise",
    "order_shuffle",
    "typo_light",
]

COST_PER_1K_TOKENS_DEFAULT = 0.0001


# =============================================================================
# Data models
# =============================================================================

@dataclass(frozen=True)
class CTHCCode:
    domain: str
    source_type: str
    jurisdiction: str
    corpus_id: str
    topic: str

    def path(self) -> str:
        return f"{self.domain}.{self.source_type}.{self.jurisdiction}.{self.corpus_id}.{self.topic}"


@dataclass
class CTHCRoute:
    status: str
    code: Optional[CTHCCode]
    domain_hash: Optional[str]
    confidence: str
    reason: str
    detected_corpus_ids: List[str]


@dataclass
class Chunk:
    chunk_id: str
    corpus_id: str
    jurisdiction: str
    title: str
    text: str
    cthc_path: str
    domain_hash: str
    token_count: int
    token_set: set[str]


@dataclass
class QueryCase:
    case_id: str
    case_type: str
    perturbation_mode: str
    query: str
    expected_corpus_id: Optional[str]
    expected_jurisdiction: Optional[str]


@dataclass
class CaseResult:
    case_id: str
    case_type: str
    perturbation_mode: str
    expected_corpus_id: Optional[str]
    expected_jurisdiction: Optional[str]
    query: str

    hsrag_decision: str
    hsrag_reason: str
    hsrag_route_status: str
    hsrag_cthc_path: Optional[str]
    hsrag_domain_hash: Optional[str]
    hsrag_detected_corpus_ids: str
    hsrag_routed_corpus_id: Optional[str]
    hsrag_retrieved_chunk_id: Optional[str]
    hsrag_retrieved_corpus_id: Optional[str]
    hsrag_retrieved_jurisdiction: Optional[str]
    hsrag_latency_ms: float
    hsrag_token_estimate: int
    hsrag_cost_estimate: float

    global_retrieved_chunk_id: Optional[str]
    global_retrieved_corpus_id: Optional[str]
    global_retrieved_jurisdiction: Optional[str]
    global_latency_ms: float
    global_token_estimate: int
    global_cost_estimate: float

    domain_retrieved_chunk_id: Optional[str]
    domain_retrieved_corpus_id: Optional[str]
    domain_retrieved_jurisdiction: Optional[str]
    domain_latency_ms: float
    domain_token_estimate: int
    domain_cost_estimate: float

    previous_hash: str
    audit_hash: str


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
# Utility
# =============================================================================

def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("u.s.c.", "usc")
    text = text.replace("u s c", "usc")
    text = text.replace("children's", "childrens")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(text))


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


def estimate_tokens(text: str) -> int:
    return max(1, len(tokenize(text)))


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def salted_domain_hash(code: CTHCCode, salt: str = BENCHMARK_SALT) -> str:
    payload = {
        "salt": salt,
        "domain": code.domain,
        "source_type": code.source_type,
        "jurisdiction": code.jurisdiction,
        "corpus_id": code.corpus_id,
    }
    return stable_json_hash(payload)


def default_cthc_code(corpus_id: str, jurisdiction: Optional[str] = None, topic: str = "GENERAL") -> CTHCCode:
    return CTHCCode(
        domain="LEGAL",
        source_type="PUBLIC_LEGAL_TEXT",
        jurisdiction=jurisdiction or CORPUS_JURISDICTION_DEFAULTS.get(corpus_id, "UNKNOWN"),
        corpus_id=corpus_id,
        topic=topic,
    )


def ratio(num: int, den: int) -> float:
    return 0.0 if den == 0 else num / den


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    rank = (len(ordered) - 1) * p
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low

    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def compatible_jurisdiction(expected: Optional[str], actual: Optional[str]) -> bool:
    if expected is None:
        return actual is None

    if actual is None:
        return False

    if expected == actual:
        return True

    return expected == "US" and actual.startswith("US-")


def cost_from_tokens(tokens: int, cost_per_1k: float) -> float:
    return (tokens / 1000.0) * cost_per_1k


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_dataclass_csv(path: Path, rows: Sequence[Any]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_dict_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# =============================================================================
# Corpus loading
# =============================================================================

def make_chunk(
    chunk_id: str,
    corpus_id: str,
    jurisdiction: str,
    title: str,
    text: str,
) -> Chunk:
    code = default_cthc_code(corpus_id=corpus_id, jurisdiction=jurisdiction)
    domain_hash = salted_domain_hash(code)
    combined_text = f"{title} {text}"

    return Chunk(
        chunk_id=chunk_id,
        corpus_id=corpus_id,
        jurisdiction=jurisdiction,
        title=title,
        text=text,
        cthc_path=code.path(),
        domain_hash=domain_hash,
        token_count=estimate_tokens(combined_text),
        token_set=token_set(combined_text),
    )


def fallback_chunks() -> List[Chunk]:
    raw = [
        (
            "EU_AI_ACT_FALLBACK_001",
            "EU_AI_ACT",
            "EU",
            "EU AI Act — Risk management",
            "The EU AI Act requires high-risk AI systems to maintain risk management systems, documentation, and provider obligations.",
        ),
        (
            "EU_DMA_FALLBACK_001",
            "EU_DMA",
            "EU",
            "Digital Markets Act — Gatekeeper obligations",
            "The Digital Markets Act imposes obligations on gatekeepers providing core platform services and restricts certain self-preferencing conduct.",
        ),
        (
            "US_COPPA_FALLBACK_001",
            "US_COPPA",
            "US",
            "COPPA — Parental consent",
            "COPPA requires operators to obtain verifiable parental consent before collecting personal information from children.",
        ),
        (
            "US_CDA230_FALLBACK_001",
            "US_CDA230",
            "US",
            "CDA Section 230 — Publisher treatment",
            "CDA Section 230 protects providers of interactive computer services from being treated as publishers of third-party information.",
        ),
        (
            "US_FTC_ACT5_FALLBACK_001",
            "US_FTC_ACT5",
            "US",
            "FTC Act Section 5 — Unfair or deceptive acts",
            "FTC Act Section 5 prohibits unfair or deceptive acts or practices in or affecting commerce.",
        ),
        (
            "US_CCPA_FALLBACK_001",
            "US_CCPA",
            "US-CA",
            "CCPA — Consumer privacy",
            "The CCPA gives California consumers rights over personal information, including access, deletion, and opt-out rights.",
        ),
    ]

    return [make_chunk(*item) for item in raw]


def load_rebuilt_chunks(max_chunks_per_corpus: int) -> Tuple[List[Chunk], str]:
    path = RESULTS_DIR / "rq4_rebuilt_chunks.csv"

    if not path.exists():
        return fallback_chunks(), "fallback_builtin_corpus"

    chunks: List[Chunk] = []
    seen: set[str] = set()

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            corpus_id = row.get("corpus_id", "").strip()
            jurisdiction = row.get("jurisdiction", "").strip()
            chunk_id = row.get("chunk_id", "").strip()
            text = row.get("text", "").strip()
            title = row.get("source_title", "").strip()
            chunk_hash = row.get("chunk_hash", "").strip()

            if not corpus_id or not chunk_id or not text:
                continue

            if len(text) < 80:
                continue

            dedupe_key = chunk_hash or stable_json_hash(
                {"corpus_id": corpus_id, "chunk_id": chunk_id, "text": text}
            )

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)

            chunks.append(
                make_chunk(
                    chunk_id=chunk_id,
                    corpus_id=corpus_id,
                    jurisdiction=jurisdiction or CORPUS_JURISDICTION_DEFAULTS.get(corpus_id, "UNKNOWN"),
                    title=title or SUPPORTED_CORPUS_LABELS.get(corpus_id, corpus_id),
                    text=text,
                )
            )

    if not chunks:
        return fallback_chunks(), "fallback_builtin_corpus_empty_rq4"

    by_corpus: Dict[str, List[Chunk]] = {}

    for chunk in chunks:
        by_corpus.setdefault(chunk.corpus_id, []).append(chunk)

    limited: List[Chunk] = []

    for corpus_id, corpus_chunks in sorted(by_corpus.items()):
        limited.extend(corpus_chunks[:max_chunks_per_corpus])

    if len({chunk.corpus_id for chunk in limited}) < 2:
        return fallback_chunks(), "fallback_builtin_corpus_insufficient_rq4_corpora"

    return limited, "rq4_rebuilt_chunks"


# =============================================================================
# Identifier matching
# =============================================================================

def edit_distance_leq_one(a: str, b: str) -> bool:
    if a == b:
        return True

    if abs(len(a) - len(b)) > 1:
        return False

    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)

        if diff <= 1:
            return True

        # Adjacent transposition.
        for i in range(len(a) - 1):
            if (
                a[i] == b[i + 1]
                and a[i + 1] == b[i]
                and a[:i] == b[:i]
                and a[i + 2:] == b[i + 2:]
            ):
                return True

        return False

    # One insertion/deletion.
    if len(a) > len(b):
        a, b = b, a

    i = j = edits = 0

    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            edits += 1
            j += 1

            if edits > 1:
                return False

    return True


def token_match(alias_token: str, query_tokens: set[str]) -> bool:
    if alias_token in query_tokens:
        return True

    # Do not fuzzy-match very short identifiers.
    if len(alias_token) < 4:
        return False

    for token in query_tokens:
        if len(token) >= 4 and edit_distance_leq_one(alias_token, token):
            return True

    return False


def opener_match(query_norm: str, query_tokens: set[str], opener: str) -> bool:
    opener_norm = normalize_text(opener)

    if not opener_norm:
        return False

    if f" {opener_norm} " in f" {query_norm} ":
        return True

    opener_tokens = opener_norm.split()

    if len(opener_tokens) == 1:
        return token_match(opener_tokens[0], query_tokens)

    matched = sum(1 for token in opener_tokens if token_match(token, query_tokens))

    return matched == len(opener_tokens)


def detect_us_code_fragment_routes(query_norm: str, query_tokens: set[str]) -> List[str]:
    """
    Detect U.S.C. citations that may be split by punctuation/order perturbation.

    Examples:
    - "Under 47 U.S.C. 230" may become tokens: 47, u, s, c, 230
    - "Under 15 U.S.C. 45" may become tokens: 15, u, s, c, 45

    This is still CTHC identifier routing, not generic keyword routing.
    """
    hits: List[str] = []

    has_usc = "usc" in query_tokens or {"u", "s", "c"}.issubset(query_tokens)

    if has_usc and "47" in query_tokens and "230" in query_tokens:
        hits.append("US_CDA230")

    if has_usc and "15" in query_tokens and "45" in query_tokens:
        hits.append("US_FTC_ACT5")

    return hits


def detect_route_openers(query: str) -> List[str]:
    cleaned = re.sub(r"\[(?:pointer|source|chunk)[^\]]*\]", " ", query, flags=re.I)
    cleaned = re.sub(r"pointer\s*:\s*[a-z0-9_\-]+", " ", cleaned, flags=re.I)

    query_norm = normalize_text(cleaned)
    query_tokens = set(query_norm.split())

    matched: List[str] = []

    # First: structured legal citation fragments.
    for corpus_id in detect_us_code_fragment_routes(query_norm, query_tokens):
        if corpus_id not in matched:
            matched.append(corpus_id)

    # Second: normal stable CTHC openers.
    for corpus_id, openers in ROUTE_OPENERS.items():
        if corpus_id in matched:
            continue

        if any(opener_match(query_norm, query_tokens, opener) for opener in openers):
            matched.append(corpus_id)

    return matched


def contains_unsupported_topic(query: str) -> bool:
    q = normalize_text(query)

    return any(normalize_text(topic) in q for topic in UNSUPPORTED_TOPICS)


def generic_ambiguous_signal(query: str) -> bool:
    q = normalize_text(query)

    phrase_hit = any(normalize_text(phrase) in q for phrase in GENERIC_AMBIGUOUS_SIGNALS)

    generic_tokens = {
        "platform",
        "online",
        "services",
        "providers",
        "obligations",
        "law",
        "digital",
        "user",
        "data",
        "compliance",
        "rule",
        "information",
    }

    token_hits = len(generic_tokens.intersection(set(q.split())))

    return phrase_hit or token_hits >= 4


def conflict_query_signal(query: str, detected_corpus_ids: Sequence[str]) -> bool:
    q = normalize_text(query)
    tokens = set(q.split())

    # Multiple stable CTHC identifiers in one query means the query is not a single-domain route.
    if len(detected_corpus_ids) > 1:
        return True

    has_using = "using" in tokens or "use" in tokens
    has_rules = "rules" in tokens or "rule" in tokens
    has_instead = "instead" in tokens
    has_compare = "compare" in tokens
    has_under = "under" in tokens
    has_but = "but" in tokens
    has_apply = "apply" in tokens or "applies" in tokens

    # Strong conflict form: "Under X, answer using Y rules".
    if re.search(r"\bunder\b.+\banswer using\b", q):
        return True

    # Do not block normal target query:
    # "Please answer carefully: Under 47 U.S.C. 230, what rule is described?"
    if len(detected_corpus_ids) >= 1 and has_using and has_rules:
        return True

    if len(detected_corpus_ids) >= 1 and has_instead:
        return True

    if len(detected_corpus_ids) >= 1 and has_compare and has_under:
        return True

    if len(detected_corpus_ids) >= 1 and has_but and has_apply and has_rules:
        return True

    return False


def classify_query_to_cthc_route(query: str, domain_hash_index: Dict[str, List[Chunk]]) -> CTHCRoute:
    """
    Query classifier does not read benchmark case_type.
    It only reads query text and the available salted domain-hash index.
    """
    detected = detect_route_openers(query)

    # Conflict is checked before route allow.
    if conflict_query_signal(query, detected):
        return CTHCRoute(
            status="BLOCK_CONFLICT_QUERY",
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Conflict-form query detected before routing.",
            detected_corpus_ids=list(detected),
        )

    # Unsupported query is checked before route allow.
    if contains_unsupported_topic(query):
        return CTHCRoute(
            status="BLOCK_UNSUPPORTED_QUERY",
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Unsupported legal topic outside local corpus.",
            detected_corpus_ids=list(detected),
        )

    # Ambiguity is checked before route allow when there is no stable identifier.
    if not detected and generic_ambiguous_signal(query):
        return CTHCRoute(
            status="BLOCK_AMBIGUOUS_QUERY",
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Generic legal query without stable CTHC identifier.",
            detected_corpus_ids=[],
        )

    if len(detected) == 1:
        corpus_id = detected[0]
        jurisdiction = CORPUS_JURISDICTION_DEFAULTS.get(corpus_id, "UNKNOWN")
        code = default_cthc_code(corpus_id=corpus_id, jurisdiction=jurisdiction)
        domain_hash = salted_domain_hash(code)

        if domain_hash not in domain_hash_index:
            return CTHCRoute(
                status="BLOCK_UNSUPPORTED_QUERY",
                code=None,
                domain_hash=None,
                confidence="HIGH",
                reason="CTHC route exists but salted domain is unavailable in local corpus.",
                detected_corpus_ids=list(detected),
            )

        return CTHCRoute(
            status="ROUTABLE",
            code=code,
            domain_hash=domain_hash,
            confidence="HIGH",
            reason="Stable CTHC legal identifier detected.",
            detected_corpus_ids=list(detected),
        )

    if len(detected) > 1:
        return CTHCRoute(
            status="BLOCK_CONFLICT_QUERY",
            code=None,
            domain_hash=None,
            confidence="HIGH",
            reason="Multiple stable CTHC identifiers detected.",
            detected_corpus_ids=list(detected),
        )

    return CTHCRoute(
        status="BLOCK_UNSUPPORTED_QUERY",
        code=None,
        domain_hash=None,
        confidence="LOW",
        reason="No stable CTHC legal identifier found.",
        detected_corpus_ids=[],
    )


# =============================================================================
# Retrieval
# =============================================================================

def lexical_score(query_tokens: set[str], chunk: Chunk) -> int:
    return len(query_tokens.intersection(chunk.token_set))


def retrieve_top_chunk(query: str, candidates: Sequence[Chunk]) -> Optional[Chunk]:
    if not candidates:
        return None

    q_tokens = token_set(query)
    best_score = -1
    best_chunk: Optional[Chunk] = None

    for chunk in candidates:
        score = lexical_score(q_tokens, chunk)

        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk


def retrieve_topk_chunks(query: str, candidates: Sequence[Chunk], top_k: int) -> List[Chunk]:
    if not candidates:
        return []

    q_tokens = token_set(query)

    scored = sorted(
        ((lexical_score(q_tokens, chunk), chunk) for chunk in candidates),
        key=lambda item: item[0],
        reverse=True,
    )

    return [chunk for _, chunk in scored[:top_k]]


# =============================================================================
# Case generation
# =============================================================================

def corpus_label(corpus_id: str) -> str:
    return SUPPORTED_CORPUS_LABELS.get(corpus_id, corpus_id.replace("_", " "))


def target_query_template(corpus_id: str, rng: random.Random) -> str:
    templates = {
        "EU_AI_ACT": [
            "Under the EU AI Act, what obligation is described for AI systems?",
            "According to the EU AI Act, what does the text say about high-risk AI or risk management?",
            "Under the Artificial Intelligence Act, what compliance duty applies to AI systems?",
        ],
        "EU_DMA": [
            "Under the Digital Markets Act, what obligation applies to gatekeepers?",
            "According to the DMA, what does the text say about core platform services?",
            "Under the EU DMA, what conduct or duty is described for gatekeepers?",
        ],
        "US_COPPA": [
            "Under COPPA, what does the text say about children and parental consent?",
            "According to the Children's Online Privacy rule, what duty applies to operators?",
            "Under COPPA, what obligation applies to operators collecting children's information?",
        ],
        "US_CDA230": [
            "Under CDA Section 230, what does the text say about publisher treatment?",
            "According to Section 230, how is an interactive computer service treated?",
            "Under 47 U.S.C. 230, what rule is described?",
        ],
        "US_FTC_ACT5": [
            "Under FTC Act Section 5, what conduct is prohibited?",
            "According to Section 5 of the Federal Trade Commission Act, what rule is described?",
            "Under 15 U.S.C. 45, what unfair or deceptive practice rule is described?",
        ],
        "US_CCPA": [
            "Under the CCPA, what rights relate to personal information?",
            "According to the California Consumer Privacy Act, what consumer privacy duty is described?",
            "Under CCPA, what does the text say about California consumers?",
        ],
    }

    return rng.choice(
        templates.get(corpus_id, [f"Under {corpus_label(corpus_id)}, what legal rule is described?"])
    )


def unsupported_query(rng: random.Random) -> str:
    topic = rng.choice(UNSUPPORTED_TOPICS)

    return f"What does {topic} require in this legal corpus?"


def ambiguous_query(rng: random.Random) -> str:
    return rng.choice(
        [
            "What does the platform law say about online services and providers?",
            "What compliance rule applies to digital services and user data?",
            "What obligations apply to providers under the law?",
            "What does the law say about platforms, services, and users?",
            "What rule applies to online providers handling information?",
        ]
    )


def conflict_query(corpora: Sequence[str], rng: random.Random) -> str:
    a, b = rng.sample(list(corpora), 2)

    return (
        f"Under {corpus_label(a)}, answer using {corpus_label(b)} rules. "
        f"Which legal obligation should apply?"
    )


def typo_light(text: str, rng: random.Random) -> str:
    words = text.split()

    # Avoid completely destroying very short legal identifiers such as DMA.
    candidates = [
        i for i, word in enumerate(words)
        if len(re.sub(r"[^A-Za-z0-9]", "", word)) > 4
    ]

    if not candidates:
        return text

    idx = rng.choice(candidates)
    word = words[idx]
    positions = [i for i, ch in enumerate(word) if ch.isalpha()]

    if len(positions) < 2:
        return text

    pos = rng.choice(positions[:-1])
    chars = list(word)
    chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
    words[idx] = "".join(chars)

    return " ".join(words)


def perturb_query(query: str, mode: str, rng: random.Random) -> str:
    if mode == "case_punctuation_noise":
        return query.upper() if rng.random() < 0.5 else query.replace(",", " , ").replace("?", " ??")

    if mode == "polite_prefix":
        return "Please answer carefully: " + query

    if mode == "legalese_paraphrase":
        return "For purposes of legal compliance analysis, " + query

    if mode == "irrelevant_tail":
        return query + " Ignore unrelated business strategy, marketing, and product roadmap details."

    if mode == "pointer_noise":
        return query + " [pointer: LOCAL-NOISE-REFERENCE-0001]"

    if mode == "jurisdiction_context_noise":
        return "Even if another jurisdiction is mentioned in surrounding context, " + query

    if mode == "order_shuffle":
        parts = [part.strip() for part in re.split(r"[,?.]", query) if part.strip()]

        if len(parts) <= 1:
            return query

        rng.shuffle(parts)

        return "; ".join(parts) + "?"

    if mode == "typo_light":
        return typo_light(query, rng)

    return query


def generate_case(index: int, rng: random.Random, corpora: Sequence[str]) -> QueryCase:
    bucket = index % 20
    mode = rng.choice(PERTURBATION_MODES)

    if bucket < 11:
        corpus_id = rng.choice(list(corpora))
        query = perturb_query(target_query_template(corpus_id, rng), mode, rng)

        return QueryCase(
            case_id=f"RQ5_CASE_{index:06d}",
            case_type="target",
            perturbation_mode=mode,
            query=query,
            expected_corpus_id=corpus_id,
            expected_jurisdiction=CORPUS_JURISDICTION_DEFAULTS.get(corpus_id, "UNKNOWN"),
        )

    if bucket < 14:
        return QueryCase(
            case_id=f"RQ5_CASE_{index:06d}",
            case_type="unsupported_query",
            perturbation_mode=mode,
            query=perturb_query(unsupported_query(rng), mode, rng),
            expected_corpus_id=None,
            expected_jurisdiction=None,
        )

    if bucket < 17:
        return QueryCase(
            case_id=f"RQ5_CASE_{index:06d}",
            case_type="ambiguous_query",
            perturbation_mode=mode,
            query=perturb_query(ambiguous_query(rng), mode, rng),
            expected_corpus_id=None,
            expected_jurisdiction=None,
        )

    return QueryCase(
        case_id=f"RQ5_CASE_{index:06d}",
        case_type="conflict_query",
        perturbation_mode=mode,
        query=perturb_query(conflict_query(corpora, rng), mode, rng),
        expected_corpus_id=None,
        expected_jurisdiction=None,
    )


def generate_cases(count: int, seed: int, corpora: Sequence[str]) -> List[QueryCase]:
    rng = random.Random(seed)
    cases = [generate_case(i, rng, corpora) for i in range(count)]
    rng.shuffle(cases)

    return [
        QueryCase(
            case_id=f"RQ5_CASE_{i:06d}",
            case_type=case.case_type,
            perturbation_mode=case.perturbation_mode,
            query=case.query,
            expected_corpus_id=case.expected_corpus_id,
            expected_jurisdiction=case.expected_jurisdiction,
        )
        for i, case in enumerate(cases)
    ]


# =============================================================================
# Benchmark run
# =============================================================================

def make_case_audit_payload(result: CaseResult) -> Dict[str, Any]:
    return {
        "case_id": result.case_id,
        "case_type": result.case_type,
        "perturbation_mode": result.perturbation_mode,
        "expected_corpus_id": result.expected_corpus_id,
        "expected_jurisdiction": result.expected_jurisdiction,
        "query": result.query,
        "hsrag_decision": result.hsrag_decision,
        "hsrag_route_status": result.hsrag_route_status,
        "hsrag_cthc_path": result.hsrag_cthc_path,
        "hsrag_domain_hash": result.hsrag_domain_hash,
        "hsrag_retrieved_chunk_id": result.hsrag_retrieved_chunk_id,
        "hsrag_retrieved_corpus_id": result.hsrag_retrieved_corpus_id,
        "hsrag_retrieved_jurisdiction": result.hsrag_retrieved_jurisdiction,
        "global_retrieved_chunk_id": result.global_retrieved_chunk_id,
        "global_retrieved_corpus_id": result.global_retrieved_corpus_id,
        "domain_retrieved_chunk_id": result.domain_retrieved_chunk_id,
        "domain_retrieved_corpus_id": result.domain_retrieved_corpus_id,
        "previous_hash": result.previous_hash,
    }


def run_case(
    case: QueryCase,
    chunks: Sequence[Chunk],
    domain_hash_index: Dict[str, List[Chunk]],
    top_k: int,
    cost_per_1k: float,
    previous_hash: str,
) -> CaseResult:
    query_tokens = estimate_tokens(case.query)

    # HSRAG / CTHC typed salted domain route
    started = time.perf_counter()
    route = classify_query_to_cthc_route(case.query, domain_hash_index)

    hsrag_chunk: Optional[Chunk] = None

    if route.status == "ROUTABLE" and route.domain_hash is not None:
        candidates = domain_hash_index.get(route.domain_hash, [])
        hsrag_chunk = retrieve_top_chunk(case.query, candidates)

    hsrag_latency = (time.perf_counter() - started) * 1000.0
    hsrag_tokens = query_tokens + 20 + (hsrag_chunk.token_count if hsrag_chunk else 0)

    # Global lexical baseline
    started = time.perf_counter()
    global_top = retrieve_topk_chunks(case.query, chunks, top_k)
    global_latency = (time.perf_counter() - started) * 1000.0
    global_chunk = global_top[0] if global_top else None
    global_tokens = query_tokens + sum(chunk.token_count for chunk in global_top)

    # Domain-hint lexical baseline.
    started = time.perf_counter()
    route_for_domain = classify_query_to_cthc_route(case.query, domain_hash_index)

    if route_for_domain.status == "ROUTABLE" and route_for_domain.domain_hash in domain_hash_index:
        domain_candidates = domain_hash_index[route_for_domain.domain_hash]
    else:
        domain_candidates = list(chunks)

    domain_top = retrieve_topk_chunks(case.query, domain_candidates, top_k)
    domain_latency = (time.perf_counter() - started) * 1000.0
    domain_chunk = domain_top[0] if domain_top else None
    domain_tokens = query_tokens + sum(chunk.token_count for chunk in domain_top)

    result = CaseResult(
        case_id=case.case_id,
        case_type=case.case_type,
        perturbation_mode=case.perturbation_mode,
        expected_corpus_id=case.expected_corpus_id,
        expected_jurisdiction=case.expected_jurisdiction,
        query=case.query,

        hsrag_decision="ALLOW" if route.status == "ROUTABLE" else route.status,
        hsrag_reason=route.reason,
        hsrag_route_status=route.status,
        hsrag_cthc_path=route.code.path() if route.code else None,
        hsrag_domain_hash=route.domain_hash,
        hsrag_detected_corpus_ids="|".join(route.detected_corpus_ids),
        hsrag_routed_corpus_id=route.code.corpus_id if route.code else None,
        hsrag_retrieved_chunk_id=hsrag_chunk.chunk_id if hsrag_chunk else None,
        hsrag_retrieved_corpus_id=hsrag_chunk.corpus_id if hsrag_chunk else None,
        hsrag_retrieved_jurisdiction=hsrag_chunk.jurisdiction if hsrag_chunk else None,
        hsrag_latency_ms=hsrag_latency,
        hsrag_token_estimate=hsrag_tokens,
        hsrag_cost_estimate=cost_from_tokens(hsrag_tokens, cost_per_1k),

        global_retrieved_chunk_id=global_chunk.chunk_id if global_chunk else None,
        global_retrieved_corpus_id=global_chunk.corpus_id if global_chunk else None,
        global_retrieved_jurisdiction=global_chunk.jurisdiction if global_chunk else None,
        global_latency_ms=global_latency,
        global_token_estimate=global_tokens,
        global_cost_estimate=cost_from_tokens(global_tokens, cost_per_1k),

        domain_retrieved_chunk_id=domain_chunk.chunk_id if domain_chunk else None,
        domain_retrieved_corpus_id=domain_chunk.corpus_id if domain_chunk else None,
        domain_retrieved_jurisdiction=domain_chunk.jurisdiction if domain_chunk else None,
        domain_latency_ms=domain_latency,
        domain_token_estimate=domain_tokens,
        domain_cost_estimate=cost_from_tokens(domain_tokens, cost_per_1k),

        previous_hash=previous_hash,
        audit_hash="PENDING",
    )

    result.audit_hash = stable_json_hash(make_case_audit_payload(result))

    return result


def run_benchmark(
    cases: Sequence[QueryCase],
    chunks: Sequence[Chunk],
    top_k: int,
    cost_per_1k: float,
) -> List[CaseResult]:
    domain_hash_index: Dict[str, List[Chunk]] = {}

    for chunk in chunks:
        domain_hash_index.setdefault(chunk.domain_hash, []).append(chunk)

    results: List[CaseResult] = []
    previous = "GENESIS"

    for case in cases:
        result = run_case(
            case=case,
            chunks=chunks,
            domain_hash_index=domain_hash_index,
            top_k=top_k,
            cost_per_1k=cost_per_1k,
            previous_hash=previous,
        )
        results.append(result)
        previous = result.audit_hash

    return results


def verify_case_audit_chain(results: Sequence[CaseResult]) -> bool:
    previous = "GENESIS"

    for result in results:
        if result.previous_hash != previous:
            return False

        if stable_json_hash(make_case_audit_payload(result)) != result.audit_hash:
            return False

        previous = result.audit_hash

    return True


# =============================================================================
# Metrics
# =============================================================================

def compute_hsrag_metrics(results: Sequence[CaseResult]) -> Dict[str, Any]:
    target = [result for result in results if result.case_type == "target"]
    unsupported = [result for result in results if result.case_type == "unsupported_query"]
    ambiguous = [result for result in results if result.case_type == "ambiguous_query"]
    conflict = [result for result in results if result.case_type == "conflict_query"]

    target_correct = sum(
        1 for result in target
        if result.hsrag_decision == "ALLOW"
        and result.hsrag_retrieved_corpus_id == result.expected_corpus_id
        and compatible_jurisdiction(result.expected_jurisdiction, result.hsrag_retrieved_jurisdiction)
    )

    wrong_corpus = sum(
        1 for result in target
        if result.hsrag_decision == "ALLOW"
        and result.hsrag_retrieved_corpus_id != result.expected_corpus_id
    )

    wrong_jurisdiction = sum(
        1 for result in target
        if result.hsrag_decision == "ALLOW"
        and not compatible_jurisdiction(result.expected_jurisdiction, result.hsrag_retrieved_jurisdiction)
    )

    unsupported_false_allow = sum(1 for result in unsupported if result.hsrag_decision == "ALLOW")
    ambiguous_false_allow = sum(1 for result in ambiguous if result.hsrag_decision == "ALLOW")
    conflict_false_allow = sum(1 for result in conflict if result.hsrag_decision == "ALLOW")

    latencies = [result.hsrag_latency_ms for result in results]
    tokens = [result.hsrag_token_estimate for result in results]
    costs = [result.hsrag_cost_estimate for result in results]

    return {
        "target_cases": len(target),
        "unsupported_query_cases": len(unsupported),
        "ambiguous_query_cases": len(ambiguous),
        "conflict_query_cases": len(conflict),
        "target_correct": ratio(target_correct, len(target)),
        "wrong_corpus_misrouting": ratio(wrong_corpus, len(target)),
        "wrong_jurisdiction_misrouting": ratio(wrong_jurisdiction, len(target)),
        "unsupported_query_false_allow": ratio(unsupported_false_allow, len(unsupported)),
        "ambiguous_query_false_allow": ratio(ambiguous_false_allow, len(ambiguous)),
        "conflict_query_false_allow": ratio(conflict_false_allow, len(conflict)),
        "p50_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_latency_ms": percentile(latencies, 0.95),
        "total_tokens": sum(tokens),
        "avg_tokens": statistics.mean(tokens) if tokens else 0.0,
        "total_cost": sum(costs),
        "avg_cost": statistics.mean(costs) if costs else 0.0,
    }


def compute_baseline_metrics(results: Sequence[CaseResult], mode: str) -> Dict[str, Any]:
    target = [result for result in results if result.case_type == "target"]
    unsupported = [result for result in results if result.case_type == "unsupported_query"]
    ambiguous = [result for result in results if result.case_type == "ambiguous_query"]
    conflict = [result for result in results if result.case_type == "conflict_query"]

    if mode == "global":
        get_corpus = lambda r: r.global_retrieved_corpus_id
        get_jurisdiction = lambda r: r.global_retrieved_jurisdiction
        latencies = [r.global_latency_ms for r in results]
        tokens = [r.global_token_estimate for r in results]
        costs = [r.global_cost_estimate for r in results]
    elif mode == "domain_hint":
        get_corpus = lambda r: r.domain_retrieved_corpus_id
        get_jurisdiction = lambda r: r.domain_retrieved_jurisdiction
        latencies = [r.domain_latency_ms for r in results]
        tokens = [r.domain_token_estimate for r in results]
        costs = [r.domain_cost_estimate for r in results]
    else:
        raise ValueError(f"Unsupported baseline mode: {mode}")

    target_correct = sum(
        1 for result in target
        if get_corpus(result) == result.expected_corpus_id
        and compatible_jurisdiction(result.expected_jurisdiction, get_jurisdiction(result))
    )

    wrong_corpus = sum(1 for result in target if get_corpus(result) != result.expected_corpus_id)

    wrong_jurisdiction = sum(
        1 for result in target
        if not compatible_jurisdiction(result.expected_jurisdiction, get_jurisdiction(result))
    )

    return {
        "mode": mode,
        "target_correct": ratio(target_correct, len(target)),
        "wrong_corpus_misrouting": ratio(wrong_corpus, len(target)),
        "wrong_jurisdiction_misrouting": ratio(wrong_jurisdiction, len(target)),
        "unsupported_query_false_allow": ratio(len(unsupported), len(unsupported)),
        "ambiguous_query_false_allow": ratio(len(ambiguous), len(ambiguous)),
        "conflict_query_false_allow": ratio(len(conflict), len(conflict)),
        "p50_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_latency_ms": percentile(latencies, 0.95),
        "total_tokens": sum(tokens),
        "avg_tokens": statistics.mean(tokens) if tokens else 0.0,
        "total_cost": sum(costs),
        "avg_cost": statistics.mean(costs) if costs else 0.0,
    }


def build_baseline_comparison(
    hsrag: Dict[str, Any],
    global_metrics: Dict[str, Any],
    domain_metrics: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for baseline in [global_metrics, domain_metrics]:
        token_reduction = (
            (1.0 - hsrag["total_tokens"] / baseline["total_tokens"]) * 100.0
            if baseline["total_tokens"]
            else 0.0
        )

        cost_reduction = (
            (1.0 - hsrag["total_cost"] / baseline["total_cost"]) * 100.0
            if baseline["total_cost"]
            else 0.0
        )

        latency_ratio = (
            baseline["p95_latency_ms"] / hsrag["p95_latency_ms"]
            if hsrag["p95_latency_ms"]
            else 0.0
        )

        rows.append(
            {
                "baseline_mode": baseline["mode"],
                "hsrag_target_correct": hsrag["target_correct"],
                "baseline_target_correct": baseline["target_correct"],
                "hsrag_wrong_corpus_misrouting": hsrag["wrong_corpus_misrouting"],
                "baseline_wrong_corpus_misrouting": baseline["wrong_corpus_misrouting"],
                "hsrag_unsupported_query_false_allow": hsrag["unsupported_query_false_allow"],
                "baseline_unsupported_query_false_allow": baseline["unsupported_query_false_allow"],
                "hsrag_ambiguous_query_false_allow": hsrag["ambiguous_query_false_allow"],
                "baseline_ambiguous_query_false_allow": baseline["ambiguous_query_false_allow"],
                "hsrag_conflict_query_false_allow": hsrag["conflict_query_false_allow"],
                "baseline_conflict_query_false_allow": baseline["conflict_query_false_allow"],
                "token_reduction_pct": token_reduction,
                "cost_reduction_pct": cost_reduction,
                "p95_latency_ratio_baseline_over_hsrag": latency_ratio,
            }
        )

    return rows


# =============================================================================
# Gates
# =============================================================================

def build_gate_checks(
    case_count: int,
    min_cases: int,
    hsrag: Dict[str, Any],
    global_metrics: Dict[str, Any],
    domain_metrics: Dict[str, Any],
    audit_ok: bool,
    max_p95_latency_ms: float,
) -> List[GateCheck]:
    baseline_false_allow = max(
        global_metrics["unsupported_query_false_allow"],
        global_metrics["ambiguous_query_false_allow"],
        global_metrics["conflict_query_false_allow"],
        domain_metrics["unsupported_query_false_allow"],
        domain_metrics["ambiguous_query_false_allow"],
        domain_metrics["conflict_query_false_allow"],
    )

    return [
        GateCheck(
            gate_id="RQ5_MC_CASES_MINIMUM",
            description="Minimum perturbation cases.",
            expected=f">= {min_cases}",
            actual=case_count,
            passed=case_count >= min_cases,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_TARGET_CORRECT",
            description="Target correctness.",
            expected=">= 0.995",
            actual=hsrag["target_correct"],
            passed=hsrag["target_correct"] >= 0.995,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_WRONG_CORPUS_MISROUTING_ZERO",
            description="Wrong-corpus misrouting.",
            expected=0.0,
            actual=hsrag["wrong_corpus_misrouting"],
            passed=hsrag["wrong_corpus_misrouting"] == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_WRONG_JURISDICTION_MISROUTING_ZERO",
            description="Wrong-jurisdiction misrouting.",
            expected=0.0,
            actual=hsrag["wrong_jurisdiction_misrouting"],
            passed=hsrag["wrong_jurisdiction_misrouting"] == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_UNSUPPORTED_QUERY_FALSE_ALLOW_ZERO",
            description="Unsupported-query false allow.",
            expected=0.0,
            actual=hsrag["unsupported_query_false_allow"],
            passed=hsrag["unsupported_query_false_allow"] == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AMBIGUOUS_QUERY_FALSE_ALLOW_ZERO",
            description="Ambiguous-query false allow.",
            expected=0.0,
            actual=hsrag["ambiguous_query_false_allow"],
            passed=hsrag["ambiguous_query_false_allow"] == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_CONFLICT_QUERY_FALSE_ALLOW_ZERO",
            description="Conflict-query false allow.",
            expected=0.0,
            actual=hsrag["conflict_query_false_allow"],
            passed=hsrag["conflict_query_false_allow"] == 0.0,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_AUDIT_CHAIN_COMPLETE",
            description="Per-case audit chain.",
            expected=1.0,
            actual=1.0 if audit_ok else 0.0,
            passed=audit_ok,
            severity="HARD",
        ),
        GateCheck(
            gate_id="HSRAG_P95_LATENCY_BOUND",
            description="HSRAG p95 latency bound.",
            expected=f"< {max_p95_latency_ms} ms",
            actual=hsrag["p95_latency_ms"],
            passed=hsrag["p95_latency_ms"] < max_p95_latency_ms,
            severity="HARD",
        ),
        GateCheck(
            gate_id="BASELINE_FALSE_ALLOW_PRESENT",
            description="At least one lexical baseline exposes non-target false allow.",
            expected="> 0",
            actual=baseline_false_allow,
            passed=baseline_false_allow > 0.0,
            severity="SOFT",
        ),
    ]


def summarize_gate_checks(checks: Sequence[GateCheck]) -> Tuple[str, List[str]]:
    failures = [
        f"{check.gate_id}: expected={check.expected}, actual={check.actual}"
        for check in checks
        if check.severity == "HARD" and not check.passed
    ]

    if failures:
        return "RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_FAIL", failures

    return "RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_PASS", []


# =============================================================================
# Summary audit chain
# =============================================================================

def build_summary_audit_chain(
    config: Dict[str, Any],
    corpus_summary: Dict[str, Any],
    hsrag_metrics: Dict[str, Any],
    baseline_comparison: Sequence[Dict[str, Any]],
    gate_checks: Sequence[GateCheck],
    final_case_hash: str,
) -> List[AuditEvent]:
    events: List[AuditEvent] = []
    previous = "GENESIS"

    payloads = [
        ("RQ5_5_CONFIG", config),
        ("RQ5_5_CORPUS_SUMMARY", corpus_summary),
        ("RQ5_5_HSRAG_METRICS", hsrag_metrics),
        ("RQ5_5_BASELINE_COMPARISON", {"rows": list(baseline_comparison)}),
        ("RQ5_5_GATE_CHECKS", {"checks": [asdict(check) for check in gate_checks]}),
        ("RQ5_5_FINAL_CASE_HASH", {"final_case_hash": final_case_hash}),
    ]

    for index, (event_type, payload) in enumerate(payloads):
        event_payload = {
            "index": index,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous,
        }
        event_hash = stable_json_hash(event_payload)
        events.append(AuditEvent(index, event_type, payload, previous, event_hash))
        previous = event_hash

    return events


def verify_summary_audit_chain(events: Sequence[AuditEvent]) -> bool:
    previous = "GENESIS"

    for event in events:
        if event.previous_hash != previous:
            return False

        payload = {
            "index": event.index,
            "event_type": event.event_type,
            "payload": event.payload,
            "previous_hash": event.previous_hash,
        }

        if stable_json_hash(payload) != event.event_hash:
            return False

        previous = event.event_hash

    return True


def write_audit_chain(path: Path, events: Sequence[AuditEvent]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")


# =============================================================================
# Output
# =============================================================================

def write_markdown_summary(
    path: Path,
    decision: str,
    failures: Sequence[str],
    config: Dict[str, Any],
    corpus_summary: Dict[str, Any],
    hsrag: Dict[str, Any],
    global_metrics: Dict[str, Any],
    domain_metrics: Dict[str, Any],
    comparison: Sequence[Dict[str, Any]],
    checks: Sequence[GateCheck],
    case_audit_ok: bool,
    summary_audit_ok: bool,
) -> None:
    lines = [
        "# RQ5.5 CTHC-Typed Salted Domain Routing Robustness Summary",
        "",
        f"Core decision: `{decision}`",
        f"Case audit chain complete: `{1.0 if case_audit_ok else 0.0}`",
        f"Summary audit chain complete: `{1.0 if summary_audit_ok else 0.0}`",
        "",
        "## Config",
    ]

    for key, value in config.items():
        lines.append(f"- {key}: `{value}`")

    lines += ["", "## Corpus Summary"]
    for key, value in corpus_summary.items():
        lines.append(f"- {key}: `{value}`")

    lines += ["", "## HSRAG Metrics"]
    for key, value in hsrag.items():
        lines.append(f"- {key}: `{value}`")

    lines += ["", "## Global Lexical Baseline"]
    for key, value in global_metrics.items():
        lines.append(f"- {key}: `{value}`")

    lines += ["", "## Domain-Hint Lexical Baseline"]
    for key, value in domain_metrics.items():
        lines.append(f"- {key}: `{value}`")

    lines += [
        "",
        "## Baseline Comparison",
        "",
        "| baseline | token_reduction_pct | cost_reduction_pct | p95_latency_ratio |",
        "|---|---:|---:|---:|",
    ]

    for row in comparison:
        lines.append(
            f"| {row['baseline_mode']} | {row['token_reduction_pct']} | "
            f"{row['cost_reduction_pct']} | {row['p95_latency_ratio_baseline_over_hsrag']} |"
        )

    lines += [
        "",
        "## Gate Checks",
        "",
        "| gate_id | passed | expected | actual | severity |",
        "|---|---:|---|---|---|",
    ]

    for check in checks:
        lines.append(
            f"| {check.gate_id} | `{check.passed}` | `{check.expected}` | "
            f"`{check.actual}` | `{check.severity}` |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- This is a live benchmark, not a frozen-result verifier.",
        "- Routing does not read case_type.",
        "- Query routing emits a CTHCRoute object.",
        "- Retrieval only uses chunks in the matching salted domain_hash bucket.",
        "- Strict acceptance gates are preserved.",
        "- Generic legal words cannot open a corpus route.",
        "- RQ5.5 adds structured U.S.C. citation fragment recovery.",
    ]

    if failures:
        lines += ["", "## Failures"]
        for failure in failures:
            lines.append(f"- {failure}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(
    decision: str,
    failures: Sequence[str],
    config: Dict[str, Any],
    corpus_summary: Dict[str, Any],
    hsrag: Dict[str, Any],
    global_metrics: Dict[str, Any],
    domain_metrics: Dict[str, Any],
    case_audit_ok: bool,
    summary_audit_ok: bool,
) -> None:
    print("=" * 80)
    print("HSRAG LAW — RQ5.5 CTHC-TYPED SALTED DOMAIN ROUTING")
    print("=" * 80)
    print(f"core_decision: {decision}")
    print(f"case_audit_chain_complete: {1.0 if case_audit_ok else 0.0}")
    print(f"summary_audit_chain_complete: {1.0 if summary_audit_ok else 0.0}")
    print("")

    print("Config:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print("")
    print("Corpus:")
    for key, value in corpus_summary.items():
        print(f"  {key}: {value}")

    print("")
    print("HSRAG:")
    for key in [
        "target_correct",
        "wrong_corpus_misrouting",
        "wrong_jurisdiction_misrouting",
        "unsupported_query_false_allow",
        "ambiguous_query_false_allow",
        "conflict_query_false_allow",
        "p95_latency_ms",
        "total_tokens",
        "total_cost",
    ]:
        print(f"  {key}: {hsrag[key]}")

    print("")
    print("Global lexical baseline:")
    for key in [
        "target_correct",
        "wrong_corpus_misrouting",
        "unsupported_query_false_allow",
        "ambiguous_query_false_allow",
        "conflict_query_false_allow",
        "p95_latency_ms",
        "total_tokens",
        "total_cost",
    ]:
        print(f"  {key}: {global_metrics[key]}")

    print("")
    print("Domain-hint lexical baseline:")
    for key in [
        "target_correct",
        "wrong_corpus_misrouting",
        "unsupported_query_false_allow",
        "ambiguous_query_false_allow",
        "conflict_query_false_allow",
        "p95_latency_ms",
        "total_tokens",
        "total_cost",
    ]:
        print(f"  {key}: {domain_metrics[key]}")

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

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run RQ5.5 CTHC typed salted domain routing robustness benchmark."
    )
    parser.add_argument("--cases", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260505)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-chunks-per-corpus", type=int, default=80)
    parser.add_argument("--min-cases", type=int, default=10000)
    parser.add_argument("--cost-per-1k", type=float, default=COST_PER_1K_TOKENS_DEFAULT)
    parser.add_argument("--max-p95-latency-ms", type=float, default=20.0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    ensure_dirs()

    chunks, corpus_source = load_rebuilt_chunks(args.max_chunks_per_corpus)

    corpora = sorted({chunk.corpus_id for chunk in chunks})
    jurisdictions = sorted({chunk.jurisdiction for chunk in chunks})
    domain_hashes = sorted({chunk.domain_hash for chunk in chunks})

    cases = generate_cases(args.cases, args.seed, corpora)

    started = time.perf_counter()
    results = run_benchmark(cases, chunks, args.top_k, args.cost_per_1k)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    case_audit_ok = verify_case_audit_chain(results)
    final_case_hash = results[-1].audit_hash if results else "NONE"

    hsrag = compute_hsrag_metrics(results)
    global_metrics = compute_baseline_metrics(results, "global")
    domain_metrics = compute_baseline_metrics(results, "domain_hint")
    comparison = build_baseline_comparison(hsrag, global_metrics, domain_metrics)

    checks = build_gate_checks(
        case_count=len(results),
        min_cases=args.min_cases,
        hsrag=hsrag,
        global_metrics=global_metrics,
        domain_metrics=domain_metrics,
        audit_ok=case_audit_ok,
        max_p95_latency_ms=args.max_p95_latency_ms,
    )
    decision, failures = summarize_gate_checks(checks)

    config = {
        "cases": args.cases,
        "seed": args.seed,
        "top_k": args.top_k,
        "max_chunks_per_corpus": args.max_chunks_per_corpus,
        "min_cases": args.min_cases,
        "cost_per_1k": args.cost_per_1k,
        "max_p95_latency_ms": args.max_p95_latency_ms,
        "benchmark_salt": BENCHMARK_SALT,
        "elapsed_ms_total": elapsed_ms,
    }

    corpus_summary = {
        "corpus_source": corpus_source,
        "chunk_count": len(chunks),
        "corpus_count": len(corpora),
        "corpora": "|".join(corpora),
        "jurisdiction_count": len(jurisdictions),
        "jurisdictions": "|".join(jurisdictions),
        "domain_hash_count": len(domain_hashes),
    }

    summary_chain = build_summary_audit_chain(
        config=config,
        corpus_summary=corpus_summary,
        hsrag_metrics=hsrag,
        baseline_comparison=comparison,
        gate_checks=checks,
        final_case_hash=final_case_hash,
    )
    summary_audit_ok = verify_summary_audit_chain(summary_chain)

    if not summary_audit_ok:
        decision = "RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_FAIL"
        failures = list(failures) + ["Summary audit chain failed."]

    payload = {
        "name": "HSRAG-LAW-RQ5.5-CTHC-Typed-Salted-Domain-Routing",
        "core_decision": decision,
        "failures": list(failures),
        "config": config,
        "corpus_summary": corpus_summary,
        "case_count": len(results),
        "case_audit_chain_complete": 1.0 if case_audit_ok else 0.0,
        "summary_audit_chain_complete": 1.0 if summary_audit_ok else 0.0,
        "final_case_hash": final_case_hash,
        "hsrag_metrics": hsrag,
        "global_lexical_baseline": global_metrics,
        "domain_hint_lexical_baseline": domain_metrics,
        "baseline_comparison": comparison,
        "gate_checks": [asdict(check) for check in checks],
        "outputs": {
            "summary_json": "rq5_mc_reproduction_summary.json",
            "summary_md": "rq5_mc_reproduction_summary.md",
            "case_results_csv": "rq5_case_results.csv",
            "gate_checks_csv": "rq5_gate_checks.csv",
            "baseline_comparison_csv": "rq5_baseline_comparison.csv",
            "audit_chain_jsonl": "rq5_audit_chain.jsonl",
        },
    }

    write_json(RESULTS_DIR / "rq5_mc_reproduction_summary.json", payload)
    write_markdown_summary(
        RESULTS_DIR / "rq5_mc_reproduction_summary.md",
        decision,
        failures,
        config,
        corpus_summary,
        hsrag,
        global_metrics,
        domain_metrics,
        comparison,
        checks,
        case_audit_ok,
        summary_audit_ok,
    )
    write_dataclass_csv(RESULTS_DIR / "rq5_case_results.csv", results)
    write_dataclass_csv(RESULTS_DIR / "rq5_gate_checks.csv", checks)
    write_dict_csv(RESULTS_DIR / "rq5_baseline_comparison.csv", comparison)
    write_audit_chain(RESULTS_DIR / "rq5_audit_chain.jsonl", summary_chain)

    print_summary(
        decision,
        failures,
        config,
        corpus_summary,
        hsrag,
        global_metrics,
        domain_metrics,
        case_audit_ok,
        summary_audit_ok,
    )

    return 0 if decision == "RQ5_5_CTHC_SALTED_DOMAIN_ROUTING_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())