#!/usr/bin/env bash
# Resume the interrupted CNBE-MoE training from last.pt, then evaluate final.pt.
set -euo pipefail

ROOT="${CNBE_MOE_ROOT:-/scnet_upload_package_MERGED_DCU/code}"
DATA="${CNBE_DATA_DIR:-/scnet_upload_package_MERGED_DCU/data}"
OUT="${CNBE_OUTPUT_DIR:-/scnet_upload_package_MERGED_DCU/output}"
MAPPING="${CNBE_MAPPING_DIR:-${OUT}/mappings}"
CONFIG="${CNBE_MOE_CONFIG:-scnet_moe_config_merged_dcu2.yaml}"
NPROC="${NPROC_PER_NODE:-2}"

[ -f "$ROOT/scripts/train_distributed.py" ] || { echo "train_distributed.py missing" >&2; exit 1; }
[ -f "$ROOT/scripts/eval.py" ] || { echo "eval.py missing" >&2; exit 1; }
[ -f "$ROOT/config/$CONFIG" ] || { echo "config missing: $ROOT/config/$CONFIG" >&2; exit 1; }
[ -f "$OUT/checkpoints/last.pt" ] || { echo "last.pt missing" >&2; exit 1; }
mkdir -p "$MAPPING" "$OUT/checkpoints"

echo "== resume training from last.pt =="
CNBE_MAPPING_DIR="$MAPPING" torchrun \
  --nproc_per_node="$NPROC" --standalone \
  "$ROOT/scripts/train_distributed.py" \
  --config "$ROOT/config/$CONFIG" \
  --cnbe-paths "$DATA"/*.cnbe \
  --output "$OUT/train_metrics.json" \
  --checkpoint-dir "$OUT/checkpoints" \
  --resume

if [ "${SKIP_EVAL:-0}" = "1" ]; then
  echo "training resumed and completed; skipping eval"
  exit 0
fi

LIMIT_ARGS=()
if [ -n "${LIMIT_BATCHES:-}" ]; then
  LIMIT_ARGS+=(--limit-batches "$LIMIT_BATCHES")
fi

VOCAB_ARGS=()
if [ -n "${VOCAB_PATH:-}" ]; then
  VOCAB_ARGS+=(--vocab "$VOCAB_PATH")
fi

echo "== eval final.pt =="
CNBE_MAPPING_DIR="$MAPPING" python "$ROOT/scripts/eval.py" \
  --checkpoint "$OUT/checkpoints/final.pt" \
  --config "$ROOT/config/$CONFIG" \
  --cnbe-paths "$DATA"/*.cnbe \
  --output "$OUT/eval_metrics.json" \
  "${VOCAB_ARGS[@]}" \
  "${LIMIT_ARGS[@]}"

echo "train metrics: $OUT/train_metrics.json"
echo "eval metrics: $OUT/eval_metrics.json"
