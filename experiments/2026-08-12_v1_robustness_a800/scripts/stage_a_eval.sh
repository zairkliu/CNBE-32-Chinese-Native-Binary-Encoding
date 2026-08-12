#!/usr/bin/env bash
set -euo pipefail

CODE="${CNBE_CODE:-/scnet_upload_package_MERGED_DCU/code}"
DCU="${CNBE_DCU:-/scnet_upload_package_DCU}"
MERGED="${CNBE_MERGED:-/scnet_upload_package_MERGED_DCU}"
V1_DATA="${CNBE_V1_DATA:-$MERGED/data}"
OUT="${CNBE_OUT:-$DCU/output}"
STAGE="$OUT/v1_robustness/stage_a"
mkdir -p "$STAGE"

find_ckpt() {
  local name=$1
  find /scnet_upload_package_DCU /scnet_upload_package_MERGED_DCU \
    -maxdepth 8 -path "*checkpoints/$name/final.pt" 2>/dev/null | head -n1
}

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
  if [ ! -f "$ckpt" ]; then
    echo "MISSING checkpoint $ckpt, skip $name"
    return 0
  fi
  echo "== eval $name =="
  python "$CODE/scripts/eval.py" \
    --checkpoint "$ckpt" \
    --config "$CODE/config/$config" \
    --cnbe-paths "$@" \
    --output "$STAGE/${name}_eval.json" \
    --prediction-hash-output "$STAGE/${name}_pred_hash.json"
}

MOE_CKPT="${CNBE_CKPT_MOE:-$(find_ckpt moe128)}"
eval_arm moe128 v1_moe128_dcu2.yaml "$MOE_CKPT" "${V1_FILES[@]}"

DENSE_CKPT="${CNBE_CKPT_DENSE:-$(find_ckpt dense)}"
eval_arm dense v1_dense_dcu2.yaml "$DENSE_CKPT" "${V1_FILES[@]}"

DENSE_MATCHED_CKPT="${CNBE_CKPT_DENSE_MATCHED:-$(find_ckpt dense_matched)}"
eval_arm dense_matched v1_dense_matched_dcu2.yaml "$DENSE_MATCHED_CKPT" "${V1_FILES[@]}"

UNI_DATA="$MERGED/output/data_unicode/unicode.u32"
UNI_CKPT="${CNBE_CKPT_UNICODE:-$(find_ckpt unicode)}"
if [ -f "$UNI_DATA" ]; then
  eval_arm unicode v1_unicode_dcu2.yaml "$UNI_CKPT" "$UNI_DATA"
else
  echo "MISSING unicode data $UNI_DATA, skip unicode"
fi

echo "stage A done: $STAGE"
