#!/usr/bin/env bash
# Run v1 controlled comparison on DCU2: MoE-128 / Dense / Unicode Dense.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE="$ROOT/code"
OUT="${CNBE_OUTPUT_DIR:-$ROOT/output}"
NPROC="${NPROC_PER_NODE:-2}"

find_v1_data() {
  for d in \
    "${CNBE_V1_DATA_DIR:-}" \
    "$ROOT/data" \
    "$PWD/data" \
    /scnet_upload_package_MERGED_DCU/data \
    /scnet_upload_package_DCU/data \
    /scnet_upload_package/data; do
    if [ -n "$d" ] && [ -f "$d/zzjh_294.cnbe" ] && [ -f "$d/sushi.cnbe" ]; then
      echo "$d"
      return 0
    fi
  done
  return 1
}

V1_DATA="$(find_v1_data || true)"
if [ -z "$V1_DATA" ]; then
  echo "v1 data not found; set CNBE_V1_DATA_DIR=/path/to/v1/data" >&2
  exit 2
fi
TEXT_DIR="${CNBE_V1_TEXT_DIR:-$(dirname "$V1_DATA")/data_src}"
if ! compgen -G "$TEXT_DIR"/*.chars.txt > /dev/null; then
  echo "chars.txt not found in $TEXT_DIR" >&2
  exit 2
fi

V1_FILES=(
  "$V1_DATA/zzjh_294.cnbe"
  "$V1_DATA/luxun_18.cnbe"
  "$V1_DATA/agatha.cnbe"
  "$V1_DATA/csbook.cnbe"
  "$V1_DATA/jinyong.cnbe"
  "$V1_DATA/caixin.cnbe"
  "$V1_DATA/sushi.cnbe"
)
for f in "${V1_FILES[@]}"; do
  [ -f "$f" ] || { echo "missing v1 file: $f" >&2; exit 2; }
done

mkdir -p "$OUT" "$OUT/data_unicode"
echo "v1 data: $V1_DATA"
echo "text dir: $TEXT_DIR"
echo "output: $OUT"
echo "v1 files: ${#V1_FILES[@]}"

if [ ! -f "$OUT/data_unicode/unicode.u32" ]; then
  echo "== build unicode dataset =="
  python "$CODE/scripts/build_unicode_dataset.py" \
    --chars-paths "$TEXT_DIR"/*.chars.txt \
    --output-dir "$OUT/data_unicode" \
    --max-chars 25200000
fi

run_arm() {
  local name=$1
  local config=$2
  shift 2
  local ckpt="$OUT/checkpoints/$name"
  local mapping="$OUT/mappings/$name"
  mkdir -p "$ckpt" "$mapping"
  echo "== train $name =="
  CNBE_MAPPING_DIR="$mapping" torchrun \
    --nproc_per_node="$NPROC" --standalone \
    "$CODE/scripts/train_distributed.py" \
    --config "$CODE/config/$config" \
    --cnbe-paths "$@" \
    --output "$OUT/${name}_metrics.json" \
    --checkpoint-dir "$ckpt"
}

eval_arm() {
  local name=$1
  local config=$2
  shift 2
  local mapping="$OUT/mappings/$name"
  echo "== eval $name =="
  CNBE_MAPPING_DIR="$mapping" python "$CODE/scripts/eval.py" \
    --checkpoint "$OUT/checkpoints/$name/final.pt" \
    --config "$CODE/config/$config" \
    --cnbe-paths "$@" \
    --output "$OUT/${name}_eval_metrics.json"
}

run_arm moe128 v1_moe128_dcu2.yaml "${V1_FILES[@]}"
run_arm dense v1_dense_dcu2.yaml "${V1_FILES[@]}"
if [ "${SKIP_UNICODE:-0}" != "1" ]; then
  run_arm unicode v1_unicode_dcu2.yaml "$OUT/data_unicode/unicode.u32"
fi
if [ "${RUN_MATCHED:-0}" = "1" ]; then
  run_arm dense_matched v1_dense_matched_dcu2.yaml "${V1_FILES[@]}"
fi

eval_arm moe128 v1_moe128_dcu2.yaml "${V1_FILES[@]}"
eval_arm dense v1_dense_dcu2.yaml "${V1_FILES[@]}"
if [ "${SKIP_UNICODE:-0}" != "1" ]; then
  eval_arm unicode v1_unicode_dcu2.yaml "$OUT/data_unicode/unicode.u32"
fi
if [ "${RUN_MATCHED:-0}" = "1" ]; then
  eval_arm dense_matched v1_dense_matched_dcu2.yaml "${V1_FILES[@]}"
fi

python "$ROOT/scripts/make_v1_table.py" --output-dir "$OUT"
echo "== done =="
echo "table: $OUT/comparison_table.md"
