#!/usr/bin/env python3
"""Package code, data, assets, and startup scripts for SCNet model training."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

import prepare_scnet_image_bundle


EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
PACKAGE = EXP / "scnet_upload_package"

DATA_SOURCES = {
    "zzjh_294.cnbe": REPO.parent / "cnbe_compression_experiment" / "outputs" / "zzjh_294.cnbe",
    "luxun_18.cnbe": REPO.parent / "luxun_repro" / "outputs" / "luxun_18.cnbe",
    "agatha.cnbe": REPO.parent / "agatha_repro" / "outputs" / "agatha.cnbe",
    "csbook.cnbe": REPO.parent / "csbook_repro" / "outputs" / "csbook.cnbe",
    "jinyong.cnbe": REPO.parent / "jinyong_repro" / "outputs" / "jinyong.cnbe",
    "caixin.cnbe": REPO.parent / "caixin_repro" / "outputs" / "caixin.cnbe",
    "sushi.cnbe": REPO.parent / "sushi_repro" / "outputs" / "sushi.cnbe",
}

CHARS_SOURCES = {
    "zzjh_294.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "zzjh_294.chars.txt",
    "luxun_18.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "luxun_18.chars.txt",
    "agatha.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "agatha.chars.txt",
    "csbook.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "csbook.chars.txt",
    "jinyong.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "jinyong.chars.txt",
    "caixin.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "caixin.chars.txt",
    "sushi.chars.txt": REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data" / "sushi.chars.txt",
}

MOE_OUTPUTS = REPO.parent / "cnbe_moe_base" / "outputs"
MOE_REPRO_OUTPUTS = REPO.parent / "cnbe_moe" / "outputs"
MOE_DOCS = [
    REPO.parent / "cnbe_moe" / "report.md",
    REPO.parent / "cnbe_moe" / "README.md",
    REPO / "experiments" / "2026-08-03_cnbe_moe" / "CNBE_MoE_最终报告.md",
    REPO / "experiments" / "2026-08-03_cnbe_moe" / "CNBE_MoE_API消融实验报告.md",
    REPO / "experiments" / "2026-08-03_cnbe_moe" / "README.md",
    REPO.parent / "cnbe_moe_base" / "README.md",
]
MOE_SCRIPTS = [
    REPO.parent / "cnbe_moe_base" / "run.py",
]

README = """\
# SCNet CNBE-MoE 上传包

本包包含代码、7 个 CNBE 语料、vocab、128/256 专家映射和启动脚本。
全部为 Linux 兼容内容，无 Windows 路径，面向 SCNet 的 DCU 或 A800 训练任务。

## 目录

```
scnet_upload_package/
  code/                 # CNBE-MoE 代码（可覆盖镜像内 /app）
  code/notebooks/       # JupyterLab 开发工作流（Ubuntu 22.04 首选入口）
  data/                 # 7 个 .cnbe 训练码流
  data_src/             # 7 个原始 .chars.txt 字表语料
  assets/               # vocab.json + mapping_128/256.json
  history/              # 前期训练结果、报告、脚本
  startup.sh            # 正式训练入口（自动适配 SCNet 环境变量）
  startup_smoke.sh      # 单进程 smoke 入口
  scnet_startup.sh      # 表单直接使用的总启动脚本（冒烟 + 正式训练）
  scnet_startup_l20.sh  # NVIDIA L20 / CUDA 12.4 专用启动脚本
  scnet_diag.sh         # 容器异常退出排查诊断脚本
  SCNET_DCU_FORM_GUIDE.md  # DCU 训练表单填写指南
  BOOTSTRAP.md          # 全新系统白手起家说明
  README_UPLOAD.md
  manifest.json
```

## 表单选择速览（详见 SCNET_DCU_FORM_GUIDE.md）

