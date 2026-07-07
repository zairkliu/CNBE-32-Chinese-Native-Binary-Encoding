# CNBE-32 LLM Training Demo

This directory contains the **Qwen3.5-0.8B LoRA fine-tuning demo** for CNBE-32 encoding knowledge injection.

## Contents

| File | Description |
|------|-------------|
| `CNBE32_Qwen3.5_Training_Whitepaper.md` | Complete experiment whitepaper (methodology, results, analysis) |
| `training_log.txt` | Raw training log from 500-step Lite run |
| `scripts/train_final.py` | LoRA fine-tuning script (CUDA compatible) |
| `scripts/serve_cnbe_model.py` | Gradio web interface + FastAPI server for the merged model |
| `scripts/do_merge.py` | Script to merge LoRA adapter weights into the base model |

## Quick Start

```bash
# 1. Install dependencies
pip install torch transformers peft accelerate gradio fastapi uvicorn

# 2. Run training (500 steps, ~22 min on RTX 4060 Ti)
python scripts/train_final.py

# 3. Merge LoRA weights into base model
python scripts/do_merge.py

# 4. Start Gradio chat interface
python scripts/serve_cnbe_model.py --port 7860 --gradio-only
# Open http://localhost:7860 in your browser
```

## Key Results
## 5000-Step Training Results

| Metric | 500 Steps (Lite) | **5000 Steps (Full)** | Improvement |
|--------|:-----------------:|:---------------------:|:-----------:|
| Training Data | 1,000 mini samples | **25,000 diverse samples** | 25x more |
| Data Format | Concatenated (instruction+output) | **Chat Template (system/user/assistant)** | Cleaner, no artifacts |
| Best Loss | 0.7524 | **0.6424** | **-14.6%** |
| Final Loss | 0.7524 | 0.7616 | Comparable |
| Learning Rate | Fixed 2e-4 | **Cosine 1e-4 → 1e-5** | Better convergence |
| Training Time | 22 min | **4.14 hours** | Complete convergence |
| Checkpoints | 5 | **11** | Better recovery |
| Augmentation Artifacts | **Present** ("这是数据增强后的CNBE-32训练样本") | **Eliminated** | Clean output |

The 5000-step training used the full 178K pre-formatted dataset, taking a diverse 25K sample subset. The chat template format eliminated the repetition artifacts seen in the Lite training.

### Loss Progression

```
Step      | Loss  | LR        
----------|-------|-----------
     50   | 2.054 | 0.000100  
    500   | 1.007 | 0.000099  (Checkpoint 1)
   1000   | 0.928 | 0.000094  (Checkpoint 2)
   1500   | 0.869 | 0.000085  (Checkpoint 3)
   2000   | 0.772 | 0.000072  (Checkpoint 4) **Best so far**
   2500   | 0.731 | 0.000056  (Checkpoint 5) **Below 0.75!**
   3000   | 0.735 | 0.000043  (Checkpoint 6)
   3500   | 0.677 | 0.000030  (Checkpoint 7) **Best 50-step avg**
   4000   | 0.728 | 0.000019  (Checkpoint 8)
   4500   | 0.807 | 0.000012  (Checkpoint 9)
   5000   | 0.762 | 0.000010  (Final) **Cosine decay complete**
```

### Key Files

| File | Description |
|------|-------------|
| `training_5k_log.txt` | Full 5000-step training log |
| `scripts/train_5k.py` | 5000-step training script (cosine LR, 25K data) |
## Notes

- Training data (178K CNBE-32 encoding samples) is **not included** in this repo due to size
- Full whitepaper with methodology, data distribution, and limitations: see CNBE32_Qwen3.5_Training_Whitepaper.md
- See the main repo [README.md](../README.md) for the complete CNBE-32 project overview

