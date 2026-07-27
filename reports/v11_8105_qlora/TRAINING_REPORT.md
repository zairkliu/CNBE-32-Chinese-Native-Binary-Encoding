# CNBE-32 8105 LLM Training Report

## Project Overview
This report documents the targeted LoRA fine-tuning of deepseek-r1:1.5b on the CNBE-32 8105 Chinese character encoding scheme.

## Environment
- Host OS: Windows 11 + WSL2 Ubuntu 26.04
- GPU: NVIDIA RTX 4060 Ti (8GB VRAM)
- Python: 3.12 (conda env), 3.14 (native)

## Infrastructure Setup
- Miniconda environment at /opt/miniconda/envs/cnbe
- PyTorch 2.6.0 with CUDA 12.4
- transformers 5.14.1 + peft 0.19.1 + bitsandbytes 0.50.0
- Model downloaded from hf-mirror.com

## Dataset
- Source: cnbe32.db (21,178 rows)
- Filtered: standard track, needs_encoding=0
- Unique characters: 7,602
- Training samples: 12,163 (chat format, bidirectional encode/decode)
- Validation: 1,520
- Test: 1,521 (293 unseen characters)

## Baseline (Zero-shot with ollama)
- Model: deepseek-r1:1.5b via ollama 0.32.4
- Tested on 50 random samples
- Accuracy: 0/50 = 0%
- The model had no prior knowledge of CNBE-32 encoding

## Fine-tuning Configuration
- Model: deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
- Quantization: 4-bit NF4 (QLoRA)
- LoRA rank: 16, alpha: 32, dropout: 0.05
- Target modules: all attention and MLP projections
- Training steps: 1000
- Batch size: 4, gradient accumulation: 2
- Learning rate: 2e-4, cosine schedule, 100 warmup steps
- Max sequence length: 512
- Optimizer: AdamW 8-bit
- Training time: 1 hour 32 minutes

## Training Results

### Loss Progression
| Step | Training Loss | Learning Rate | Gradient Norm |
|------|--------------|---------------|---------------|
| 10 | 8.654 | 1.8e-5 | 19.55 |
| 20 | 4.800 | 3.8e-5 | 8.263 |
| 30 | 1.002 | 5.8e-5 | 0.735 |
| 40 | 0.563 | 7.8e-5 | 0.454 |
| 50 | 0.318 | 9.8e-5 | 0.385 |
| 60 | 0.221 | 1.18e-4 | 0.232 |
| 70 | 0.182 | 1.38e-4 | 0.176 |
| 80 | 0.163 | 1.58e-4 | 0.133 |
| 90 | 0.152 | 1.78e-4 | 0.118 |
| 100 | 0.145 | 1.98e-4 | 0.126 |

### Final Training Metrics
- Total steps completed: 1000
- Total training time: 5,516 seconds (1h 32m)
- Final training loss: 0.2518
- Final Eval loss: 0.09179
- Train samples/sec: 1.45
- Trainable parameters: 18,464,768 (1.03%)
- Adapter size: 73.9 MB

### Evaluation Results (Post-Training)
- Test samples: 100
- Responses with valid hex codes: 47%
- Exact match accuracy: 0%
- Key finding: Model learned the format of CNBE-32 encoding but needs more training for exact mapping memorization

## Comparison with Previous Qwen3.5 Experiment
| Metric | Qwen3.5 0.8B (Previous) | DeepSeek-R1 1.5B (This) |
|--------|-------------------------|-------------------------|
| Training steps | 5000 | 1000 |
| Best loss | 0.6424 | 0.0918 (eval) |
| Data size | 25K/178K | 12K (8105 focused) |
| Hardware | GPU | RTX 4060 Ti |

## Conclusions

1. The model successfully learned the CNBE-32 encoding format (generating valid 0xXXXXXXXX style codes)
2. The loss reduction from 8.65 to 0.09 confirms effective learning
3. Exact encoding memorization requires more training steps and/or higher LoRA rank
4. The 8105-based training data provides a clean, standards-aligned foundation

## Next Steps

1. Run additional training (5000+ steps) with higher LoRA rank
2. Fix evaluation to use proper chat template matching training format
3. Evaluate field-level accuracy (radix, stroke count, structure type)
4. Test on unseen characters to measure generalization
5. Convert adapter to GGUF format for ollama deployment