| 表单项 | 推荐值 |
|---|---|
| 加速卡 | DCU（异构加速卡） |
| 开发工具 | JupyterLab / Jupyter |
| Python | 3.10 |
| DTK | 24.04.1 或 24.04.2 |
| 操作系统 | Ubuntu 20.04 / 22.04 |
| 基础镜像 | PyTorch / 2.1.0 / py3.10-ubuntu20.04 / dtk-24.04.1 |

> 若表单实际提供 **NVIDIA A800 + CUDA 12.4**（如华东四区山东 087/016 组），
> 则必须改选 **CUDA 12.4 的 PyTorch Jupyter 镜像**，不能使用上面的 DTK/DCU 镜像；
> 具体选择见 `SCNET_DCU_FORM_GUIDE.md` 第零节。

## 上传与挂载建议

1. 将 `scnet_upload_package.tar.gz` 上传到 SCNet 存储并解压；
2. 在模型训练任务中挂载：

| 上传目录 | 容器路径 |
|---|---|
| `.../code` | `/app` |
| `.../data` | `/data/cnbe` |
| `.../assets` | `/app/assets` |
| `.../output` | `/output` |

3. 先跑 smoke 验证 DCU 与数据挂载：

```bash
bash /app/startup_smoke.sh
```

4. 正式训练：

```bash
bash /app/startup.sh
```

## 表单一键启动

SCNet 训练表单的“启动脚本”字段可直接粘贴：

```bash
bash /app/scnet_startup.sh
```

该脚本会先检查挂载，再跑 smoke，通过后自动进入正式训练。
也支持 `bash /app/scnet_startup.sh --smoke-only` 只冒烟。

## Jupyter 开发工作流（Ubuntu 22.04）

创建 Notebook 时选择 **JupyterLab** 和 **CUDA 12.4 的 PyTorch 镜像**
（Python 3.10，Ubuntu 22.04）。挂载完成后，在 JupyterLab 打开：

```text
code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb
```

Notebook 会依次执行：环境检查 → 挂载检查 → 配置加载 → 冒烟训练 →
结果查看。正式多卡训练仍在 Jupyter 的 Terminal 里执行：

```bash
bash /app/startup.sh
```

## 正式训练配置

`code/config/scnet_moe_config_c.yaml`：

- d_model=1024, d_ff=4096, 16 层, 16 头
- 256 专家, Top-2, 三字段硬路由
- seq_len=256, batch_size=16/卡, grad_accum=4
- 24M tokens 训练 10 epoch

## 要求

- 基础镜像：SCNet 官方 DCU 镜像（PyTorch 2.1.0 + Python 3.10 + DTK 24.04）
- 启动目录：`/app`
- 输出目录：`/output`
- 本包不依赖 CUDA 专有代码；DCU 的 DAS 栈会兼容 `torch.cuda.is_available()`
"""

BOOTSTRAP = """\
# 全新系统白手起家引导

本包设计为可在 SCNet 的全新 Linux/DCU 或 A800 系统中独立完成 CNBE-MoE 训练，
不依赖任何本机路径。

## 1. 上传并解压

```bash
tar -xzf scnet_upload_package.tar.gz
cd scnet_upload_package
```

## 2. 选择与加速卡匹配的基础镜像

若资源是 **DCU**，推荐直接使用 SCNet 官方 DCU 基础镜像：

`PyTorch / 2.1.0 / py3.10-ubuntu20.04 / dtk-24.04.1`

若实际资源是 **NVIDIA A800 + CUDA 12.4**，则改用 CUDA 12.4 的 PyTorch
Jupyter 基础镜像（如 `pytorch 2.x + cuda12.4 + py3.10 + ubuntu22.04`），
并选择 **016 组（2 卡）**；不要选 DTK/DCU 镜像。开发工具固定选
**JupyterLab / Jupyter**。

如需自建镜像，可基于 SourceFind 的 DCU 镜像：

```bash
cd code
docker build \
  --build-arg BASE_IMAGE=image.sourcefind.cn:5000/dcu/admin/base/pytorch:2.1.0-ubuntu22.04-dtk24.04.2-py3.10 \
  -t cnbe-moe-scnet:0.1 .
```

