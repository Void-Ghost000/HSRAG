#!/usr/bin/env bash
# HSRAG LAW RQ6 — Full Demo Alias
# Backward-compatible alias for the stress demo.
#
# Usage:
#   bash examples/hsrag_law/rq6/run_rq6_full.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/run_rq6_stress.sh"
