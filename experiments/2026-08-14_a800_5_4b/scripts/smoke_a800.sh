#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FROZEN="${CNBE_FROZEN:-/scnet_upload_package_CORPUS_V2_FROZEN}"
CODE="${CNBE_CODE:-$FROZEN/code}"
OUT="${CNBE_OUT:-/output/smoke_2026-08-14}"
mkdir -p "$OUT/checkpoints"

echo "== smoke 100 steps =="
torchrun \
  --nproc_per_node=2 --standalone \
  "$CODE/scripts/train_distributed.py" \
  --config "$ROOT/configs/v2_moe128_a800_smoke.yaml" \
  --cnbe-paths "$FROZEN/data/train.cnbe" \
  --vocab-path "$FROZEN/assets/vocab.json" \
  --mapping-path "$FROZEN/assets/mapping_128.json" \
  --output "$OUT/smoke_metrics.json" \
  --checkpoint-dir "$OUT/checkpoints" \
  --step-metrics "$OUT/step_metrics.jsonl" \
  --max-steps 100 2>&1 | tee "$OUT/smoke.log"

echo "== resume test 10 steps =="
torchrun \
  --nproc_per_node=2 --standalone \
  "$CODE/scripts/train_distributed.py" \
  --config "$ROOT/configs/v2_moe128_a800_smoke.yaml" \
  --cnbe-paths "$FROZEN/data/train.cnbe" \
  --vocab-path "$FROZEN/assets/vocab.json" \
  --mapping-path "$FROZEN/assets/mapping_128.json" \
  --output "$OUT/resume_metrics.json" \
  --checkpoint-dir "$OUT/checkpoints" \
  --step-metrics "$OUT/resume_step_metrics.jsonl" \
  --max-steps 110 \
  --resume 2>&1 | tee "$OUT/resume.log"

echo "== smoke done =="
echo "loss curve: $OUT/step_metrics.jsonl"
echo "checkpoints: $OUT/checkpoints"
