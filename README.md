# CNBE-32: Chinese Native Binary Encoding

A structured 32-bit representation of **97,686 CJK characters** for AI systems, hardware acceleration, and semantic processing.

[![License](https://img.shields.io/badge/License-MulanPSL2-blue.svg)]()
[![CJK Coverage](https://img.shields.io/badge/CJK-97%2C686-brightgreen)]()
[![Zero Collisions](https://img.shields.io/badge/Collisions-0-success)]()
[![RISC-V](https://img.shields.io/badge/RISC--V-5%20custom-orange)]()

---

## 1. Executive Summary

CNBE-32 (Chinese Native Binary Encoding) embeds Chinese character structural knowledge directly into 32-bit codes. Unlike traditional schemes (Unicode, GB 18030-2022) that treat characters as opaque identifiers, CNBE-32 encodes **radical, stroke count, structure type, and index** as distinct bit-fields.

| Metric | Value | Notes |
|---|---|---|
| Total characters | **97,686** | CJK Unified + Extensions A-I, 10 blocks |
| Encoding collisions | **0** | Verified across all characters |
| Kangxi radicals | **214/214** | 8-bit radical field, 100% coverage |
| Structure types | **9** | Single, Left-Right, Up-Down, 6 enclosures |
| Stroke range | **1-31** | 5-bit stroke count field |
| Code space utilization | **0.0023%** | Ample room for future expansion |
| GB 18030-2022 comparison | **+9,799 chars** | CNBE covers 11.1% more CJK characters |

---

## 2. Why CNBE?

Existing Chinese character encodings share a fundamental limitation: **they encode identity, not structure**. AI systems must learn character relationships from scratch. CNBE embeds structural information directly:

```
Bit: 31        24 23    19 18   15 14                 4 3  0
      +----------+--------+-------+--------------------+---+
      | Radical  | Stroke |Struct |    Index           |Ext|
      |  (8 bit) | (5 bit)|(4 bit)|    (11 bit)        |(4)|
      +----------+--------+-------+--------------------+---+
```

This enables:
- **Direct AI readability**: 99.94% accuracy in 3 epochs (vs 5.92% baseline)
- **Semantic search via encoding distance**: same-radical chars cluster naturally
- **Hardware-native processing**: 5 RISC-V custom instructions verified
- **Zero-shot understanding**: structural prior generalizes to unseen characters

---

## 3. GB 18030-2022 Comparison

| Dimension | GB 18030-2022 | CNBE-32 | Advantage |
|---|---|---|---|
| CJK Characters | 87,887 | **97,686** | **+9,799 (+11.1%)** |
| Kangxi Radicals | Not encoded | **214/214 (8-bit)** | CNBE explicit |
| Structure Types | None | **9 types (4-bit)** | CNBE unique |
| AI Readability | Must train | **99.94% in 3 epochs** | CNBE direct |
| Hardware Acceleration | None | **5 RISC-V instructions** | CNBE native |
| Semantic Search | Needs embedding model | **Encoding distance** | CNBE implicit |
| Confusable Resolution | No structural info | **Non-zero separation** | All 13 pairs resolved |

**Role**: CNBE-32 is a **semantic processing layer** complementing GB 18030-2022 (storage) for AI and hardware use.

---

## 4. Encoding Design

### Bit-Field Layout

| Field | Bits | Range | Description |
|---|---|---|---|
| Radical | 31:24 | 1-214 | Kangxi radical identifier |
| Stroke count | 23:19 | 1-31 | Total strokes |
| Structure type | 18:15 | 0-10 | 9 structure types |
| Character index | 14:4 | 0-2047 | Index within (radical,stroke,structure) group |
| Extension | 3:0 | 0-15 | Reserved (variant flags, etc.) |

### Strategy B Indexing (v3 Fix)

Characters in same (radical, stroke, structure) group sorted by stroke count + Unicode, ensuring:
- Predictable ordering within groups
- Non-zero separation for confusable pairs (已/巳, 未/末, 土/士)
- Stable encoding across expansion

### Coverage

| Unicode Block | Characters | % |
|---|---|---|
| CJK Unified (U+4E00-U+9FFF) | 20,992 | 21.5% |
| Extension A (U+3400-U+4DBF) | 6,592 | 6.7% |
| Extension B (U+20000-U+2A6DF) | 42,720 | 43.7% |
| Extension C-F | 17,606 | 18.0% |
| Extension G-I | 9,753 | 10.0% |

---

## 5. Experimental Results

### Radical Classification (E1)

| Model | Accuracy | Parameters | vs Baseline |
|---|---|---|---|
| Baseline (Traditional Embedding) | **5.92%** | 1,081,943 | - |
| CNBE Full (All Bit-Fields) | **99.94%** | 131,415 | **12.1%** of baseline |

### Language Modeling (B and B_v3)

| Model | Test Loss | Description |
|---|---|---|
| Baseline (Trained Embedding) | **2.200** | Full trainable |
| CNBE Static Only | 5.102 | Pure static encoding |
| CNBE Hybrid (Static + Trained) | **2.712** | **-46.8%** vs pure static |

**Finding**: "Augmentation over replacement" — CNBE works best as structural prior.

### Confusable Analysis (C_v3)

| Metric | Value |
|---|---|
| Pairs tested | 13 classic confusable pairs |
| Non-zero separation | **100%** (zero collisions resolved) |
| AUC (confusable detection) | **0.627** |

### Few-shot Learning (v4)

| Training Size | Baseline | CNBE |
|---|---|---|
| 10 samples/class | 0.74% | **99.89%** |
| 50 samples/class | 2.14% | **99.92%** |

---

## 6. RISC-V Custom Instructions

5 instructions in custom-0 opcode space:

| Instruction | Function | Cycles |
|---|---|---|
| cnhe.extract | Extract bit-field | 1 |
| cnhe.cmp | Compare codes (distance) | 2-3 |
| cnhe.map | Unicode to CNBE | 1-2 |
| cnhe.mv | Move/copy | 1 |
| cnhe.enc | Pack fields into CNBE | 1 |

**Simulation**: All 5 instructions verified in Ripes.

---

## 7. Quick Start

```python
from cnbe_encoder import CNBE32Encoder
encoder = CNBE32Encoder()
code = encoder.encode('\u6811')  # Output: 0x4B920000
features = encoder.extract(code)
print(f'Radical: {features["radical"]}, Strokes: {features["strokes"]}')

# Semantic distance
c1, c2 = encoder.encode('\u6797'), encoder.encode('\u6811')
print(f'Distance: {encoder.semantic_distance(c1, c2):.4e}')
```

---

## 8. Reproducibility

All experiments run on **CPU** (PyTorch 2.12+, no GPU needed):

```bash
pip install torch pandas scikit-learn openpyxl matplotlib tqdm
python CNBE_AI_verification_experiments.py
```

Suite: 11 experiments, ~15 min on modern CPU.

---

## 9. License

Mulan Permissive Software License v2 (MulanPSL-2.0).

---

## 10. Citation

```bibtex
@software{liu2026cnbe32,
  author = {Liu, Zhaoqi},
  title = {CNBE-32: Chinese Native Binary Encoding},
  year = {2026},
  url = {https://github.com/zairkliu/CNBE-32-Chinese-Native-Binary-Encoding}
}
```
