#!/usr/bin/env bash
set -euo pipefail

CODE="${CNBE_CODE:-/scnet_upload_package_MERGED_DCU/code}"
DCU="${CNBE_DCU:-/scnet_upload_package_DCU}"
MERGED="${CNBE_MERGED:-/scnet_upload_package_MERGED_DCU}"
V1_DATA="${CNBE_V1_DATA:-$MERGED/data}"
OUT="${CNBE_OUT:-$DCU/output}"
STAGE="$OUT/v1_robustness/stage_a"
mkdir -p "$STAGE"

V1_FILES=(
  "$V1_DATA/zzjh_294.cnbe"
  "$V1_DATA/luxun_18.cnbe"
  "$V1_DATA/agatha.cnbe"
  "$V1_DATA/csbook.cnbe"
  "$V1_DATA/jinyong.cnbe"
  "$V1_DATA/caixin.cnbe"
  "$V1_DATA/sushi.cnbe"
)

eval_arm() {
  local name=$1
  local config=$2
  local ckpt=$3
  shift 3
  echo "== eval $name =="
  python "$CODE/scripts/eval.py" \
    --checkpoint "$ckpt" \
    --config "$CODE/config/$config" \
    --cnbe-paths "$@" \
    --output "$STAGE/${name}_eval.json" \
    --prediction-hash-output "$STAGE/${name}_pred_hash.json"
}

eval_arm moe128 v1_moe128_dcu2.yaml \
  "$OUT/checkpoints/moe128/final.pt" "${V1_FILES[@]}"

eval_arm dense v1_dense_dcu2.yaml \
  "$OUT/checkpoints/dense/final.pt" "${V1_FILES[@]}"

eval_arm dense_matched v1_dense_matched_dcu2.yaml \
  "$OUT/checkpoints/dense_matched/final.pt" "${V1_FILES[@]}"

UNI_DATA="$MERGED/output/data_unicode/unicode.u32"
eval_arm unicode v1_unicode_dcu2.yaml \
  "$MERGED/output/checkpoints/unicode/final.pt" "$UNI_DATA"

echo "stage A done: $STAGE"
