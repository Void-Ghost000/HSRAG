"""
HSRAG CTHC scope detection.

QSVCS scope:
- I / Intent:
  Detect stable legal corpus identifiers from a natural-language query.
- V / Validation:
  Do not use expected_corpus, expected_jurisdiction, case_type, or answer keys.
- O / Operation:
  Normalize query text, detect stable route openers, and detect fragmented
  U.S.C. citation patterns used in RQ5.5/RQ6.
- P / Postcondition:
  Return detected corpus ids only from query text.
- F / Feedback:
  Generic legal words alone must not open a route.
"""

from __future__ import annotations

import re
from typing import Iterable, List


ROUTE_OPENERS: dict[str, tuple[str, ...]] = {
    "EU_AI_ACT": (
        "eu ai act",
        "ai act",
        "artificial intelligence act",
        "regulation 2024 1689",
    ),
    "EU_DMA": (
        "digital markets act",
        "eu dma",
        "dma",
        "gatekeeper",
        "gatekeepers",
    ),
    "EU_GDPR": (
        "gdpr",
        "general data protection regulation",
    ),
    "US_COPPA": (
        "coppa",
        "children online privacy",
        "childrens online privacy",
        "children's online privacy",
    ),
    "US_CDA230": (
        "cda section 230",
        "section 230",
        "47 usc 230",
        "47 u s c 230",
        "platform liability",
        "interactive computer service",
    ),
    "US_FTC_ACT5": (
        "ftc act section 5",
        "ftc section 5",
        "federal trade commission act",
        "15 usc 45",
        "15 u s c 45",
        "unfair or deceptive",
    ),
    "US_CCPA": (
        "ccpa",
        "california consumer privacy act",
    ),
}


GENERIC_AMBIGUOUS_SIGNALS: tuple[str, ...] = (
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
)


UNSUPPORTED_TOPICS: tuple[str, ...] = (
    "pipeda",
    "canada pipeda",
    "lgpd",
    "brazil lgpd",
    "hipaa",
    "uk online safety act",
    "singapore pdpa",
    "india digital personal data protection act",
)


def normalize_text(text: str) -> str:
    """Normalize legal query text for CTHC route detection."""

    out = (text or "").lower()
    out = out.replace("u.s.c.", "usc")
    out = out.replace("u.s.", "us")
    out = out.replace("u.s", "us")
    out = out.replace("u s c", "usc")
    out = out.replace("children's", "childrens")

    typo_map = {
        "artcle": "article",
        "secton": "section",
        "oblgations": "obligations",
        "liablity": "liability",
    }
    for bad, good in typo_map.items():
        out = out.replace(bad, good)

    out = re.sub(r"[^a-z0-9]+", " ", out)
    return " ".join(out.split())


def tokenize(text: str) -> list[str]:
    """Tokenize normalized text."""

    return re.findall(r"[a-z0-9]+", normalize_text(text))


def token_set(text: str) -> set[str]:
    """Return normalized token set."""

    return set(tokenize(text))


def _edit_distance_leq_one(a: str, b: str) -> bool:
    """Return True if two tokens differ by at most one edit."""

    if a == b:
        return True

    if abs(len(a) - len(b)) > 1:
        return False

    if len(a) == len(b):
        diff = sum(1 for x, y in zip(a, b) if x != y)
        if diff <= 1:
            return True

        for i in range(len(a) - 1):
            if (
                a[i] == b[i + 1]
                and a[i + 1] == b[i]
                and a[:i] == b[:i]
                and a[i + 2 :] == b[i + 2 :]
            ):
                return True

        return False

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


def _token_match(alias_token: str, query_tokens: set[str]) -> bool:
    """Fuzzy token match used only for stable legal route openers."""

    if alias_token in query_tokens:
        return True

    if len(alias_token) < 4:
        return False

    for token in query_tokens:
        if len(token) >= 4 and _edit_distance_leq_one(alias_token, token):
            return True

    return False


def _opener_match(query_norm: str, query_tokens: set[str], opener: str) -> bool:
    """Return True if a stable route opener appears in the query."""

    opener_norm = normalize_text(opener)
    if not opener_norm:
        return False

    if f" {opener_norm} " in f" {query_norm} ":
        return True

    opener_tokens = opener_norm.split()
    if len(opener_tokens) == 1:
        return _token_match(opener_tokens[0], query_tokens)

    return all(_token_match(token, query_tokens) for token in opener_tokens)


def detect_us_code_fragment_routes(query: str) -> list[str]:
    """Detect fragmented U.S.C. citation route openers.

    Examples:
    - 47 U.S.C. 230 -> US_CDA230
    - 15 U.S.C. 45  -> US_FTC_ACT5
    """

    toks = token_set(query)
    hits: list[str] = []

    has_usc = "usc" in toks or {"u", "s", "c"}.issubset(toks)

    if has_usc and "47" in toks and "230" in toks:
        hits.append("US_CDA230")

    if has_usc and "15" in toks and "45" in toks:
        hits.append("US_FTC_ACT5")

    return hits


def detect_route_openers(query: str) -> list[str]:
    """Detect stable legal corpus ids from query text.

    This function does not inspect benchmark labels.
    """

    cleaned = re.sub(r"\[(?:pointer|source|chunk)[^\]]*\]", " ", query or "", flags=re.I)
    cleaned = re.sub(r"pointer\s*:\s*[a-z0-9_\-]+", " ", cleaned, flags=re.I)

    query_norm = normalize_text(cleaned)
    q_tokens = set(query_norm.split())

    matched: list[str] = []

    for corpus_id in detect_us_code_fragment_routes(query_norm):
        if corpus_id not in matched:
            matched.append(corpus_id)

    for corpus_id, openers in ROUTE_OPENERS.items():
        if corpus_id in matched:
            continue
        if any(_opener_match(query_norm, q_tokens, opener) for opener in openers):
            matched.append(corpus_id)

    return matched


def contains_unsupported_topic(query: str) -> bool:
    """Return True if the query asks for an explicitly unsupported topic."""

    q = normalize_text(query)
    return any(normalize_text(topic) in q for topic in UNSUPPORTED_TOPICS)


def generic_ambiguous_signal(query: str) -> bool:
    """Return True if query is generic legal wording without stable identifier."""

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


def conflict_query_signal(query: str, detected_corpus_ids: Iterable[str]) -> bool:
    """Detect cross-corpus conflict-form queries."""

    detected = list(detected_corpus_ids)
    q = normalize_text(query)
    toks = set(q.split())

    if len(detected) > 1:
        return True

    if re.search(r"\bunder\b.+\banswer using\b", q):
        return True

    has_using = "using" in toks or "use" in toks
    has_rules = "rules" in toks or "rule" in toks
    has_instead = "instead" in toks
    has_compare = "compare" in toks
    has_under = "under" in toks

    if detected and has_using and has_rules:
        return True

    if detected and has_instead:
        return True

    if detected and has_compare and has_under:
        return True

    return False