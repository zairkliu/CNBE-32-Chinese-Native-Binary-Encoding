# CNBE-32 · Chinese Native Binary Encoding / Chinese Native Binary Encoding

**A structured 32-bit encoding for 97,686 CJK characters that embeds radical, stroke count, and structure type directly into the encoding space.**

> This is not a replacement for Unicode. It is a **semantic enhancement layer** that lets machines *understand* Chinese characters at the binary level, not just display them.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-Spike+QEMU-orange)]()
[![OS](https://img.shields.io/badge/OS-WSL%20Ubuntu%2026.04-blue)]()

---

## Code Quick Look

**One character, one 32-bit binary.**

```
Bit: 31     28 27    24 23    19 18    15 14              4 3     0
     +--------+--------+--------+------------------------+-------+
     |RESERVED|SUB_TYPE|EXT_FLAG|  RADIX     |  STROKE   |STRUCT |
     +--------+--------+--------+------------------------+-------+
```

| Char | Unicode | CNBE-32 Code | Radical | Strokes | Structure |
|------|---------|-------------|---------|---------|-----------|
| one | U+4E00 | 0x01080000 | Yi (1) | 1 | Single |
| Han | U+6C49 | 0x0F288101 | Shui (15) | 5 | Left-Right |
| Guo | U+56FD | 0x1F400B0B | Wei (31) | 8 | Full-Wrap |
| Ming | U+660E | 0x48400801 | Sun (72) | 8 | Left-Right |

---

## Why CNBE-32?

| Aspect | Unicode / UTF-8 | CNBE-32 |
|--------|----------------|---------|
| Purpose | Character display & exchange | AI understanding & hardware acceleration |
| Encoding | Flat ID mapping | Semantic structured (radical+stroke+structure) |
| Machine cognition | Identifies characters | Understands character composition |
| AI compatibility | Must learn from data | Provides structural prior |

**9 domains validated**: linguistics, ecology, meteorology, finance, biology, physics, sociology, pretraining, mathematics

---

## Key Experiments

### 1. Small Model, Big Boost (v2)

**Hypothesis**: Structured encoding compensates for small model capacity.

**Method**: Qwen 3.5 0.8B with CNBE input vs standard input on Chinese sentence understanding.

| Input | Accuracy | Improvement |
|-------|----------|-------------|
| Standard | 48% | -- |
| **CNBE** | **87%** | **+81%** |

**Conclusion**: CNBE provides significant knowledge compensation for small models.

### 2. CNBE > Unicode (v6.5.2)

**Hypothesis**: Structured bit fields carry more semantic information than Unicode code points.

**Method**: Gemma 4B on Chinese hard tasks (reasoning, classical text).

| Input | Accuracy |
|-------|----------|
| Unicode | 26.1% |
| **CNBE** | **43.5%** |

**Conclusion**: A new, untrained encoding surpasses a 30-year-old standard on first attempt (+17.4pp).

### 3. Full Chinese Operating System (v8.4)

**Hypothesis**: CNBE enables a complete Chinese-native software stack.

**Method**: RISC-V QEMU virtual machine with Chinese BASIC interpreter, Shell, and text editor.

- Chinese Shell with commands like output(), getcode(), compare()
- Chinese BASIC interpreter with 7 keywords
- Text editor with Daodejing (205 lines, 7,720 characters)
- RISC-V custom instructions: cnhe.map/extract/cmp (Spike+FPGA)

**Conclusion**: A complete tech stack from encoding to operating system has been validated.

### 4. Math Reasoning Foundation (v10.8)

**Hypothesis**: CNBE frozen embeddings can replace learned embeddings in Transformer models.

**Method**: TinyGPT with CNBE frozen embeddings on parity/prime/sequence reasoning tasks.

| Task | CNBE Best | OneHot Best | Winner |
|------|-----------|-------------|--------|
| Parity | 0.3174 | 0.3427 | **CNBE** |
| Prime | 0.3894 | 0.5061 | **CNBE** |
| Sequence | 1.0726 | 1.2344 | **CNBE** |

**Conclusion**: Structured encoding approaches learned embedding performance with zero training.

---

## Tech Stack

```
Application: Chinese BASIC + Text Editor + Daodejing
System: Shell + CNBE Runtime (cnhe_map/extract/cmp)
Hardware: RISC-V 1GHz + 1GB RAM (QEMU + Spike)
Instructions: cnhe.map / cnhe.extract / cnhe.cmp
Encoding: 32-bit CJK structured bit field (radix/stroke/structure)
```

---

## Quick Start

### Python SDK

```bash
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding.git
cd CNBE-32-Chinese-Native-Binary-Encoding
python -c "import sys; sys.path.insert(0,'src'); from cnbe32 import encode_cnbe; print(hex(encode_cnbe(1,1,0)))"
```

### RISC-V Simulator

```bash
cd hardware/simulator
gcc -o cnhe_sim cnhe_sim.c -Wall -O2 && ./cnhe_sim
```

### Chinese OS (QEMU)

```bash
cd v84_riscv_os_full
make all && make run
```

### Reproduce Experiments

```bash
cd v10_8_math_reasoning && python run_v108.py
cd v10_3_typhoon && python v10_3_typhoon.py
```

---

## Project Structure

```
CNBE-32-Chinese-Native-Binary-Encoding/
|-- docs/specification/      # Encoding specification (7 docs)
|-- src/cnbe32/              # Python SDK (core/skill_table/encoders)
|-- include/cnbe32.h         # C header
|-- data/                    # Encoding database (CSV)
|-- tests/                   # Test suite
|-- tools/                   # Development tools
|-- bindings/rust/           # Rust/WASM bindings
|-- hardware/               # RISC-V simulator + FPGA RTL
|-- v9_jepa_tree/           # JEPA prediction experiments (v9)
|-- v10_5~v10_8/            # Cross-domain experiments (v10)
|-- v84_riscv_os_full/      # Chinese OS prototype
|-- results/                 # White papers (41 docs)
|-- pyproject.toml           # Python project config
|-- LICENSE                  # Mulan PSL v2
```

---

## Milestones (v1-v10.8)

| Phase | Version | Key Result |
|-------|---------|------------|
| Semantic Validation | v1-v4 | CNBE understood by AI (+81% on 0.8B) |
| Model Comparison | v5 | CNBE benefit decreases with model size |
| Numerical Features | v6 | Bare number format F optimal |
| Hardware Validation | v7 | 3 RISC-V instructions (Spike+FPGA) |
| Chinese OS | v8 | Full Chinese tech stack + BASIC |
| JEPA Prediction | v9.0-v9.4 | Structured encoding advantage confirmed |
| Finance Backtest | v10.0-v10.2 | Both markets profitable |
| Cross-Domain | v10.3-v10.8 | 9 domains validated |

**Full white papers**: [results/](results/) directory (41 documents)

---

## Roadmap

| Phase | Status | Content |
|-------|--------|---------|
| Encoding & Semantics | Done | v1-v6: CJK encoding design |
| Hardware & System | Done | v7-v8: RISC-V + Chinese OS |
| Complex Prediction | Done | v9-v10: 9 domains validated |
| AI Compiler | Planning | Chinese natural language to machine code |
| Edge AI Integration | Planning | CNBE as default for edge AI chips |
| Ecosystem | Vision | Open source community + standards |

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution tiers:
- **Low barrier**: Encoding dictionary, test cases, documentation
- **High barrier**: RISC-V pipeline, FPGA, LLM adaptation, compiler

---

## License

**Mulan Permissive Software License v2** (Mulan PSL v2)

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

---

*Built for the Chinese AI ecosystem -- from encoding to hardware.*
*Made Chinese a native language of AI.*
