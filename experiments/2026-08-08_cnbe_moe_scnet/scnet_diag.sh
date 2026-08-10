#!/usr/bin/env bash
# SCNet CNBE-MoE container diagnostic.
# Prints environment and mount state, then exits 0 so the container can be
# examined without being marked as an abnormal training run.
set -x

echo "== env =="
env | sort

echo "== mounts =="
ls -la /app 2>&1 || true
ls -la /data/cnbe 2>&1 || true
ls -la /output 2>&1 || true
ls -la /root/private_data 2>&1 || true
ls -la /root 2>&1 || true

echo "== python =="
python -V 2>&1 || true
python - <<'PY'
import os
import platform
import sys

print("python:", sys.version.split()[0])
print("platform:", platform.platform())
try:
    import torch
    print("torch:", torch.__version__)
    print("cuda_available:", torch.cuda.is_available())
    print("cuda_device_count:", torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print("device", i, torch.cuda.get_device_name(i), props.total_memory // (1024**3), "GB")
except Exception as exc:
    print("torch_error:", repr(exc))
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
print("HIP_VISIBLE_DEVICES:", os.environ.get("HIP_VISIBLE_DEVICES"))
print("MASTER_ADDR:", os.environ.get("MASTER_ADDR"))
print("MASTER_PORT:", os.environ.get("MASTER_PORT"))
print("WORLD_SIZE:", os.environ.get("WORLD_SIZE"))
print("RANK:", os.environ.get("RANK"))
PY

echo "DIAG_DONE"