## 3. 准备目录

```bash
mkdir -p output
cp -r data /data/cnbe
cp -r code /app
cp -r assets /app/assets
```

或按 SCNet 训练任务的挂载表配置：

| 本包目录 | 容器路径 |
|---|---|
| `code` | `/app` |
| `data` | `/data/cnbe` |
| `assets` | `/app/assets` |
| `output` | `/output` |

## 4. 冒烟验证

```bash
bash /app/startup_smoke.sh
```

预期输出 `/output/smoke_metrics.json`。若需确认 DCU 可见：

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

## 4.5 JupyterLab 开发入口（Ubuntu 22.04）

创建 Notebook 时选择 JupyterLab 与匹配的基础镜像后，在 JupyterLab 中打开：

```text
code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb
```

依次运行：环境检查 → 挂载检查 → 配置加载 → 冒烟训练 → 结果查看。

## 4.6 表单一键启动

训练表单的“启动脚本”字段可直接粘贴：

```bash
bash /app/scnet_startup.sh
```

脚本会先检查 `code/data/output` 挂载，再跑 smoke，通过后自动进入正式训练。

## 5. 正式训练（配置 C，256 专家 / 16 层 / 10 epoch）

```bash
bash /app/startup.sh
```

checkpoint 写入 `/output/checkpoints/`，指标写入 `/output/train_metrics.json`。

## 6. 可复现说明

- 7 个 `.cnbe` 码流是训练输入；
- 7 个 `.chars.txt` 是原始字表语料，可用于重建码流；
- `assets/vocab.json` 与 `mapping_128/256.json` 由全量语料预生成；
- `history/` 包含前期所有训练步数、配置与结果，供对照和续训；
- 私有语料不进入公开仓库，只存在于本上传包。
"""

TRAINING_HISTORY = """\
# CNBE-MoE 前期训练历史

## Phase 0/1（3M 字，d_model=256，800 步）

| 模型 | Eval Loss | Next-code |
|---|---:|---:|
| Dense | 5.856 | 14.49% |
| MoE-8 | 5.683 | 16.24% |
| MoE-16 | 5.648 | 16.58% |

## Phase 2（6M 字，d_model=384，1200 步）

| 模型 | Eval Loss | Next-code | 训练期 Gini | 参数量 |
|---|---:|---:|---:|---:|
| Dense | 5.461 | 15.92% | - | 12.0M |
| MoE-8 | 5.295 | 17.65% | 0.030 | 28.6M |
| MoE-16 | 5.262 | 17.99% | 0.162 | 47.5M |
| MoE-64 | 5.187 | 19.18% | 0.297 | 160.9M |
| MoE-64-3f | 5.199 | 18.98% | 0.153 | ~160M |

## Ubuntu 26.04 验证（MoE-64，1200 步）

向量化 grouped GEMM 吞吐 9.02 steps/s；Triton kernel 前向/反向一致性误差 1e-7。

## DeepSeek V4 API 消融（2026-08-03）

| 任务 | 原文 | CNBE 提示 | Unicode 提示 |
|---|---:|---:|---:|
| 句读 F1 | 0.8472 | 0.8348 | 0.6544 |
| 形近字纠正 | 0.6000 | 0.9333 | 0.7667 |

## 本次 SCNet 目标

配置 C：d_model=1024，d_ff=4096，16 层，256 专家，24M tokens，10 epoch。

## 完整结果文件

- `history/results/`：`cnbe_moe_base/outputs/*.json`
- `history/api_and_routing/`：`cnbe_moe/outputs/*.json`
- `history/docs/`：最终报告与消融报告
"""


STARTUP = """\
#!/usr/bin/env bash
set -euo pipefail

mkdir -p /output/checkpoints

