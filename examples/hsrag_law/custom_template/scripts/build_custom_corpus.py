"""
HSRAG LAW Custom Template — build_custom_corpus.py

Placeholder scaffold.

Next step:
- read manifest.example.json
- read input/legal_texts/*.txt
- normalize text
- split into chunks
- assign CTHC typed addresses
- generate salted domain hashes
- write output/custom_chunks.csv
- write output/custom_manifest.json
- write output/custom_audit_chain.jsonl
"""

from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE / "input"
OUTPUT_DIR = BASE / "output"

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("HSRAG LAW custom corpus builder scaffold is ready.")
    print(f"input_dir: {INPUT_DIR}")
    print(f"output_dir: {OUTPUT_DIR}")
    print("Implementation will be added in the next step.")

if __name__ == "__main__":
    main()
