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

| Metric | Value |
|--------|-------|
| Base Model | Qwen3.5-0.8B (752M params) |
| LoRA Rank | r=32, alpha=64 |
| Training Steps | 500 (~22 min) |
| Final Loss | 0.7524 |
| GPU Memory | 1.5 GB / 8 GB |
| Training Samples | 1,000 (mini subset of 178K full dataset) |

## Notes

- Training data (178K CNBE-32 encoding samples) is **not included** in this repo due to size
- Full whitepaper with methodology, data distribution, and limitations: see CNBE32_Qwen3.5_Training_Whitepaper.md
- See the main repo [README.md](../README.md) for the complete CNBE-32 project overview
