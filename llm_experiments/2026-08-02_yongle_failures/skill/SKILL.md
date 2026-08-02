---
name: guji-punctuation-14b-training
description: 基于今日失败教训训练 DeepSeek-R1-Distill-Qwen-14B 古籍句读模型。当用户要求“训练14B句读”“古籍断句模型”“失败教训训练”“句读微调”或继续推进 CNBE 古籍 OCR 项目的 LLM 训练时使用。
---

# 古籍句读 14B 训练 Skill

## 背景（今日失败教训）

2026-08-02 实测证明：

- 1.5B 无法完成 400-500 字整页 OCR 转录（v3/v4 精确匹配约 20-21%）。
- OCR 只做定位与兜底：PaddleOCR 覆盖率 18.05%，DeepSeek-OCR v1 去重后 37.76%。
- 页面锚定真值库命中 100%；识典公开全文与人工校订逐字一致 100%。
- 规则句读基线 F1=0.0933，模型目标 F1 >= 0.90。
- 原 CNBE 模型：Qwen3.5-0.8B + 178,034 条样本、5,000 步、覆盖 8,105 字。

详细证据见：
`guji-platform/docs/FAILURE_SUMMARY_2026-08-02.md`
`guji-platform/docs/WHITEPAPER_2026-08-02_14B.md`

## 核心原则

1. 模型只接收真值库纯文本，绝不接收 OCR 脏文本。
2. 只做句读与分段，不做整页转录、不做排版重排。
3. 关闭思考模式（think），使用纯文本续写格式。
4. 样本控制在 80-150 字，防止长文本退化。
5. 14B 与 0.8B 架构不兼容，采用知识迁移：混入原 CNBE 178K 数据防遗忘。
6. 若同架构有原 CNBE 适配器，先合并再挂新 LoRA。

## 工作流

### 1. 准备句读数据

```bash
cd guji-platform
python scripts/prepare_punctuation_dataset.py \
  --library ../work/yongle_821_review/pipeline/ground_truth_library.json \
  --chapter-sources ../work/yongle_821_review/pipeline/chapter_sources.json \
  --out-dir llm/data
```

### 2. 检查真值

```bash
python run.py verify
python scripts/eval_punctuator.py
```

### 3. 训练 14B

```bash
python llm/train_punctuator.py \
  --config llm/qlora_config_14b.yaml \
  --output-dir llm/outputs/cnbe-punct-14b-v1
```

首次运行先下载权重：

```bash
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-R1-Distill-Qwen-14B', trust_remote_code=True)"
```

### 4. 验证

```bash
python scripts/eval_punctuator.py --out llm/data/punctuator_eval_14b.json
```

要求：句读 F1 >= 0.90；CNBE 8,105 字抽测准确率不回退。

### 5. 接入管线

```python
from app.llm import HFQLoRAPunctuator
from app.llm.yongle_llm_pipeline import Yongle_LLM_Pipeline

punctuator = HFQLoRAPunctuator(
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
    adapter_path="llm/outputs/cnbe-punct-14b-v1",
)
pipe = Yongle_LLM_Pipeline(library, punctuator=punctuator)
```

### 6. 封装 GGUF

合并 LoRA 后使用 `cnbe-training1/scripts/convert_to_gguf.py` 转 GGUF，
再写 Modelfile 注册 Ollama 模型名 `cnbe-punct-14b`。

## 失败禁止事项

- 禁止用任何规模的 LLM 做整页 OCR 转录。
- 禁止把 PaddleOCR 输出直接喂给句读模型。
- 禁止聊天模板/思考模式训练。
- 禁止整页样本（>300 字）作为训练样本。
- 禁止从基础模型重训而丢掉 CNBE 知识（必须混入原 CNBE 数据）。
