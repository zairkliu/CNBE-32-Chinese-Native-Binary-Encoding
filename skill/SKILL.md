---
name: cnbe32-experiment
description: "Reproduce and extend CNBE-32 experiments (v1-v8.1) using local LLMs via Ollama, supporting DeepSeek, Qwen, Gemma, and OPT models. Use when the task involves: (1) encoding Chinese text with CNBE structural codes, (2) running controlled experiments comparing LLM understanding with and without CNBE annotation, (3) reproducing published white-paper results across all v1-v8 experiments, (4) evaluating CNBE vs Unicode numerical encoding, (5) testing model size vs encoding benefit, (6) preparing RISC-V cross-compilation tests, or (7) compiling Chinese source code to CNBE-enhanced RISC-V assembly."
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

| ID | Task | Core Finding | Key Data | White Paper |
|:--:|------|-------------|:--------:|:-----------:|
| v1 | Single char validation | CNBE zero-shot understood | 200 chars, 100% | llm_experiments/v1_v4_validation/ |
| v2 | Sentence understanding | CNBE improves comprehension | 48%->87%(+81%) | llm_experiments/v1_v4_validation/ |
| v3 | Format optimization | Format A (per-char annotation) best | 87% eff, 9% distr | llm_experiments/v1_v4_validation/ |
| v4 | Long text (On Protracted War) | CNBE helps full-paper understanding | 91%->100%(+9.1%) | llm_experiments/v1_v4_validation/ |
| v5 | 7-model comparison | CNBE benefit decreases with model size | 0.8B:+81% 8B:~0% | llm_experiments/v5_model_comparison/ |
| v6 | Numerical format + Unicode compare | Format F optimal; CNBE>Unicode on Gemma | +17.4pp(Gemma4B) | llm_experiments/v6_numerical_features/ |
| v7.0-v7.2 | RISC-V hardware (C->Spike->FPGA) | x86:0.8ns QEMU:2.5ns FPGA:1cycle | 3 custom insns | riscv/ |
| v7.3 | Feature space co-validation | CNBE 3D features parsable by ML | 2/3 hard tasks win | experiments/v73/ |
| v8.0 | Chinese programming compiler | Chinese -> RISC-V + CNBE mapping | test_loop=34insns | v8_chinese_programming/ |
| v8.1 | Complete compiler + Skill table | All 4 tests compile; runtime integrated | test_struct=48insns | v8_chinese_programming/ |

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

See `riscv/README.md` and `riscv/v7.*/` white papers for details.

## Chinese Programming Compiler (v8)

Compile Chinese source code to CNBE-enhanced RISC-V assembly:

```bash
cd <repo-root>/v8_chinese_programming
python src/compiler.py tests/test_loop.cnbe -o output/test_loop.s
```

### Test Programs

| Program | Description | Status |
|---------|-------------|:------:|
| test_loop.cnbe | Loop sum 0+..+9=45 | 34 RISC-V insns |
| test_struct.cnbe | CNBE radical/structure compare | 48 RISC-V insns |
| test_cluster.cnbe | CNBE semantic distance | 27 RISC-V insns |
| test_array.cnbe | Array sum 0+1+2+3+4=10 | 34 RISC-V insns |

### CNBE Semantic Functions

| Chinese | RISC-V | Meaning |
|---------|:------:|---------|
| 取编码(char) | cnhe.map | Unicode -> CNBE code |
| 取部首(code) | cnhe.extract f=0 | Extract radical |
| 取笔画(code) | cnhe.extract f=1 | Extract stroke count |
| 取结构(code) | cnhe.extract f=2 | Extract structure type |
| 比较(c1,c2) | cnhe.cmp | Weighted Hamming distance |

### RISC-V Toolchain (for full verification)

```bash
# Cross-compile assembled output with runtime
riscv64-linux-gnu-gcc -O2 output/test_loop.s \
    src/runtime/cnbe_runtime.c -o output/test_loop.elf
qemu-riscv64 output/test_loop.elf
```

See `v8_chinese_programming/README.md` and white papers for details.

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
- `references/experiments.md` — Full experiment design docs (v1-v8.1)
- `../llm_experiments/` — Published white papers (v1-v6)
- `../riscv/` — Hardware implementation docs (v7)
- `../experiments/v73/` — v7.3 feature space validation
- `../v8_chinese_programming/` — Chinese programming compiler (v8)
- `../docs/` — System architecture and encoding specification
