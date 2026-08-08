#!/usr/bin/env python3
"""Prepare the SCNet CNBE-MoE image build bundle."""

from __future__ import annotations

import shutil
import sys
import tarfile
from pathlib import Path


EXP = Path(__file__).resolve().parent
BUNDLE = EXP / "scnet_cnbe_moe_bundle"
SRC_SOURCE = EXP.parents[0] / "2026-08-03_cnbe_moe" / "cnbe_moe_base" / "src"
SCRIPTS_SOURCE = EXP / "scripts_src"
CONFIG_SOURCE = EXP / "config_src"

DOCKERFILE = """\
ARG BASE_IMAGE=pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime
FROM ${BASE_IMAGE}

WORKDIR /app

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY config ./config
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV TORCH_HOME=/app/.cache/torch

ENTRYPOINT ["/app/entrypoint.sh"]
"""

REQUIREMENTS = """\
numpy>=1.24
PyYAML>=6.0
"""

ENTRYPOINT = """\
#!/usr/bin/env bash
set -e

if [ $# -eq 0 ]; then
  echo "Usage: docker run IMAGE [command]"
  echo "Example: python scripts/train_scnet.py --smoke"
  exit 1
fi

exec "$@"
"""

TRAIN_SCNET = """\
#!/usr/bin/env python3
# SCNet CNBE-MoE single-process training entry (smoke and full run).

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cnbe_router import build_balanced_mapping  # noqa: E402
from src.data import CodeDataset, build_vocab, id_to_code_array, load_codes  # noqa: E402
from src.train import train_eval  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="CNBE-MoE SCNet training entry")
    ap.add_argument("--config", default="/app/config/scnet_moe_config_a.yaml")
    ap.add_argument("--cnbe-paths", nargs="+", default=[])
    ap.add_argument("--output", default="/output/metrics.json")
    ap.add_argument("--smoke", action="store_true", help="run a tiny smoke test")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    model_cfg = cfg["model"]
    train_cfg = cfg["training"]

    paths = args.cnbe_paths or data_cfg["cnbe_paths"]
    if not paths:
        print("no cnbe paths", flush=True)
        return 2

    if args.smoke:
        max_train = 20_000
        max_eval = 2_000
        seq_len = 32
        batch_size = 2
        steps = 5
        d_model = 64
        d_ff = 128
        layers = 1
        heads = 2
        experts = 8
    else:
        max_train = int(data_cfg.get("max_train_tokens", 24_000_000))
        max_eval = int(data_cfg.get("max_eval_tokens", 1_200_000))
        seq_len = int(train_cfg["seq_len"])
        batch_size = int(train_cfg["batch_size"])
        steps = int(train_cfg.get("steps", 1000))
        d_model = int(model_cfg["d_model"])
        d_ff = int(model_cfg["d_ff"])
        layers = int(model_cfg["n_layers"])
        heads = int(model_cfg["n_heads"])
        experts = int(model_cfg["num_experts"])

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading {len(paths)} cnbe files, device={device}", flush=True)
    codes = load_codes(paths, max_train + max_eval)
    train_codes = codes[:max_train]
    eval_codes = codes[max_train : max_train + max_eval]
    vocab = build_vocab(codes)
    id_to_code = id_to_code_array(vocab).tolist()
    print(
        f"train={len(train_codes):,} eval={len(eval_codes):,} vocab={len(vocab):,}",
        flush=True,
    )

    mapping_dir = Path("/app/mappings")
    mapping_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = mapping_dir / f"mapping_{experts}.json"
    mapping_path.write_text(
        json.dumps(build_balanced_mapping(train_codes, experts, mode=3), ensure_ascii=False),
        encoding="utf-8",
    )
    print("saved mapping:", mapping_path, flush=True)

    train_ds = CodeDataset(train_codes, vocab, seq_len)
    eval_ds = CodeDataset(eval_codes, vocab, seq_len)

    result = train_eval(
        train_ds,
        eval_ds,
        len(vocab),
        id_to_code,
        use_moe=True,
        mapping_path=str(mapping_path),
        num_experts=experts,
        top_k=int(model_cfg["top_k"]),
        d_model=d_model,
        d_ff=d_ff,
        n_layers=layers,
        n_heads=heads,
        batch_size=batch_size,
        steps=steps,
        device=device,
        aux_loss_weight=float(model_cfg.get("aux_loss_weight", 0.1)),
        balance_weight=float(model_cfg.get("balance_weight", 0.01)),
        learned_router=bool(model_cfg.get("learned_router", False)),
    )
    result["smoke"] = args.smoke
    result["config"] = {
        "max_train": max_train,
        "max_eval": max_eval,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "steps": steps,
        "d_model": d_model,
        "d_ff": d_ff,
        "layers": layers,
        "heads": heads,
        "experts": experts,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print("saved:", out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

CONFIG_YAML = """\
experiment_name: cnbe-moe-128-scnet
seed: 42
device: cuda

