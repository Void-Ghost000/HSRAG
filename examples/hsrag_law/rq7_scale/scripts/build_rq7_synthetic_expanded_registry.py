from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_rq4_builder() -> Any:
    script_path = Path(__file__).resolve().parent / "build_chunk_registry_from_rq4_rebuilt.py"
    spec = importlib.util.spec_from_file_location("rq4_rebuilt_builder", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("RQ4_BUILDER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def mark_real_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    output = dict(chunk)
    output["synthetic_expansion"] = False
    output["synthetic_source_chunk_id"] = None
    output["synthetic_variant_index"] = 0
    output["synthetic_generation_rule"] = None
    return output


def make_synthetic_chunk(source: dict[str, Any], variant_index: int) -> dict[str, Any]:
    chunk_id = f"{source['chunk_id']}_SYN_{variant_index:04d}"

    text = (
        str(source["text"])
        + "\n\n[SYNTHETIC_SCALE_EXPANSION: "
        + f"source_chunk_id={source['chunk_id']}; "
        + f"variant_index={variant_index}; "
        + "not_additional_legal_evidence=true]"
    )

    output = dict(source)
    output["chunk_id"] = chunk_id
    output["cthc_address"] = (
        f"cthc://LAW/{source['jurisdiction']}/{source['corpus']}/{source['unit']}/{chunk_id}"
    )
    output["source_hash"] = sha256_text(text)
    output["source_type"] = "SYNTHETIC_SCALE_EXPANSION"
    output["official_source"] = False
    output["text"] = text
    output["synthetic_expansion"] = True
    output["synthetic_source_chunk_id"] = source["chunk_id"]
    output["synthetic_variant_index"] = variant_index
    output["synthetic_generation_rule"] = "DETERMINISTIC_RQ4_CHUNK_COPY_WITH_EXPLICIT_MARKER"
    return output


def build_synthetic_registry(rq4_csv: Path, target_size: int) -> dict[str, Any]:
    builder = load_rq4_builder()
    base_registry = builder.build_registry(rq4_csv)

    real_chunks = [mark_real_chunk(chunk) for chunk in base_registry["chunks"]]
    real_count = len(real_chunks)

    if target_size < real_count:
        raise ValueError(f"TARGET_SIZE_BELOW_REAL_COUNT:{target_size}<{real_count}")

    expanded = list(real_chunks)

    synthetic_needed = target_size - real_count
    for synthetic_index in range(synthetic_needed):
        source = real_chunks[synthetic_index % real_count]
        variant_index = (synthetic_index // real_count) + 1
        expanded.append(make_synthetic_chunk(source, variant_index))

    return {
        "schema": "HSRAG_RQ7_CHUNK_REGISTRY_V0_1",
        "registry_variant": "SYNTHETIC_EXPANDED_REGISTRY_V0_1",
        "description": "Synthetic scale expansion built from RQ4 rebuilt chunks. Synthetic chunks are explicitly marked and are not additional legal evidence.",
        "generator": "build_rq7_synthetic_expanded_registry.py",
        "local_only": True,
        "source_registry_schema": base_registry.get("schema"),
        "source_artifact": str(rq4_csv.as_posix()),
        "source_artifact_hash": base_registry.get("source_artifact_hash"),
        "target_size": target_size,
        "chunk_count": len(expanded),
        "real_chunk_count": real_count,
        "synthetic_chunk_count": synthetic_needed,
        "chunks": expanded,
        "claim_boundary": {
            "synthetic_expansion": True,
            "synthetic_chunks_explicitly_labeled": True,
            "synthetic_expansion_is_not_new_legal_corpus": True,
            "scale_stress_only": True,
            "full_scale_real_corpus_benchmark": False,
            "legal_advice": False
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq4-csv", default="examples/hsrag_law/results/rq4_rebuilt_chunks.csv")
    parser.add_argument("--target-size", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rq4_csv = Path(args.rq4_csv)

    if not rq4_csv.exists():
        raise SystemExit(f"RQ4_REBUILT_CSV_NOT_FOUND:{rq4_csv}")

    registry = build_synthetic_registry(rq4_csv, args.target_size)
    output_path = Path(args.output)
    write_json(output_path, registry)

    print(
        json.dumps(
            {
                "status": "OK",
                "output": str(output_path),
                "target_size": registry["target_size"],
                "chunk_count": registry["chunk_count"],
                "real_chunk_count": registry["real_chunk_count"],
                "synthetic_chunk_count": registry["synthetic_chunk_count"],
                "synthetic_expansion": True,
                "synthetic_chunks_explicitly_labeled": True,
                "scale_stress_only": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
