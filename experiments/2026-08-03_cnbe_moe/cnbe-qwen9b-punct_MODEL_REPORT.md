# cnbe-qwen9b-punct 模型交付报告

## 1. 模型概要

| 项目 | 内容 |
|---|---|
| 基座 | Qwen/Qwen3.5-9B（Ollama 中对应 `qwen3.5:9b`） |
| 训练方式 | QLoRA 4-bit NF4（r=16, alpha=32） |
| 训练数据 | 今日古籍句读 train 265 条 + eval 30 条 + CNBE 防遗忘 500 条/轮 |
| 训练步数 | 120 步（约 1.25 轮混合数据） |
| 训练 Eval Loss | 1.823（冒烟 2 步时为 2.465） |
| 输出格式 | 纯文本续写，无 think/chat 模板 |

## 2. 训练数据

- 句读训练：`guji-platform/llm/data/train.jsonl`（265 条，80-150 字短样本）
- 句读验证：`guji-platform/llm/data/eval.jsonl`（30 条）
- CNBE 防遗忘混合：`C:/Users/zairk/cnbe-training1/data/cnbe_train.jsonl`

## 3. 产物清单

| 产物 | 路径 | 大小 |
|---|---|---:|
| LoRA adapter | `D:\models\cnbe-qwen9b-punct-v1\adapter` | ~116 MB |
| 合并 HF 模型 | `D:\models\Qwen3.5-9B-merged-punct` | ~17.9 GB |
| F16 GGUF | `D:\models\gguf\cnbe-qwen9b-punct-f16.gguf` | ~17.9 GB |
| Q4_K_M GGUF | `D:\models\gguf\cnbe-qwen9b-punct-q4_k_m.gguf` | ~5.6 GB |
| Ollama 模型 | `cnbe-qwen9b-punct:latest` | 5.6 GB |

## 4. 句读评估（30 条 eval）

Ollama 本地评估（`cnbe-qwen9b-punct:latest`，`think:false`）：

| 指标 | 值 |
|---|---:|
| Precision | 0.7954 |
| Recall | 0.7519 |
| F1 | 0.7665 |

评估明细：`guji-platform/outputs/qwen9b_ollama_punct_eval.json`

## 5. 使用方式

```bash
ollama run cnbe-qwen9b-punct
```

或 REST API：

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "cnbe-qwen9b-punct:latest",
  "prompt": "古籍句读：\n<无标点古文>\n答案：\n",
  "stream": false,
  "options": {"temperature": 0.0, "num_ctx": 2048}
}'
```

## 6. 打包

`outputs/cnbe-qwen9b-punct_v1.0.zip` 包含 adapter、Q4_K_M GGUF、Modelfile、
评估报告与训练日志。
