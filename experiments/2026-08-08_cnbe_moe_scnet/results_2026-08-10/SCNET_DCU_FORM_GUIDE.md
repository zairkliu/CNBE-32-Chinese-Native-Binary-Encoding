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
