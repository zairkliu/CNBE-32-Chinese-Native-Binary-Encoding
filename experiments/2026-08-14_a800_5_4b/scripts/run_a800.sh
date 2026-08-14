#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FROZEN="${CNBE_FROZEN:-/scnet_upload_package_CORPUS_V2_FROZEN}"
CODE="${CNBE_CODE:-$FROZEN/code}"
OUT="${CNBE_OUT:-/output/run_2026-08-14}"
mkdir -p "$OUT/checkpoints"

RESUME_ARGS=()
if [ "${RESUME:-0}" = "1" ]; then
  RESUME_ARGS=(--resume)
fi

echo "frozen: $FROZEN"
echo "code: $CODE"
echo "output: $OUT"

torchrun \
  --nproc_per_node=2 --standalone \
  "$CODE/scripts/train_distributed.py" \
  --config "$ROOT/configs/v2_moe128_a800.yaml" \
  --cnbe-paths "$FROZEN/data/train.cnbe" "$FROZEN/data/eval.cnbe" \
  --vocab-path "$FROZEN/assets/vocab.json" \
  --mapping-path "$FROZEN/assets/mapping_128.json" \
  --output "$OUT/train_metrics.json" \
  --checkpoint-dir "$OUT/checkpoints" \
  --step-metrics "$OUT/step_metrics.jsonl" \
  "${RESUME_ARGS[@]}" 2>&1 | tee "$OUT/training.log"

echo "== eval final =="
python "$CODE/scripts/eval.py" \
  --checkpoint "$OUT/checkpoints/final.pt" \
  --config "$ROOT/configs/v2_eval_a800.yaml" \
  --cnbe-paths "$FROZEN/data/eval.cnbe" \
  --vocab "$FROZEN/assets/vocab.json" \
  --mapping "$FROZEN/assets/mapping_128.json" \
  --output "$OUT/eval_metrics.json" \
  --prediction-hash-output "$OUT/eval_pred_hash.json"

echo "== done =="
echo "metrics: $OUT/train_metrics.json"
echo "step metrics: $OUT/step_metrics.jsonl"
echo "eval: $OUT/eval_metrics.json"