if [ -z "${NPROC_PER_NODE:-}" ]; then
  if [ -n "${HIP_VISIBLE_DEVICES:-}" ]; then
    NPROC_PER_NODE=$(printf '%s' "$HIP_VISIBLE_DEVICES" | tr ',' '\\n' | wc -l)
  elif [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
    NPROC_PER_NODE=$(printf '%s' "$CUDA_VISIBLE_DEVICES" | tr ',' '\\n' | wc -l)
  else
    NPROC_PER_NODE=$(python -c "import torch; print(torch.cuda.device_count() or 1)" 2>/dev/null || echo 1)
  fi
fi
: "${NPROC_PER_NODE:=1}"

NNODES=${NNODES:-${WORLD_SIZE:-1}}
NODE_RANK=${NODE_RANK:-${RANK:-0}}

ARGS=(--nproc_per_node="${NPROC_PER_NODE}")
if [ -n "${MASTER_ADDR:-}" ]; then
  ARGS+=(--nnodes="${NNODES}" --node_rank="${NODE_RANK}" \\
    --master_addr="${MASTER_ADDR}" --master_port="${MASTER_PORT:-29500}")
else
  ARGS+=(--standalone)
fi

torchrun "${ARGS[@]}" \\
  /app/scripts/train_distributed.py \\
  --config /app/config/scnet_moe_config_c.yaml \\
  --output /output/train_metrics.json \\
  --checkpoint-dir /output/checkpoints
"""

STARTUP_SMOKE = """\
#!/usr/bin/env bash
set -e

mkdir -p /output

python /app/scripts/train_scnet.py \\
  --smoke \\
  --cnbe-paths /data/cnbe/zzjh_294.cnbe \\
  --output /output/smoke_metrics.json
"""

SCNET_STARTUP = """\
#!/usr/bin/env bash
# SCNet CNBE-MoE startup script.
# Defaults assume custom mounts:
#   code   -> /app
#   data   -> /data/cnbe
#   output -> /output
# If mounts are missing, the script searches the uploaded package under
# /root, /root/private_data, /root/group_data and /root/public_data.
set -euo pipefail
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

ROOT="${CNBE_MOE_ROOT:-/app}"
DATA="${CNBE_DATA_DIR:-/data/cnbe}"
OUT="${CNBE_OUTPUT_DIR:-/output}"
MAPPING="${CNBE_MAPPING_DIR:-${OUT}/mappings}"
CONFIG="${CNBE_MOE_CONFIG:-scnet_moe_config_c.yaml}"

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
    found=$(find "$base" -maxdepth 4 -type d -name "scnet_upload_package_DCU" 2>/dev/null | head -n1)
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

check_mounts() {
  [ -f "$ROOT/scripts/train_scnet.py" ] || { echo "code not mounted at $ROOT" >&2; exit 1; }
  [ -f "$ROOT/scripts/train_distributed.py" ] || { echo "train_distributed.py missing" >&2; exit 1; }
  [ -f "$ROOT/config/$CONFIG" ] || { echo "config missing: $CONFIG" >&2; exit 1; }
  [ -f "$DATA/zzjh_294.cnbe" ] || { echo "data not mounted at $DATA" >&2; exit 1; }
}

env_info() {
  echo "== CNBE-MoE SCNet startup =="
  echo "root=$ROOT"
  echo "data=$DATA"
  echo "out=$OUT"
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
print("HIP_VISIBLE_DEVICES:", os.environ.get("HIP_VISIBLE_DEVICES"))
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
PY
}

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
    printf '%s' "$CUDA_VISIBLE_DEVICES" | tr ',' '\\n' | wc -l
    return
  fi
  if [ -n "${HIP_VISIBLE_DEVICES:-}" ]; then
    printf '%s' "$HIP_VISIBLE_DEVICES" | tr ',' '\\n' | wc -l
    return
  fi
  echo 1
}

run_smoke() {
  echo "== smoke =="
  mkdir -p "$OUT"
  CNBE_MAPPING_DIR="$MAPPING" python "$ROOT/scripts/train_scnet.py" \\
    --smoke \\
    --config "$ROOT/config/$CONFIG" \\
    --cnbe-paths "$DATA/zzjh_294.cnbe" \\
    --output "$OUT/smoke_metrics.json"
  echo "smoke metrics: $OUT/smoke_metrics.json"
}

