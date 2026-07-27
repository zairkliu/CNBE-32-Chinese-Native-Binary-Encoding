# v11: 8105 QLoRA Fine-tuning Experiment

## Overview
Fine-tune DeepSeek-R1-Distill-Qwen-1.5B on CNBE-32 8105 standardized character encodings using QLoRA (4-bit NF4).

## Training Parameters
| Parameter | Value |
|-----------|-------|
| Base model | deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B |
| Quantization | 4-bit NF4 (QLoRA) |
| LoRA rank/alpha | 16/32 |
| Training steps | 5,000 |
| Batch size | 4, grad_accum 2 |
| Learning rate | 2e-4, cosine decay |
| Warmup steps | 500 |
| Training data | 12,163 samples (7,602 unique chars) |
| Hardware | RTX 4060 Ti (8GB VRAM) |
| Training time | 5.8 hours |

## Results Summary

### Field-Level Evaluation (50 samples)
| Metric | Accuracy |
|--------|:--------:|
| Structure type (13 classes) | 66.0% |
| Stroke count (+-1) | 38.0% |
| Stroke count (+-2) | 54.0% |
| Radix (+-3) | 8.0% |
| Any field correct | 70.0% |

### Downstream Tasks
| Task | Result |
|------|:------:|
| Confusing character discrimination | 92.7% |
| Structure discrimination | 88.6% |
| Unseen character generalization | Similar to seen |
| Semantic clustering (guji) | ratio=0.99x (boundary) |

## Deployment
See `tools/deploy/` for:
- `merge_adapter.py` - Merge LoRA adapter
- `api_server.py` - FastAPI REST service
- `ocr_pipeline.py` - PDF → OCR → CNBE pipeline
- `Modelfile` - Ollama custom model
