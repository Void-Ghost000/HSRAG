from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

LOCAL_ONLY = True
ZERO_NETWORK = True
ZERO_SECRET = True
DETERMINISTIC = True

DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.5
DEFAULT_DIM = 512


def load_vector_module() -> Any:
    script_path = Path(__file__).resolve().parent / "local_hash_vector.py"
    spec = importlib.util.spec_from_file_location("local_hash_vector", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("LOCAL_HASH_VECTOR_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def lexical_score(query: str, document: str) -> float:
    q = Counter(tokenize(query))
    d = Counter(tokenize(document))

    if not q or not d:
        return 0.0

    dot = sum(q[token] * d.get(token, 0) for token in q)
    q_norm = math.sqrt(sum(value * value for value in q.values()))
    d_norm = math.sqrt(sum(value * value for value in d.values()))

    if q_norm == 0.0 or d_norm == 0.0:
        return 0.0

    return dot / (q_norm * d_norm)


def vector_score(query: str, document: str, dim: int = DEFAULT_DIM) -> float:
    vector_module = load_vector_module()
    qv = vector_module.vectorize_text(query, dim)
    dv = vector_module.vectorize_text(document, dim)
    return float(vector_module.cosine_similarity(qv, dv))


def hybrid_score(
    query: str,
    document: str,
    *,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    dim: int = DEFAULT_DIM,
) -> dict[str, float]:
    if alpha < 0 or beta < 0 or (alpha == 0 and beta == 0):
        raise ValueError("INVALID_HYBRID_WEIGHTS")

    lexical = lexical_score(query, document)
    vector = vector_score(query, document, dim)
    total = alpha + beta
    score = ((alpha * lexical) + (beta * vector)) / total

    return {
        "hybrid_score": round(score, 12),
        "lexical_score": round(lexical, 12),
        "vector_score": round(vector, 12),
        "alpha": float(alpha),
        "beta": float(beta),
    }


def rank_documents(
    query: str,
    documents: list[dict[str, Any]],
    *,
    top_k: int = 10,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    dim: int = DEFAULT_DIM,
) -> list[dict[str, Any]]:
    if top_k <= 0:
        raise ValueError("INVALID_TOP_K")

    ranked = []

    for index, document in enumerate(documents):
        text = str(document.get("text", ""))
        scores = hybrid_score(query, text, alpha=alpha, beta=beta, dim=dim)

        ranked.append(
            {
                "rank_input_index": index,
                "score": scores["hybrid_score"],
                "lexical_score": scores["lexical_score"],
                "vector_score": scores["vector_score"],
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
    args = parser.parse_args()

    registry_path = Path(args.registry)
    if not registry_path.exists():
        raise SystemExit(f"REGISTRY_NOT_FOUND:{registry_path}")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    results = rank_documents(args.query, registry.get("chunks", []), top_k=args.top_k)

    print(
        json.dumps(
            {
                "status": "OK",
                "local_only": LOCAL_ONLY,
                "zero_network": ZERO_NETWORK,
                "zero_secret": ZERO_SECRET,
                "deterministic": DETERMINISTIC,
                "result_count": len(results),
                "results": results,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
