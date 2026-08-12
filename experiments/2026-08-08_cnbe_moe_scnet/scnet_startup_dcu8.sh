#!/usr/bin/env bash
# SCNet CNBE-MoE startup for 113 group DCU BW 8 cards.
# Resource: 异构加速卡BW 64GB x 8, DTK 26.04, Central China Zone A.
# Default mounts: code -> /app, data -> /data/cnbe, output -> /output.
set -euo pipefail

ROOT="${CNBE_MOE_ROOT:-/app}"
DATA="${CNBE_DATA_DIR:-/data/cnbe}"
OUT="${CNBE_OUTPUT_DIR:-/output}"
MAPPING="${CNBE_MAPPING_DIR:-${OUT}/mappings}"
CONFIG="${CNBE_MOE_CONFIG:-scnet_moe_config_dcu8.yaml}"

SMOKE_ONLY=0
TRAIN_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --smoke-only) SMOKE_ONLY=1 ;;
    --train-only) TRAIN_ONLY=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

find_package() {
  for base in /root /root/private_data /root/group_data /root/public_data; do
    [ -d "$base" ] || continue
    found=$(find "$base" -maxdepth 4 -type d \( -name "scnet_upload_package_DCU" -o -name "scnet_upload_package" \) 2>/dev/null | head -n1)
    if [ -n "$found" ] && [ -f "$found/code/scripts/train_scnet.py" ]; then
      echo "$found"
      return 0
    fi
  done
  return 1
}

if [ ! -d "$ROOT/scripts" ]; then
  PKG=$(find_package || true)
  if [ -n "$PKG" ]; then
    ROOT="$PKG/code"
    DATA="${CNBE_DATA_DIR:-$PKG/data}"
    OUT="${CNBE_OUTPUT_DIR:-$PKG/output}"
    MAPPING="${CNBE_MAPPING_DIR:-${OUT}/mappings}"
  fi
fi

[ -f "$ROOT/scripts/train_scnet.py" ] || { echo "code not found at $ROOT" >&2; exit 1; }
[ -f "$ROOT/scripts/train_distributed.py" ] || { echo "train_distributed.py missing" >&2; exit 1; }
[ -f "$ROOT/config/$CONFIG" ] || { echo "config missing: $CONFIG" >&2; exit 1; }
[ -f "$DATA/zzjh_294.cnbe" ] || { echo "data not found at $DATA" >&2; exit 1; }

echo "== CNBE-MoE SCNet startup (DCU BW 8 cards) =="
echo "root=$ROOT"
echo "data=$DATA"
echo "out=$OUT"
echo "config=$CONFIG"
python - <<'PY'
import os
import platform
import sys
import torch

print("python:", sys.version.split()[0])
print("platform:", platform.platform())
print("torch:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
print("cuda_device_count:", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print("device", i, torch.cuda.get_device_name(i), props.total_memory // (1024**3), "GB")
print("HIP_VISIBLE_DEVICES:", os.environ.get("HIP_VISIBLE_DEVICES"))
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
PY

detect_nproc() {
  if [ -n "${NPROC_PER_NODE:-}" ]; then
    echo "$NPROC_PER_NODE"
    return
  fi
  COUNT=$(python -c "import torch; print(torch.cuda.device_count())" 2>/dev/null || echo 0)
  if [ "$COUNT" -gt 0 ]; then
    echo "$COUNT"
    return
  fi
  if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
    printf '%s' "$CUDA_VISIBLE_DEVICES" | tr ',' '\n' | wc -l
    return
  fi
  if [ -n "${HIP_VISIBLE_DEVICES:-}" ]; then
    printf '%s' "$HIP_VISIBLE_DEVICES" | tr ',' '\n' | wc -l
    return
  fi
  echo 8
}

echo "== smoke =="
mkdir -p "$OUT"
CNBE_MAPPING_DIR="$MAPPING" python "$ROOT/scripts/train_scnet.py" \
  --smoke \
  --config "$ROOT/config/$CONFIG" \
  --cnbe-paths "$DATA/zzjh_294.cnbe" \
  --output "$OUT/smoke_metrics.json"
echo "smoke metrics: $OUT/smoke_metrics.json"

if [ "$SMOKE_ONLY" -eq 1 ]; then
  exit 0
fi

echo "== training =="
mkdir -p "$OUT/checkpoints" "$MAPPING"
NPROC=$(detect_nproc)
NNODES="${NNODES:-${WORLD_SIZE:-1}}"
NODE_RANK="${NODE_RANK:-${RANK:-0}}"
ARGS=(--nproc_per_node="$NPROC")
if [ -n "${MASTER_ADDR:-}" ]; then
  ARGS+=(--nnodes="$NNODES" --node_rank="$NODE_RANK" \
    --master_addr="$MASTER_ADDR" --master_port="${MASTER_PORT:-29500}")
else
  ARGS+=(--standalone)
fi
echo "nproc_per_node=$NPROC nnodes=$NNODES node_rank=$NODE_RANK"
CNBE_MAPPING_DIR="$MAPPING" torchrun "${ARGS[@]}" \
  "$ROOT/scripts/train_distributed.py" \
  --config "$ROOT/config/$CONFIG" \
  --cnbe-paths "$DATA"/*.cnbe \
  --output "$OUT/train_metrics.json" \
  --checkpoint-dir "$OUT/checkpoints"
