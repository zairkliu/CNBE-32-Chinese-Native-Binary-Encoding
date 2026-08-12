#!/usr/bin/env bash
# Evaluate the latest CNBE-MoE checkpoint with the single-GPU eval script.
set -euo pipefail

ROOT="${CNBE_MOE_ROOT:-/scnet_upload_package_MERGED_DCU/code}"
DATA="${CNBE_DATA_DIR:-/scnet_upload_package_MERGED_DCU/data}"
OUT="${CNBE_OUTPUT_DIR:-/scnet_upload_package_MERGED_DCU/output}"
MAPPING="${CNBE_MAPPING_DIR:-${OUT}/mappings}"
CONFIG="${CNBE_MOE_CONFIG:-scnet_moe_config_merged_dcu2.yaml}"
CKPT="${CKPT:-${OUT}/checkpoints/last.pt}"

[ -f "$ROOT/scripts/eval.py" ] || { echo "eval.py missing at $ROOT/scripts/eval.py" >&2; exit 1; }
[ -f "$ROOT/config/$CONFIG" ] || { echo "config missing: $ROOT/config/$CONFIG" >&2; exit 1; }
[ -f "$CKPT" ] || { echo "checkpoint missing: $CKPT" >&2; exit 1; }
mkdir -p "$MAPPING" "$OUT"

LIMIT_ARGS=()
if [ -n "${LIMIT_BATCHES:-}" ]; then
  LIMIT_ARGS+=(--limit-batches "$LIMIT_BATCHES")
fi

VOCAB_ARGS=()
if [ -n "${VOCAB_PATH:-}" ]; then
  VOCAB_ARGS+=(--vocab "$VOCAB_PATH")
fi

CNBE_MAPPING_DIR="$MAPPING" python "$ROOT/scripts/eval.py" \
  --checkpoint "$CKPT" \
  --config "$ROOT/config/$CONFIG" \
  --cnbe-paths "$DATA"/*.cnbe \
  --output "$OUT/eval_metrics.json" \
  "${VOCAB_ARGS[@]}" \
  "${LIMIT_ARGS[@]}"

echo "eval metrics: $OUT/eval_metrics.json"
