#!/usr/bin/env bash
set -euo pipefail

SEED="${1:-43}"
CODE="${CNBE_CODE:-/scnet_upload_package_MERGED_DCU/code}"
DCU="${CNBE_DCU:-/scnet_upload_package_DCU}"
V1_DATA="${CNBE_V1_DATA:-$DCU/data}"
OUT="${CNBE_OUT:-$DCU/output}"
STAGE="$OUT/v1_robustness/stage_b"
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

run_seed() {
  local arm=$1
  local config=$2
  local tag="${SEED}_${arm}"
  local ckpt="$STAGE/$tag"
  mkdir -p "$ckpt"
  echo "== train $tag =="
  CNBE_MAPPING_DIR="$STAGE/mappings_$tag" torchrun \
    --nproc_per_node=2 --standalone \
    "$CODE/scripts/train_distributed.py" \
    --config "$CODE/config/$config" \
    --seed "$SEED" \
    --cnbe-paths "${V1_FILES[@]}" \
    --output "$STAGE/${tag}_metrics.json" \
    --checkpoint-dir "$ckpt"

  echo "== eval $tag =="
  CNBE_MAPPING_DIR="$STAGE/mappings_$tag" python "$CODE/scripts/eval.py" \
    --checkpoint "$ckpt/final.pt" \
    --config "$CODE/config/$config" \
    --cnbe-paths "${V1_FILES[@]}" \
    --output "$STAGE/${tag}_eval.json" \
    --prediction-hash-output "$STAGE/${tag}_pred_hash.json"
}

run_seed moe128 v1_moe128_dcu2.yaml
run_seed dense_matched v1_dense_matched_dcu2.yaml

echo "stage B seed=$SEED done: $STAGE"
