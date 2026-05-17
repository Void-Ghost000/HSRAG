#!/usr/bin/env bash
# HSRAG LAW RQ6 — Standard Demo
# MC = 3000
#
# Usage from repo root:
#   bash examples/hsrag_law/rq6/run_rq6_standard.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

MC=3000
CHUNKS="examples/hsrag_law/results/rq4_rebuilt_chunks.csv"
RUNNER="examples/hsrag_law/rq6/run_rq6_conversational_collision.py"

if [[ ! -f "$RUNNER" ]]; then
  echo "ERROR: Cannot find RQ6 runner: $RUNNER" >&2
  exit 1
fi

if [[ ! -f "$CHUNKS" ]]; then
  echo "ERROR: Cannot find chunks file: $CHUNKS" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
else
  PYTHON_BIN="${PYTHON_BIN:-python}"
fi

mkdir -p logs

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="logs/rq6_standard_mc3000_${STAMP}.log"

echo "============================================================"
echo "HSRAG LAW RQ6 Standard Demo"
echo "MC: $MC"
echo "Expected rows: 108000"
echo "Chunks: $CHUNKS"
echo "Log: $LOG_FILE"
echo "============================================================"

"$PYTHON_BIN" "$RUNNER" --chunks "$CHUNKS" --mc "$MC" 2>&1 | tee "$LOG_FILE"

LATEST_RUN="$(ls -td runs/rq6_conversational_collision_* | head -n 1)"

echo ""
echo "Latest run:"
echo "$LATEST_RUN"

MODE_COMPARISON="$LATEST_RUN/rq6_mode_comparison.md"

if [[ -f "$MODE_COMPARISON" ]]; then
  echo ""
  echo "============================================================"
  echo "RQ6 Mode Comparison"
  echo "============================================================"
  cat "$MODE_COMPARISON"
else
  echo "WARNING: Mode comparison file not found: $MODE_COMPARISON" >&2
fi