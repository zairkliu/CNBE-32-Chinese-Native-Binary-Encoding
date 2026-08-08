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
全部为 Linux 兼容内容，无 Windows 路径。

## 目录

```
scnet_upload_package/
  code/                 # CNBE-MoE 代码（可覆盖镜像内 /app）
  data/                 # 7 个 .cnbe 训练码流
  data_src/             # 7 个原始 .chars.txt 字表语料
  assets/               # vocab.json + mapping_128/256.json
  history/              # 前期训练结果、报告、脚本
  startup.sh            # 8 卡正式训练入口
  startup_smoke.sh      # 单进程 smoke 入口
  BOOTSTRAP.md          # 全新系统白手起家说明
  README_UPLOAD.md
  manifest.json
```

## 上传与挂载建议

1. 将 `scnet_upload_package.tar.gz` 上传到 SCNet 存储并解压；
2. 在模型训练任务中挂载：

| 上传目录 | 容器路径 |
|---|---|
| `.../code` | `/app` |
| `.../data` | `/data/cnbe` |
| `.../assets` | `/app/assets` |
| `.../output` | `/output` |

3. 启动命令：

```bash
bash /app/startup.sh
```

smoke 验证：

```bash
bash /app/startup_smoke.sh
```

## 正式训练配置

`code/config/scnet_moe_config_c.yaml`：

- d_model=1024, d_ff=4096, 16 层, 16 头
- 256 专家, Top-2, 三字段硬路由
- seq_len=256, batch_size=16/卡, grad_accum=4
- 24M tokens 训练 10 epoch

## 要求

- 镜像：`cnbe-moe-scnet:0.1`
- Linux 环境，NVIDIA CUDA GPU
- 启动目录：`/app`
- 输出目录：`/output`
"""

BOOTSTRAP = """\
# 全新系统白手起家引导

本包设计为可在“全新的 Linux 系统”中独立完成 CNBE-MoE 训练，不依赖任何本机路径。

## 1. 上传并解压

```bash
tar -xzf scnet_upload_package.tar.gz
cd scnet_upload_package
```

## 2. 构建镜像（如果 SCNet 已有镜像可跳过）

```bash
cd code
docker build -t cnbe-moe-scnet:0.1 .
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

预期输出 `/output/smoke_metrics.json`。

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
set -e

mkdir -p /output/checkpoints

torchrun --nproc_per_node=${NPROC_PER_NODE:-8} --nnodes=${NNODES:-1} \\
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
    write_lf(PACKAGE / "BOOTSTRAP.md", BOOTSTRAP)
    write_lf(PACKAGE / "history" / "TRAINING_HISTORY.md", TRAINING_HISTORY)
    manifest = {
        "package": "scnet_upload_package",
        "generated_at": "2026-08-08",
        "image": "cnbe-moe-scnet:0.1",
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
