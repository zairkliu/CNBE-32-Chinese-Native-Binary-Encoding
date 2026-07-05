---
name: cnbe32-experiment
description: "Reproduce and extend CNBE-32 experiments (v1-v7) using local LLMs via Ollama, supporting DeepSeek, Qwen, Gemma, and OPT models. Use when the task involves: (1) encoding Chinese text with CNBE structural codes, (2) running controlled experiments comparing LLM understanding with and without CNBE annotation, (3) reproducing published white-paper results on sentence comprehension, long-text understanding, numerical format optimization, or hard-task analysis, (4) evaluating CNBE vs Unicode numerical encoding, (5) testing model size vs encoding benefit, or (6) preparing RISC-V cross-compilation tests."
---

# CNBE-32 Experiment Reproduction

Reproduce experiments from the [CNBE-32](https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding) project using local LLMs via Ollama. Supports DeepSeek, Qwen, Gemma, and OPT models.

## Prerequisites

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
# or on Windows: download from https://ollama.com/download

# Pull at least one model
ollama pull qwen3.5:0.8b
ollama pull gemma4:4b    # recommended for CNBE vs Unicode comparison
ollama pull deepseek-r1:8b
```

- Python 3.8+ with `numpy` (`pip install numpy`)
- Repo root: `git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git`
- Ollama running: `ollama serve`

## Quick Start

```bash
cd <repo-root>/skill/scripts

# List available experiments and models
python experiment.py list

# Run v2 sentence understanding
python experiment.py v2 --model qwen3.5:0.8b

# Run with a larger model
python experiment.py v4 --model gemma4:4b --samples 5

# Run CNBE vs Unicode comparison
python experiment.py v6 --model gemma4:4b --format F

# Dry run to inspect prompts (no API calls)
python experiment.py v65 --model deepseek-r1:8b --dry-run
```

## Experiments

| ID | Task | Measures | Published Result |
|:--:|------|----------|:----------------:|
| v2 | Sentence understanding (10-100 sentences) | Effective rate improvement | 48% -> 87% (0.8B, +81%) |
| v4 | Long text comprehension (20 paragraphs) | Summary quality | 91% -> 100% (0.8B, +9%) |
| v6 | CNBE vs Unicode numerical format | Character recognition | CNBE +17.4pp (Gemma 4B) |
| v65 | Hard tasks (rare chars, chemistry) | Recognition accuracy | CNBE > baseline |

## Scripts

- `scripts/encode.py` — Core CNBE encoder. Encodes text in formats A/C/D/F using the skill table at `riscv/skill_table/skill_table_8105.npy`. Can be used standalone: `python encode.py "你好" --format C`
- `scripts/experiment.py` — Unified runner for all v2/v4/v6/v65 experiments. See `python experiment.py list`

## Model Size Effect

CNBE benefit decreases with model size (verified across 7 models):

| Size | CNBE Benefit | Recommended Use |
|:----:|:------------:|:----------------:|
| < 1B | +50-81% | Edge devices, education |
| 1-7B | +9-17% | Mobile deployment |
| > 7B | ~0% | Large models self-sufficient |

## RISC-V (v7) Reproduction

The C-language skill table implementation is at `riscv/src/`. Cross-compile for RISC-V:

```bash
cd <repo-root>/riscv/src
riscv64-linux-gnu-gcc -O2 test_lookup.c -o test_lookup_riscv
qemu-riscv64 ./test_lookup_riscv

# Verilog simulation
iverilog -o cnhe_tb cnhe_core.v tb_cnhe.v
vvp cnhe_tb
```

See `riscv/README.md` for full v7 details.

## Interpreting Results

The experiment runner outputs a summary table with control vs CNBE valid-response counts and percentage improvement. For detailed analysis, the scripts also save per-sample response JSON files.

Compare results against published white papers under `llm_experiments/`. Marginal gains (<5%) on models >7B are expected and consistent with the documented benefit-decay trend.

## References

- `references/models.md` — Ollama setup, model pulling, troubleshooting
- `references/experiments.md` — Full experiment design docs from v1-v7
- `../llm_experiments/` — Published white papers (v1-v6)
- `../riscv/` — Hardware implementation docs (v7)
- `../docs/` — System architecture and encoding specification
