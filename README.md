# CNBE-32: Chinese Native Binary Encoding

A structured 32-bit representation of **97,686 CJK characters** for AI systems, hardware acceleration, and semantic processing — embedding radical, stroke count, and structure type directly into the encoding space.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![Zero Collisions](https://img.shields.io/badge/Collisions-0-success)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-601x%20speedup-orange)]()

---

## 1. Executive Summary

CNBE-32 (Chinese Native Binary Encoding) embeds Chinese character structural knowledge directly into 32-bit codes. Unlike traditional schemes (Unicode, GB 18030-2022) that treat characters as opaque identifiers, CNBE-32 encodes **radical, stroke count, structure type, and index** as distinct bit-fields — making the encoding itself machine-readable for AI and hardware systems.

| Metric | Value | Notes |
|---|---|---|
| Total characters | **97,686** | CJK Unified + Extensions A-I, 10 Unicode blocks |
| Encoding collisions | **0** | Strategy B verified across all characters |
| Kangxi radicals | **214/214** | 8-bit radical field, 100% coverage (Unihan verified) |
| Structure types | **9+** | Single, Left-Right, Up-Down, enclosures, Pin-Structure |
| Stroke range | **1-31** | 5-bit stroke count field (99.82% Unihan verified) |
| Code space utilization | **0.0023%** | Ample room for future expansion |
| Unihan radical verification | **100%** | 93,672 chars checked against Unicode database |
| GB 18030-2022 comparison | **+9,799 chars** | CNBE covers 11.1% more CJK |

---

## 2. Experiment Results

### 2.1 Semantic Clustering (Separation Ratio)

| Dataset | CNBE-32 | Unicode Baseline | Improvement |
|---|---|---|---|
| 97,686 CJK (v3) | **1.6x** | 1.15x | **+39%** |
| 97,686 CJK (v4) | 1.1x | 1.15x | Modern-first tradeoff |
| 8,105 core chars | **543x** | — | Practical AI range |

### 2.2 Few-shot Classification (214 Radicals)

| Training | v3 Accuracy | v4 Accuracy | Random Baseline |
|---|---|---|---|
| 5-shot | **63.01%** | **66.67%** | <1% |
| 10-shot | **75.24%** | **79.11%** | <1% |
| 20-shot | **84.35%** | **85.25%** | <1% |

### 2.3 Confusable Character Analysis

All 12 classic confusable pairs (已/巳, 未/末, 土/士, 天/夫, etc.) have **non-zero encoding distance**. Strategy B indexing ensures minimum distance of 11 (1 index step × 11 weight) for same-group pairs.

### 2.4 RISC-V Instruction Verification

| Metric | Value |
|---|---|
| Speedup (Python vs HW sim) | **601x** |
| SW path (10K chars × 10K loops) | 72,124 ms |
| HW path @2.5GHz | 120 ms |
| CNHE.MAP ROM size | 572 KB (fits L2 cache) |
| Cross-compilation | Verified (riscv64-linux-gnu-gcc) |
| QEMU execution | Functional correctness PASS |

### 2.5 Time Dimension (v4 Extension Bits)

| Test | Accuracy | Notes |
|---|---|---|
| Ext bit only (Modern vs Ancient) | **100%** | v4 extension bit design verified |
| Full code (24 bits) | 64.02% | Stroke+radial carry time info |

---

## 3. Encoding Design

### Bit-Field Layout (32-bit)

`
[31:24] Radical (8-bit, 1-214)
[23:19] Stroke count (5-bit, 1-31)
[18:15] Structure type (4-bit, 0-10)
[14:4]  Index (11-bit, 0-2047)
[3:0]   Extension (4-bit, time layer / reserved)
`

### Version Comparison

| Feature | v3.0 | v4.0 |
|---|---|---|
| Sorting | Radical → Stroke → Unicode | Radical → Modern-first → Unicode |
| Modern chars | Not marked | 8,105 (通用规范汉字表) |
| Extension bits | Reserved | Time layer (Modern=0, Ancient=1) |
| Pin-Structure | Not used | 37 chars (品, 森, 鑫, etc.) |
| Structure IDs | 0-10 (v3 mapping) | 0-10 (remapped for 3D world model) |
| Clustering | **1.6x** (better) | 1.1x |
| Few-shot (5-shot) | 63.01% | **66.67%** (better) |

### 8105 Core Set Approach

The 8,105 characters from 《通用规范汉字表》cover **99.997%** of modern Chinese publications. On this subset, CNBE-32 achieves **543x** separation ratio. Recommended strategy: "Core set (8105) + Extension set (97,686)" dual-layer encoding.

---

## 4. RISC-V Custom Instructions

Five instructions defined in custom-0 opcode space:

| Instruction | Function | Cycles | Status |
|---|---|---|---|
| cnhe.extract | Extract bit-field | 1 | Simulated |
| cnhe.cmp | Compare codes | 2-3 | Simulated |
| cnhe.map | Unicode to CNBE | 1-2 | 572 KB ROM |
| cnhe.mv | Move/copy | 1 | Simulated |
| cnhe.enc | Encode character | 1 | Simulated |

All 5 instructions verified via Python cycle-accurate simulation + QEMU execution.

---

## 5. Quick Start

`python
from cnbe_encoder import CNBE32Encoder
encoder = CNBE32Encoder()

# Encode a character
code = encoder.encode('树')
print(f"CNBE Code: 0x{code:08X}")  # 0x4B920000

# Extract structural features
features = encoder.extract(code)
print(f"Radical: {features['radical']}, Strokes: {features['strokes']}")

# Semantic distance
c1, c2 = encoder.encode('林'), encoder.encode('树')
print(f"Distance: {encoder.semantic_distance(c1, c2):.4e}")
`

---

## 6. Project Resources

| Resource | File | Format |
|---|---|---|
| **v3 Full Encoding Catalog** | data/CNBE_编码目录_修复版_v3.xlsx | XLSX (6.1 MB) |
| **v4_3D World Model Catalog** | data/CNBE_编码目录_修复版_v4.xlsx | XLSX (10 MB) |
| **v4 Fixed (Structure Corrected)** | data/CNBE_编码目录_修复版_v4_fixed.xlsx | XLSX (8.5 MB) |
| **v3 White Paper (Chinese)** | data/CNBE-32_v3_全量验证实验白皮书.docx | DOCX (40 KB) |
| **v3 White Paper (English)** | data/CNBE_White_Paper_v3_fixed_GB.docx | DOCX (1.5 MB) |
| **v4 3D World White Paper** | data/CNBE-32_v4_三维世界模型白皮书.docx | DOCX (36 KB) |
| **Experiment Report** | data/CNBE_大规模验证实验报告.docx | DOCX (37 KB) |
| **Encoder Library** | src/CNBE编码器.py | Python |
| **AI Experiment Scripts** | experiments/ | Python |
| **RISC-V Simulator** | hardware/cnbe_riscv_sim.py | Python |
| **RISC-V Instruction Macros** | hardware/cnbe_macros.h | C Header |
| **RISC-V Test Program** | hardware/test_cnbe_full.c | C |
| **Spike Integration** | hardware/spike-patches/ | C/Patch |

---

## 7. Reproducibility

All experiments run on **CPU only** (no GPU needed):

`ash
pip install torch pandas scikit-learn openpyxl numpy
python experiments/CNBE_AI验证实验.py
`

For RISC-V verification (requires WSL2 or Linux):
`ash
sudo apt install gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu spike qemu-user
cd hardware
riscv64-linux-gnu-gcc -O2 -march=rv64imafdc -static test_cnbe_full.c -o test_cnbe_full.elf
qemu-riscv64 test_cnbe_full.elf
`

---

## 8. License

This project is licensed under the **Mulan Permissive Software License v2** (Mulan PSL v2).  

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)](http://license.coscl.org.cn/MulanPSL2)

See [LICENSE](LICENSE) for details.

---

## 9. Citation

`ibtex
@software{liu2026cnbe32,
  author = {Liu, Zhaoqi},
  title = {CNBE-32: Chinese Native Binary Encoding},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
`

---

**Related**: [Technical White Paper (v3)](data/CNBE-32_v3_全量验证实验白皮书.docx) | [3D World Model Paper (v4)](data/CNBE-32_v4_三维世界模型白皮书.docx) | [Experiment Report](data/CNBE_大规模验证实验报告.docx)

*Built for the Chinese AI ecosystem — from encoding to hardware. Licensed under Mulan PSL v2.*
