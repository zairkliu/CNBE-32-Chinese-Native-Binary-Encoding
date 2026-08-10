#!/usr/bin/env python3
"""Create the DCU-specific SCNet upload package with a _DCU suffix."""

from __future__ import annotations

import json
import shutil
import sys
import tarfile
from pathlib import Path

import prepare_scnet_upload_package as base


EXP = Path(__file__).resolve().parent
SRC = EXP / "scnet_upload_package"
DST = EXP / "scnet_upload_package_DCU"
BUNDLE_SRC = EXP / "scnet_cnbe_moe_bundle"
BUNDLE_DST = EXP / "scnet_cnbe_moe_bundle_DCU"

DCU_README = """\
# SCNet CNBE-MoE 上传包（DCU 版）

本包包含代码、7 个 CNBE 语料、vocab、128/256 专家映射、启动脚本和
JupyterLab 开发工作流。全部为 Linux 兼容内容，无 Windows 路径。

## 目录

```
scnet_upload_package_DCU/
  code/                 # CNBE-MoE 代码（可覆盖镜像内 /app）
  code/notebooks/       # JupyterLab 开发工作流
  data/                 # 7 个 .cnbe 训练码流
  data_src/             # 7 个原始 .chars.txt 字表语料
  assets/               # vocab.json + mapping_128/256.json
  history/              # 前期训练结果、报告、脚本
  startup.sh            # 正式训练入口（自动适配 SCNet 环境变量）
  startup_smoke.sh      # 单进程 smoke 入口
  SCNET_DCU_FORM_GUIDE.md  # DCU 训练表单填写指南
  BOOTSTRAP.md          # 全新系统白手起家说明
  README_UPLOAD.md
  manifest.json
```

## 表单选择速览（DCU）

| 表单项 | 推荐值 |
|---|---|
| 加速卡 | 异构加速卡BW（DCU，64GB） |
| 开发工具 | JupyterLab / Jupyter |
| Python | 3.11 |
| DTK | 26.04 |
| 操作系统 | Ubuntu 22.04 |
| 基础镜像 | PyTorch / 2.9.0 / py3.11-Ubuntu22.04 / dtk26.04 |

> 2026-08-08 控制台实测的基础镜像显示名为：
> `PyTorch / 2.9.0 / py3.11-Ubuntu22.04 / dtk26.04`
>
> 若必须填完整镜像地址，以控制台展开后的完整地址为准；不要填写
> 本地上次保存的自定义镜像名，自定义镜像当前无法启用。
>
## 上传与挂载建议

1. 将 `scnet_upload_package_DCU.tar.gz` 上传到 SCNet 存储并解压；
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

该脚本会先检查 `code/data/output` 挂载，再跑 smoke，通过后自动进入
正式训练；也支持 `bash /app/scnet_startup.sh --smoke-only` 只冒烟。

## Jupyter 开发工作流

创建 Notebook 时选择 **JupyterLab** 和 DCU 基础镜像。挂载完成后，
在 JupyterLab 打开：

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

- 基础镜像：SCNet 官方 DCU 镜像（PyTorch 2.9.0 + Python 3.11 + DTK 26.04）
- 开发工具：JupyterLab / Jupyter
- 启动目录：`/app`
- 输出目录：`/output`
- DCU 的 DAS 栈兼容 `torch.cuda.is_available()`，代码无需转码
"""

DCU_BOOTSTRAP = """\
# 全新系统白手起家引导（DCU 版）

本包设计为可在 SCNet 的全新 Linux/DCU 系统中独立完成 CNBE-MoE 训练，
不依赖任何本机路径。

## 1. 上传并解压

```bash
tar -xzf scnet_upload_package_DCU.tar.gz
cd scnet_upload_package_DCU
```

## 2. 选择 DCU 基础镜像

2026-08-08 控制台实测，请直接使用平台基础镜像：

`PyTorch / 2.9.0 / py3.11-Ubuntu22.04 / dtk26.04`

这是平台内置的官方 DCU 镜像（异构加速卡BW，64GB）。若表单要求填完整地址，
以控制台展开后的完整地址为准。自定义镜像当前无法启用，不要填写
本地 `cnbe-moe-scnet-dcu:0.1` 之类的名字。

开发工具固定选 **JupyterLab / Jupyter**，不要选 CUDA/A800 镜像。
如需自建镜像，本包 `code/Dockerfile` 已内置 Jupyter 安装步骤，但当前
阶段建议先用平台基础镜像跑通，不要阻塞在自定义镜像上。

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

## 4.1 表单一键启动

SCNet 训练表单的“启动脚本”字段可直接粘贴：

```bash
bash /app/scnet_startup.sh
```

脚本会先检查 `code/data/output` 挂载，再跑 smoke，通过后自动进入正式训练。

## 5. JupyterLab 开发入口

在 JupyterLab 中打开：

```text
code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb
```

依次运行：环境检查 → 挂载检查 → 配置加载 → 冒烟训练 → 结果查看。

## 6. 正式训练（配置 C，256 专家 / 16 层 / 10 epoch）

```bash
bash /app/startup.sh
```

checkpoint 写入 `/output/checkpoints/`，指标写入 `/output/train_metrics.json`。

## 7. 可复现说明

- 7 个 `.cnbe` 码流是训练输入；
- 7 个 `.chars.txt` 是原始字表语料，可用于重建码流；
- `assets/vocab.json` 与 `mapping_128/256.json` 由全量语料预生成；
- `history/` 包含前期所有训练步数、配置与结果，供对照和续训；
- 私有语料不进入公开仓库，只存在于本上传包。
"""

DCU_FORM_GUIDE = """\
# SCNet DCU 训练表单填写指南

日期：2026-08-08
目标：CNBE-MoE 256 专家分布式训练（配置 C）

## 一、表单推荐值

| 表单项 | 推荐值 | 原因 |
|---|---|---|
| 加速卡 | 异构加速卡BW（DCU，64GB） | 2026-08-08 控制台实际资源，本包不依赖 CUDA 专有代码 |
| 开发工具 | JupyterLab / Jupyter | 平台要求镜像包含 Jupyter，否则容器实例功能可能不可用 |
| Python | 3.11 | 平台基础镜像自带 |
| DTK | 26.04 | 平台基础镜像自带 |
| 操作系统 | Ubuntu 22.04 | 平台基础镜像自带 |
| 基础镜像 | PyTorch / 2.9.0 / py3.11-Ubuntu22.04 / dtk26.04 | 2026-08-08 控制台实测可用 |

## 二、为什么这样选

1. DCU 的 PyTorch 由 DAS 软件栈提供，`torch.cuda.is_available()` 返回
   `True`，`nn.Linear`、`MultiheadAttention` 等标准模块无需改写；
2. 当前控制台实测组合是 PyTorch 2.9.0 + Python 3.11 + DTK 26.04 +
   Ubuntu 22.04，直接使用平台基础镜像即可；
3. 自定义镜像当前无法启用，不要浪费时间在“我的镜像”上，先用平台
   基础镜像把项目和启动脚本跑通。

## 三、为什么不选其他项

| 选项 | 结论 |
|---|---|
| VS Code | 仅适合容器实例 + SSH；模型训练表单通常由 Jupyter 打开控制台 |
| RStudio | 面向 R 语言，与 PyTorch/CNBE-MoE 无关 |
| 自定义镜像 | 当前无法启用，先使用平台基础镜像 |
| CUDA/A800 镜像 | 与 DCU 硬件不匹配，会导致容器实例异常 |

## 四、镜像名称录入

平台表单里“镜像”通常分三种入口，不要混填：

1. 选择“**基础镜像**”时，直接在列表点选，显示名：
   `PyTorch / 2.9.0 / py3.11-Ubuntu22.04 / dtk26.04`
2. 如果表单要求填完整镜像地址，以控制台展开后的完整地址为准；
3. 不要填本地 Docker tag `cnbe-moe-scnet-dcu:0.1`，当前自定义镜像
   无法启用；
4. “我的镜像”只能选平台里已经保存过的镜像。

不要选“模型镜像”里的 4 个 CUDA 12.1 镜像，它们不是 DCU 训练镜像。

## 五、创建任务后的验证顺序

1. 在 Jupyter 终端确认 DCU 可见：

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

4. 训练表单“启动脚本”字段可直接粘贴：

```bash
bash /app/scnet_startup.sh
```

脚本会先检查挂载，再跑 smoke，通过后自动进入正式训练。

5. JupyterLab 打开 `code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb`，
   按顺序运行环境检查、挂载检查、配置加载、冒烟训练与结果查看。

6. 正式训练：

```bash
bash /app/startup.sh
```

## 六、多卡注意事项

- `startup.sh` 会自动读取 SCNet 注入的 `MASTER_ADDR`、`MASTER_PORT`、
  `WORLD_SIZE`、`RANK` 环境变量；没有这些变量时自动回退单节点 standalone；
- 若 DCU 的 `nccl` 兼容后端异常，可先设置 `DIST_BACKEND=gloo` 排查；
- 训练代码支持 Triton 不可用时的向量化 grouped GEMM 回退，不影响 DCU 运行。
"""

DCU_DOCKERFILE = """\
ARG BASE_IMAGE=image.sourcefind.cn:5000/dcu/admin/base/jupyterlab-pytorch:2.1.0-ubuntu20.04-dtk24.04.1-py3.10-scnet
FROM ${BASE_IMAGE}

WORKDIR /app

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} -r requirements.txt

# Ensure Jupyter is available at the platform-required path.
RUN python -m pip install --no-cache-dir jupyterlab && \
    mkdir -p /opt/conda/bin && \
    ln -sf "$(python -c 'import sys; print(sys.prefix)')/bin/jupyter" /opt/conda/bin/jupyter || true

COPY src ./src
COPY scripts ./scripts
COPY config ./config
COPY notebooks ./notebooks
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV TORCH_HOME=/app/.cache/torch

ENTRYPOINT ["/app/entrypoint.sh"]
"""

DCU_CODE_README = """\
# SCNet CNBE-MoE 代码（DCU 版）

- 基础镜像：DCU PyTorch 2.9.0 + Python 3.11 + DTK 26.04（平台基础镜像）
- 开发工具：JupyterLab / Jupyter
- 入口：`notebooks/CNBE_MoE_SCNet_Jupyter.ipynb`
- 冒烟：`python scripts/train_scnet.py --smoke --cnbe-paths /data/cnbe/zzjh_294.cnbe`
- 正式训练：`bash /app/startup.sh`
- 自定义镜像当前无法启用时，直接使用平台基础镜像，不要阻塞在镜像名上。
"""


def write_lf(path: Path, text: str) -> None:
    with path.open("w", newline="\n", encoding="utf-8") as f:
        f.write(text)


def main() -> int:
    base.main()
    if not SRC.exists():
        print("missing base package:", SRC)
        return 1

    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)

    write_lf(DST / "README_UPLOAD.md", DCU_README)
    write_lf(DST / "BOOTSTRAP.md", DCU_BOOTSTRAP)
    write_lf(DST / "SCNET_DCU_FORM_GUIDE.md", DCU_FORM_GUIDE)
    write_lf(DST / "code" / "Dockerfile", DCU_DOCKERFILE)
    write_lf(DST / "code" / "README.md", DCU_CODE_README)

    if BUNDLE_DST.exists():
        shutil.rmtree(BUNDLE_DST)
    shutil.copytree(BUNDLE_SRC, BUNDLE_DST)
    write_lf(BUNDLE_DST / "Dockerfile", DCU_DOCKERFILE)
    write_lf(BUNDLE_DST / "README.md", DCU_CODE_README)

    bundle_tar_path = EXP / "scnet_cnbe_moe_bundle_DCU.tar.gz"
    with tarfile.open(bundle_tar_path, "w:gz") as tf:
        tf.add(BUNDLE_DST, arcname="scnet_cnbe_moe_bundle_DCU")

    manifest_path = DST / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["package"] = "scnet_upload_package_DCU"
    manifest["variant"] = "dcu"
    manifest["image"] = "cnbe-moe-scnet-dcu:0.1"
    manifest["scnet_form"] = {
        "accelerator": "异构加速卡BW（DCU，64GB）",
        "dev_tool": "JupyterLab / Jupyter",
        "python": "3.11",
        "dtk": "26.04",
        "os": "Ubuntu 22.04",
        "base_image": "PyTorch/2.9.0/py3.11-Ubuntu22.04/dtk26.04",
        "note": "自定义镜像当前无法启用，使用平台基础镜像",
    }
    manifest.pop("scnet_form_a800", None)
    manifest["jupyter"] = "code/notebooks/CNBE_MoE_SCNet_Jupyter.ipynb"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    tar_path = EXP / "scnet_upload_package_DCU.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(DST, arcname="scnet_upload_package_DCU")

    print("dcu package:", DST)
    print("dcu tar:", tar_path, tar_path.stat().st_size)
    print("dcu bundle tar:", bundle_tar_path, bundle_tar_path.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
