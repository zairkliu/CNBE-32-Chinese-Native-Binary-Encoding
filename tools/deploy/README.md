# CNBE-32 部署指南

## 概述

CNBE-32 提供三种部署方式：

1. **API Server**: FastAPI REST 服务（推荐，支持完整 LoRA 适配器）
2. **Ollama 自定义模型**: 轻量集成（无 LoRA，适合快速测试）
3. **OCR 管线**: 古籍 PDF → OCR → CNBE 编码 一体化

## 前提条件

### 硬件
- GPU: NVIDIA 8GB+ VRAM（推荐 RTX 3060/4060 及以上）
- RAM: 16GB+
- 存储: 10GB+

### 软件
- Windows 11 + WSL2 Ubuntu 24.04+
- Python 3.10+
- Ollama 0.13.0+（需安装 deepseek-ocr）
- NVIDIA CUDA 12.1+

## 方式一：API Server（推荐）

### 1. 合并 LoRA 适配器

将 5000 步训练的 LoRA 适配器合并到基础模型：

```bash
# 在 WSL 中执行
/opt/miniconda/envs/cnbe/bin/python /path/to/deploy/merge_adapter.py \
    --adapter /opt/cnbe-training/output/lora-adapter \
    --output /opt/cnbe-training/output/merged-model
```

### 2. 启动 API 服务

```bash
# 在 WSL 中执行
/opt/miniconda/envs/cnbe/bin/python /path/to/deploy/api_server.py \
    --model /opt/cnbe-training/output/merged-model
```

服务监听在 http://localhost:8000

### 3. API 调用示例

```python
import requests

# 编码单个汉字
resp = requests.post("http://localhost:8000/encode", json={"char": "好"})
print(resp.json())
# 输出: {"char":"好","response":"...","cnbe":{"radix":38,"stroke":6,"struct":1,"hex":"0x274C6010"}}

# 批量编码
resp = requests.post("http://localhost:8000/batch", json={"chars": ["好","的","人"]})
print(resp.json())

# 健康检查
resp = requests.get("http://localhost:8000/health")
print(resp.json())
```

## 方式二：Ollama 自定义模型

创建轻量级 ollama 模型（不包含 LoRA 适配器，但可直接 `ollama run`）：

```bash
ollama create cnbe-32 -f /path/to/deploy/Modelfile
ollama run cnbe-32
# >>> 编码汉字：好
```

## 方式三：OCR 管线（古籍处理）

整合 deepseek-ocr + CNBE-32 的一体化管线：

```bash
# 1. 启动 API 服务（方式一）
# 2. 运行 OCR 管线
python /path/to/deploy/ocr_pipeline.py "古籍PDF路径.pdf" 2 3 4
```

### MiMo V2.5 图形阅读补充（DeepSeek 视觉兜底）

DeepSeek 是文本模型，图片/古籍影像的阅读可交给小米 MiMo V2.5：

```bash
# 1. 安装并配置 deepseek-vision skill（密钥由 skill 保管，不写入仓库）
python /path/to/deploy/mimo_ocr.py "古籍页面.png"

# 2. OCR 管线切换 MiMo 引擎
python /path/to/deploy/ocr_pipeline.py "古籍PDF.pdf" --engine mimo
```

MiMo 适配器调用 `~/.codex/skills/deepseek-vision/scripts/mimo.py`，
按量付费时会在返回结果中附带 token 数与人民币费用。

## 5000 步训练

### 当前训练状态

训练运行在 WSL 的 conda 环境中（PID 1117）：
- 步数: 78/5000
- 速度: ~4.2 秒/步
- GPU: NVIDIA RTX 4060 Ti (8GB VRAM)
- 预计完成: 启动后约 6 小时

### 监控训练进度

```bash
# 查看最新进度
tail -5 /opt/cnbe-training/training_5k.log

# 查看 GPU 状态
wsl -d Ubuntu-26.04 -u root -- bash -c "nvidia-smi"

# 检查检查点
ls -la /opt/cnbe-training/output/checkpoint-*/
```

### 训练参数

| 参数 | 值 |
|------|-----|
| 基础模型 | deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B |
| 量化 | 4-bit NF4 (QLoRA) |
| LoRA rank | 16, alpha 32 |
| 训练步数 | 5000 |
| 批次大小 | 4, grad_accum 2 |
| 学习率 | 2e-4, cosine decay |
| 预热步数 | 500 |
| 优化器 | AdamW 8-bit |
| 训练数据 | 12,163 个 chat 格式样本 |
| 评估数据 | 1,520 个验证样本 |

## 实验验证结果摘要

### 位域分类评估（50 样本）
- 结构准确率: 66.0%
- 笔画 ±1: 38.0%
- 任一位域正确: 70.0%

### 形近字纠错（41 个混淆对）
- 区分率: 92.7%
- 结构区分: 88.6%
- 笔画区分: 61.0%

### 生僻字泛化
- 未见字符表现与已见字符几乎持平
- 编码知识是泛化的，非死记硬背

## 目录结构

```
outputs/
├── deploy/
│   ├── merge_adapter.py    # LoRA 合并脚本
│   ├── api_server.py       # API 服务
│   ├── ocr_pipeline.py     # OCR 管线
│   ├── Modelfile           # Ollama 模型定义
│   └── DEPLOY.md           # 本文件
├── 8105-training-data/     # 训练数据集
├── TRAINING_REPORT.md      # 完整训练报告
├── FIELD_EVAL_SUPPLEMENT.md# 位域评估补充
├── field_eval.json         # 位域评估结果
├── downstream_eval.json    # 下游任务评估
├── semantic_eval.json      # 语义相似度评估
├── guji_semantic_eval.json # 古籍语义验证
├── eval_results.json       # 旧评估结果
└── training.log            # 训练日志
```

## 移除 BOM 编码

因 Windows PowerShell 写入文件时添加了 UTF-8 BOM，在 Linux/WSL 中运行前需移除：

```bash
sed -i '1s/^\xEF\xBB\xBF//' *.py
```
