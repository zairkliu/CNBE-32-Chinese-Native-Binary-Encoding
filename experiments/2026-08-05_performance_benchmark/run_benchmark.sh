#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
REPO="$(cd ../.. && pwd)"

python3 -m pip show cnbe32 >/dev/null 2>&1 || true
export PYTHONPATH="$REPO/src"
python3 bench_cnbe32.py --db "$REPO/data/cnbe32.db" --out results.json
