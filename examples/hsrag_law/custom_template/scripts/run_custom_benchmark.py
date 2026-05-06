"""
HSRAG LAW Custom Template — run_custom_benchmark.py

Placeholder scaffold.

Next step:
- load output/custom_chunks.csv
- generate supported / unsupported / ambiguous test queries
- route by CTHC + salted domain hash
- apply evidence gate
- write benchmark summary and audit chain
"""

from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE / "output"

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("HSRAG LAW custom benchmark scaffold is ready.")
    print(f"output_dir: {OUTPUT_DIR}")
    print("Implementation will be added in the next step.")

if __name__ == "__main__":
    main()
