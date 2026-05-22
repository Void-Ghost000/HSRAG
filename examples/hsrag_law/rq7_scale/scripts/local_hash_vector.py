from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

DEFAULT_DIM = 512

LOCAL_ONLY = True
ZERO_NETWORK = True
ZERO_SECRET = True
DETERMINISTIC = True


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def stable_bucket(token: str, dim: int = DEFAULT_DIM) -> int:
    if dim <= 0:
        raise ValueError("INVALID_VECTOR_DIM")

    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % dim


def vectorize_text(text: str, dim: int = DEFAULT_DIM) -> dict[int, float]:
    counts: dict[int, float] = {}

    for token in tokenize(text):
        bucket = stable_bucket(token, dim)
        counts[bucket] = counts.get(bucket, 0.0) + 1.0

    return counts


def l2_norm(vector: dict[int, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))


def cosine_similarity(a: dict[int, float], b: dict[int, float]) -> float:
    if not a or not b:
        return 0.0

    if len(a) > len(b):
        a, b = b, a

    dot = sum(value * b.get(index, 0.0) for index, value in a.items())
    denom = l2_norm(a) * l2_norm(b)

    if denom == 0.0:
        return 0.0

    return dot / denom


def rank_documents(
    query: str,
    documents: list[dict[str, Any]],
    *,
    text_key: str = "text",
    top_k: int = 10,
    dim: int = DEFAULT_DIM,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("INVALID_TOP_K")

    query_vector = vectorize_text(query, dim)

    ranked: list[dict[str, Any]] = []

    for index, document in enumerate(documents):
        text = str(document.get(text_key, ""))
        doc_vector = vectorize_text(text, dim)
        score = cosine_similarity(query_vector, doc_vector)

        ranked.append(
            {
                "rank_input_index": index,
                "score": round(score, 12),
                "document": document,
            }
        )

    ranked.sort(
        key=lambda item: (
            -float(item["score"]),
            str(item["document"].get("cthc_address", "")),
            str(item["document"].get("chunk_id", "")),
            int(item["rank_input_index"]),
        )
    )

    return ranked[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--dim", type=int, default=DEFAULT_DIM)
    args = parser.parse_args()

    registry_path = Path(args.registry)

    if not registry_path.exists():
        raise SystemExit(f"REGISTRY_NOT_FOUND:{registry_path}")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    documents = registry.get("chunks", [])

    ranked = rank_documents(
        args.query,
        documents,
        top_k=args.top_k,
        dim=args.dim,
    )

    print(
        json.dumps(
            {
                "status": "OK",
                "local_only": LOCAL_ONLY,
                "zero_network": ZERO_NETWORK,
                "zero_secret": ZERO_SECRET,
                "deterministic": DETERMINISTIC,
                "top_k": args.top_k,
                "dim": args.dim,
                "result_count": len(ranked),
                "results": ranked,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