run_train() {
  echo "== training =="
  mkdir -p "$OUT/checkpoints" "$MAPPING"
  NPROC=$(detect_nproc)
  NNODES="${NNODES:-${WORLD_SIZE:-1}}"
  NODE_RANK="${NODE_RANK:-${RANK:-0}}"
  ARGS=(--nproc_per_node="$NPROC")
  if [ -n "${MASTER_ADDR:-}" ]; then
    ARGS+=(--nnodes="$NNODES" --node_rank="$NODE_RANK" \\
      --master_addr="$MASTER_ADDR" --master_port="${MASTER_PORT:-29500}")
  else
    ARGS+=(--standalone)
  fi
  echo "nproc_per_node=$NPROC nnodes=$NNODES node_rank=$NODE_RANK"
  CNBE_MAPPING_DIR="$MAPPING" torchrun "${ARGS[@]}" \\
    "$ROOT/scripts/train_distributed.py" \\
    --config "$ROOT/config/$CONFIG" \\
    --cnbe-paths "$DATA"/*.cnbe \\
    --output "$OUT/train_metrics.json" \\
    --checkpoint-dir "$OUT/checkpoints"
}

check_mounts
env_info
if [ "$TRAIN_ONLY" -eq 1 ]; then
  run_train
elif [ "$SMOKE_ONLY" -eq 1 ]; then
  run_smoke
else
  run_smoke
  run_train
fi
"""

DCU_FORM_GUIDE = """\
# SCNet 训练表单填写指南（DCU 与 A800 双场景）

日期：2026-08-08
目标：CNBE-MoE 256 专家分布式训练（配置 C）

## 零、A800 / CUDA 12.4 场景（当前表单出现 A800 时优先）

若创建页面出现：

```
NVIDIA A800 80GB PCIE，单机，CUDA 12.4，华东四区【山东】
087 组：1 卡
016 组：2 卡
```

按以下方式填写：

| 表单项 | 推荐值 | 原因 |
|---|---|---|
| 资源组 | **016 组（2 卡）** | 单机 2 卡可跑 DDP；087 只有 1 卡，训练步数翻倍 |
| 开发工具 | **JupyterLab / Jupyter** | 平台要求镜像包含 Jupyter，否则容器实例功能可能不可用 |
| 镜像类型 | **CUDA 12.4 的 PyTorch 基础镜像** | 必须与 A800/CUDA 12.4 匹配，不能选 DTK/DCU 镜像 |
| Python | 3.10（镜像内） | 与 CUDA PyTorch 官方镜像配套，推荐 2.1/2.3/2.4 系列 |
| 操作系统 | Ubuntu 22.04 | 平台封装支持，依赖最通用 |

选择镜像时以控制台实际列表为准，只要同时满足：

1. 镜像名/描述含 `cuda12.4` 或 `cuda-12.4`；
2. 镜像类型是 PyTorch（2.1、2.3、2.4 均可）；
3. 该镜像自带 Jupyter（开发工具选 JupyterLab 后能正常进入终端）；
4. 不要选 `dtk`、`dcu`、`centos-7.6-dtk` 等异构加速卡镜像。

## 一、DCU 场景表单推荐值（若页面只提供 DCU 时使用）

| 表单项 | 推荐值 | 原因 |
|---|---|---|
| 加速卡 | DCU（异构加速卡） | 平台训练仅提供 DCU；本包不依赖 CUDA 专有代码 |
| 开发工具 | JupyterLab / Jupyter | 官方 DCU 基础镜像自带；用于创建后冒烟验证和文件检查 |
| Python | 3.10 | 与官方 PyTorch 2.1.0 + DTK 24.04 镜像配套 |
| DTK | 24.04.1 或 24.04.2 | 平台异构加速卡 AI 仅支持 dtk 24.04 及以上 |
| 操作系统 | Ubuntu 20.04 / 22.04 均可 | 优先选择官方镜像自带版本；两者均被平台封装支持 |
| 基础镜像 | PyTorch / 2.1.0 / py3.10-ubuntu20.04 / dtk-24.04.1 | SCNet 官方 DCU 基础镜像 |

## 二、为什么这样选

1. DCU 的 PyTorch 由 DAS 软件栈提供，`torch.cuda.is_available()` 返回
   `True`，`nn.Linear`、`MultiheadAttention` 等标准模块无需改写；
2. 官方 DCU 基础镜像最常见的组合就是 PyTorch 2.1.0 + Python 3.10 +
   DTK 24.04，这是兼容面最大、平台文档示例最多的组合；
3. DTK 24.04 是平台对异构加速卡 AI 支持的下限，24.04.1/24.04.2 均为
   已验证版本，不建议选更早版本；
4. Ubuntu 20.04 与 22.04 都满足平台对 SSH/SUDO 封装的支持范围；
   若表单两者都有，选官方镜像对应的版本即可。

## 三、为什么不选其他项

| 选项 | 结论 |
|---|---|
| VS Code | 仅适合容器实例 + SSH；模型训练表单通常由 Jupyter 打开控制台，选 Jupyter 更稳 |
| RStudio | 面向 R 语言，与 PyTorch/CNBE-MoE 无关 |
| Python 3.11/3.12 | 官方 DCU PyTorch 2.1.0 镜像以 Python 3.10 为准 |
| DTK 24.04 以下 | 平台不支持，无法创建异构加速卡任务 |
| CentOS 7 | 可用但不是本包首选，Ubuntu 依赖更通用 |

## 四、创建任务后的验证顺序

1. 在 Jupyter 终端确认加速卡可见（DCU 的 DAS 栈同样兼容 CUDA API）：

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

2. 确认挂载：

```bash
ls /app/scripts/train_scnet.py
ls /data/cnbe/zzjh_294.cnbe
ls /output
```

3. 冒烟：

```bash
bash /app/startup_smoke.sh
```

预期生成 `/output/smoke_metrics.json`。

4. 正式训练：

```bash
bash /app/startup.sh
```

## 四.5 JupyterLab 开发入口（Ubuntu 22.04）

创建 Notebook 时选择 **JupyterLab** 与匹配的基础镜像。挂载完成后，
在 JupyterLab 文件树打开：

```text
code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb
```

Notebook 依次执行：环境检查 → 挂载检查 → 配置加载 → 冒烟训练 →
结果查看；正式多卡训练在 Jupyter 的 Terminal 执行：

```bash
bash /app/startup.sh
```

## 五、多卡注意事项

- `startup.sh` 会自动读取 SCNet 注入的 `MASTER_ADDR`、`MASTER_PORT`、
  `WORLD_SIZE`、`RANK` 环境变量；没有这些变量时自动回退单节点 standalone；
- 若 DCU 的 `nccl` 兼容后端异常，可先设置 `DIST_BACKEND=gloo` 排查；
- A800 场景按正常 CUDA 流程即可，`nccl` 后端可用时无需额外设置；
- 训练代码支持 Triton 不可用时的向量化 grouped GEMM 回退，不影响运行。
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    prepare_scnet_image_bundle.main()
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    for sub in ("code", "data", "data_src", "assets", "history", "history/results", "history/api_and_routing", "history/docs", "history/scripts"):
        (PACKAGE / sub).mkdir(parents=True, exist_ok=True)

    shutil.copytree(EXP / "scnet_cnbe_moe_bundle", PACKAGE / "code", dirs_exist_ok=True)

    files: list[dict] = []
    for name, src in DATA_SOURCES.items():
        if not src.exists():
            print("missing data:", src)
            return 1
        dst = PACKAGE / "data" / name
        shutil.copy2(src, dst)
        files.append(
            {
                "path": f"data/{name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )

    for name, src in CHARS_SOURCES.items():
        if not src.exists():
            print("missing chars:", src)
            return 1
        dst = PACKAGE / "data_src" / name
        shutil.copy2(src, dst)
        files.append(
            {
                "path": f"data_src/{name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )

    for json_path in MOE_OUTPUTS.glob("*.json"):
        dst = PACKAGE / "history" / "results" / json_path.name
        shutil.copy2(json_path, dst)
        files.append(
            {
                "path": f"history/results/{json_path.name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )
    for json_path in MOE_REPRO_OUTPUTS.glob("*.json"):
        dst = PACKAGE / "history" / "api_and_routing" / json_path.name
        shutil.copy2(json_path, dst)
        files.append(
            {
                "path": f"history/api_and_routing/{json_path.name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )
    for doc in MOE_DOCS:
        if not doc.exists():
            print("missing doc:", doc)
            continue
        dst = PACKAGE / "history" / "docs" / doc.name
        shutil.copy2(doc, dst)
        files.append(
            {
                "path": f"history/docs/{doc.name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )
    for script in MOE_SCRIPTS:
        if not script.exists():
            continue
        dst = PACKAGE / "history" / "scripts" / script.name
        shutil.copy2(script, dst)
        files.append(
            {
                "path": f"history/scripts/{script.name}",
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )

    for asset in (EXP / "scnet_upload_assets").glob("*"):
        if asset.is_file():
            dst = PACKAGE / "assets" / asset.name
            shutil.copy2(asset, dst)
            files.append(
                {
                    "path": f"assets/{asset.name}",
                    "bytes": dst.stat().st_size,
                    "sha256": sha256(dst),
                }
            )

    def write_lf(path: Path, text: str) -> None:
        with path.open("w", newline="\n", encoding="utf-8") as f:
            f.write(text)

    write_lf(PACKAGE / "README_UPLOAD.md", README)
    write_lf(PACKAGE / "startup.sh", STARTUP)
    write_lf(PACKAGE / "startup_smoke.sh", STARTUP_SMOKE)
    write_lf(PACKAGE / "scnet_startup.sh", SCNET_STARTUP)
    l20_script = EXP / "scnet_startup_l20.sh"
    if l20_script.exists():
        shutil.copy2(l20_script, PACKAGE / "scnet_startup_l20.sh")
    diag_script = EXP / "scnet_diag.sh"
    if diag_script.exists():
        shutil.copy2(diag_script, PACKAGE / "scnet_diag.sh")
    write_lf(PACKAGE / "BOOTSTRAP.md", BOOTSTRAP)
    write_lf(PACKAGE / "SCNET_DCU_FORM_GUIDE.md", DCU_FORM_GUIDE)
    write_lf(PACKAGE / "history" / "TRAINING_HISTORY.md", TRAINING_HISTORY)
    manifest = {
        "package": "scnet_upload_package",
        "generated_at": "2026-08-08",
        "image": "cnbe-moe-scnet:0.1",
        "scnet_form": {
            "accelerator": "DCU",
            "dev_tool": "JupyterLab",
            "python": "3.10",
            "dtk": "24.04.1 / 24.04.2",
            "os": "Ubuntu 20.04 / 22.04",
            "base_image": "PyTorch/2.1.0/py3.10-ubuntu20.04/dtk24.04.1",
        },
        "scnet_form_a800": {
            "resource_group": "016 组（2 卡）",
            "accelerator": "NVIDIA A800 80GB PCIE",
            "cuda": "12.4",
            "dev_tool": "JupyterLab / Jupyter",
            "image": "CUDA 12.4 的 PyTorch Jupyter 基础镜像",
            "python": "3.10",
            "os": "Ubuntu 22.04",
        },
        "jupyter": "code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb",
        "config": "code/config/scnet_moe_config_c.yaml",
        "files": files,
    }
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    tar_path = EXP / "scnet_upload_package.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(PACKAGE, arcname="scnet_upload_package")

    print("package:", PACKAGE)
    print("tar:", tar_path, tar_path.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