data:
  cnbe_paths:
    - /data/cnbe/zzjh_294.cnbe
    - /data/cnbe/luxun_18.cnbe
    - /data/cnbe/agatha.cnbe
    - /data/cnbe/csbook.cnbe
    - /data/cnbe/jinyong.cnbe
    - /data/cnbe/caixin.cnbe
    - /data/cnbe/sushi.cnbe
  max_train_tokens: 24000000
  max_eval_tokens: 1200000

model:
  d_model: 512
  d_ff: 2048
  n_layers: 8
  n_heads: 8
  num_experts: 128
  top_k: 2
  dropout: 0.1
  use_moe: true
  learned_router: false
  balance_weight: 0.01
  aux_loss_weight: 0.1

training:
  seq_len: 256
  batch_size: 32
  grad_accum_steps: 4
  epochs: 2
  steps: 1000
  lr: 0.0003
  warmup_steps: 100
  weight_decay: 0.01
  grad_clip: 1.0
  precision: bf16
"""

README = """\
# SCNet CNBE-MoE 镜像构建包

## 内容

- `Dockerfile`：PyTorch 2.4.1 + CUDA 12.4 运行镜像
- `src/`：CNBE-MoE 原型代码（复制自 `experiments/2026-08-03_cnbe_moe/cnbe_moe_base/src`）
- `scripts/train_scnet.py`：单进程训练入口，支持 smoke / 全量
- `config/scnet_moe_config_a.yaml`：推荐配置 A
- `entrypoint.sh`：容器入口

## 在 SCNet 镜像管理创建

1. 打开 `https://www.scnet.cn/ui/console/index.html#/image-management/create`；
2. 镜像名建议：`cnbe-moe-scnet`，标签：`0.1`；
3. 构建源选择本目录 `scnet_cnbe_moe_bundle/`（或上传 `scnet_cnbe_moe_bundle.tar.gz`）；
4. Dockerfile 路径：`Dockerfile`；
5. 提交构建。

## 本地构建（有 Docker 时）

```bash
docker build -t cnbe-moe-scnet:0.1 ./scnet_cnbe_moe_bundle
```

本项目已在 Ubuntu-26.04 + Docker 29.1.3 完成构建，
并用真实 `zzjh_294.cnbe` 跑通 5 步 smoke 训练。

## 本地 smoke 测试

```bash
docker run --rm --gpus all cnbe-moe-scnet:0.1 \
  python scripts/train_scnet.py --smoke \
  --cnbe-paths /data/cnbe/zzjh_294.cnbe
```

## SCNet 作业启动命令

```bash
python scripts/train_scnet.py \
  --config /app/config/scnet_moe_config_a.yaml
```

smoke 验证：

```bash
python scripts/train_scnet.py \
  --smoke --cnbe-paths /data/cnbe/zzjh_294.cnbe
```

## 注意事项

- 数据文件不打包进镜像，训练时挂载 `/data/cnbe/`；
- 当前入口为单进程，多卡 DDP 入口会在下一阶段加入；
- 本地 GPU 透传需 `nvidia-container-toolkit`；SCNet 运行时自带 GPU 挂载，无需本地验证；
- 私有语料与训练代码不上传公开 GitHub。
"""


def main() -> int:
    if not SRC_SOURCE.exists():
        print("missing source:", SRC_SOURCE)
        return 1
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    for sub in ("src", "scripts", "config"):
        (BUNDLE / sub).mkdir(parents=True, exist_ok=True)

    for py in SRC_SOURCE.glob("*.py"):
        shutil.copy2(py, BUNDLE / "src" / py.name)
    for py in SCRIPTS_SOURCE.glob("*.py"):
        shutil.copy2(py, BUNDLE / "scripts" / py.name)
    for yml in CONFIG_SOURCE.glob("*.yaml"):
        shutil.copy2(yml, BUNDLE / "config" / yml.name)

    def write_lf(path: Path, text: str) -> None:
        with path.open("w", newline="\n", encoding="utf-8") as f:
            f.write(text)

    write_lf(BUNDLE / "Dockerfile", DOCKERFILE)
    write_lf(BUNDLE / "requirements.txt", REQUIREMENTS)
    write_lf(BUNDLE / "entrypoint.sh", ENTRYPOINT)
    write_lf(BUNDLE / "scripts" / "train_scnet.py", TRAIN_SCNET)
    write_lf(BUNDLE / "config" / "scnet_moe_config_a.yaml", CONFIG_YAML)
    write_lf(BUNDLE / "README.md", README)

    tar_path = EXP / "scnet_cnbe_moe_bundle.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(BUNDLE, arcname="scnet_cnbe_moe_bundle")

    print("bundle:", BUNDLE)
    print("tar:", tar_path)
    for p in sorted(BUNDLE.rglob("*")):
        if p.is_file():
            print(p.relative_to(EXP))
    return 0


if __name__ == "__main__":
    sys.exit(main())
