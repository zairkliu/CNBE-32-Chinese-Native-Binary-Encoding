# CNBE-32: Chinese Native Binary Encoding / Chinese Native Binary Encoding

A structured 32-bit representation of 97,686 CJK characters for AI, hardware, and semantic processing.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

---

## CNBE-32 Encoding Quick Look

One 32-bit code per Chinese character:

| Char | Unicode | Code (hex) | Radical | Strokes | Structure |
|------|---------|-----------|---------|---------|----------|
| one | U+4E00 | 0x01080000 | Yi(1) | 1 | Single |
| Han | U+6C49 | 0x0F288101 | Shui(15) | 5 | Left-Right |
| Guo | U+56FD | 0x1F400B0B | Wei(31) | 8 | Full-Wrap |
| Ming | U+660E | 0x48400801 | Sun(72) | 8 | Left-Right |

Designed for machine understanding, not just display.

---

## One Sentence

CNBE-32 is a semantic enhancement layer on top of Unicode: 32-bit fixed-width, CPU-native, 9 domains validated.

---

## Key Experiments

1. Small Model Boost (v2): CNBE +81% on Qwen 0.8B (87% vs 48%)
2. CNBE > Unicode (v6.5.2): +17.4pp on Gemma 4B
3. Typhoon Prediction (v10.3): CNBE 174km vs Raw 216km (-19%)
4. Math Reasoning (v10.8): CNBE frozen embedding > OneHot on all tasks

---

## Tech Stack

Application Layer: Chinese BASIC + Text Editor
System Layer: Shell + CNBE Runtime
Hardware Layer: RISC-V 1GHz + QEMU
Instruction Layer: cnhe.map/extract/cmp (Spike+FPGA)
Encoding Layer: 32-bit structured bit field

---

## Milestones (v1-v10.8)

v1-v4: Semantic Validation - CNBE understood by AI (+81%)
v7: Hardware - 3 RISC-V custom instructions
v8: Chinese OS - Full Chinese tech stack
v9.0-v9.4: JEPA Prediction - Structured encoding advantage
v10.0-v10.2: Finance Backtest - Positive returns
v10.3-v10.8: Cross-Domain - 9 domains validated

---

## Quick Start

pip install numpy torch scikit-learn
git clone https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding
python -c "from cnbe32 import encode_cnbe; print(hex(encode_cnbe(1,1,0)))"

---

## License: Mulan PSL v2

https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding
