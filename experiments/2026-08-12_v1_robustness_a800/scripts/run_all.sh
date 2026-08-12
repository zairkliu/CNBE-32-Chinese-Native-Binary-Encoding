#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE="${CNBE_CODE:-/scnet_upload_package_MERGED_DCU/code}"
DCU="${CNBE_DCU:-/scnet_upload_package_DCU}"
MERGED="${CNBE_MERGED:-/scnet_upload_package_MERGED_DCU}"

if [ -n "${CNBE_V1_DATA:-}" ]; then
  V1_DATA="$CNBE_V1_DATA"
else
  V1_DATA=""
  for d in "$MERGED/data" "$DCU/data" "$ROOT/data"; do
    if [ -f "$d/zzjh_294.cnbe" ]; then
      V1_DATA="$d"
      break
    fi
  done
fi
if [ -z "$V1_DATA" ]; then
  echo "v1 data not found; set CNBE_V1_DATA=/path/to/v1/data" >&2
  exit 2
fi

export CNBE_V1_DATA="$V1_DATA"
echo "v1 data: $V1_DATA"

mkdir -p "$DCU/output/v1_robustness"
cp -f "$ROOT/code/scripts/train_distributed.py" "$CODE/scripts/train_distributed.py"
cp -f "$ROOT/code/scripts/eval.py" "$CODE/scripts/eval.py"
mkdir -p "$CODE/config"
cp -f "$ROOT"/configs/v1_*.yaml "$CODE/config/"

python "$ROOT/tools_generate_v1_manifest.py" \
  --output "$DCU/output/v1_robustness/MANIFEST.json"

bash "$ROOT/scripts/stage_a_eval.sh"
bash "$ROOT/scripts/stage_b_multiseed.sh" "${1:-43}"

if [ "${RUN_SEED44:-0}" = "1" ]; then
  bash "$ROOT/scripts/stage_b_multiseed.sh" 44
fi

echo "== robustness pipeline done =="
echo "results: $DCU/output/v1_robustness"
