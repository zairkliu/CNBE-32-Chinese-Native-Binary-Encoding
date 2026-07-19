<p align="center">
  <strong>CNBE-32</strong><br>
  Chinese Native Binary Encoding
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./README_ZH.md">简体中文</a> ·
  <a href="./README_EN.md">English mirror</a>
</p>

<p align="center">
  <img alt="Project status" src="https://img.shields.io/badge/status-research%20prototype-orange">
  <img alt="Python SDK" src="https://img.shields.io/badge/Python%20SDK-stable%20baseline-blue">
  <a href="https://pypi.org/project/cnbe32/"><img alt="PyPI" src="https://img.shields.io/pypi/v/cnbe32.svg"></a>
  <img alt="Basic CJK DB" src="https://img.shields.io/badge/Basic%20CJK-20%2C902%20entries-green">
  <img alt="Extended scope" src="https://img.shields.io/badge/97%2C686-experimental%20target-lightgrey">
</p>

A 32-bit structural fingerprint for CJK characters — built for people who wonder what Chinese text would look like if it were designed closer to the metal.

> **CNBE-32 is a research prototype.**
> The packaged Python SDK currently targets **20,902 Basic CJK** entries.
> The broader **97,686 CJK** figure is an intended / experimental extended scope, not current packaged SDK coverage.
> The latest published package is **cnbe32 1.0.4**, matching the GitHub `v1.0.4` release checkpoint.

## Current standards restart

CNBE is being reorganized around a stricter standards-aligned workflow.

The **8105 common standardized Chinese character table** is now the national-standard core for the rebuild. Existing CNBE rows are treated as legacy/current runtime data until they pass the renewed evidence gates. The 20,902-row Agent pre-encoding pool is a project candidate pool, and the 97,686-row full catalog remains an extended research target.

The restart target is to rebuild CNBE as a national-language-standard-aligned encoding project: the Agent performs controlled Hanzi structure work, every promoted row carries evidence and review state, and the repository separates runtime code, evidence, reports, historical experiments, and reproducible research outputs.

Current confirmed state:

- release checkpoint: `v1.0.4`
- published Python package: `cnbe32==1.0.4`
- 8105 baseline rows: `8105`
- current CNBE rows inside 8105 scope: `7829`
- missing current CNBE rows inside 8105 scope: `276`
- human-approved 8105 Agent structure baseline: `8105 / 8105`
- runtime CNBE32 rows patched from the approved 8105 dry run: `6712`
- additional conservative standardized runtime repairs: `598`
- total patched 8105 runtime rows after repair: `7310`
- force-approved rows retained for later insertion/radical strategy: `795`
- runtime JSON and SQLite databases rebuilt from the approved 20,902-row source

Governance documents:

- [CNBE 8105 Encoding Governance](./docs/CNBE8105_ENCODING_GOVERNANCE.md)
- [CNBE Reproducible Agent Workflow](./docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md)
- [CNBE Version Governance](./docs/CNBE_VERSION_GOVERNANCE.md)
- [Repository Structure](./docs/REPOSITORY_STRUCTURE.md)
- [CNBE 8105 Encoding Comparison](./evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md)
- [CNBE 8105 Runtime Promotion](./reports/8105_CNBE32_RUNTIME_PROMOTION.md)
- [CNBE 8105 Standardized Runtime Repair](./reports/8105_STANDARDIZED_RUNTIME_REPAIR.md)

Earlier AI-generated catalog fields are now treated as a historical test
baseline only. They remain useful for regression localization, but they are not
used as authority for structure, radical, stroke, teaching, or research claims.

## Project rationale

CNBE-32 is useful only if the encoding process is stricter than the early
AI-generated catalog that inspired it. The current project rationale is:

- use Unicode as the compatibility identity, never as something CNBE replaces;
- use the 8105 common standardized Chinese character table as the release-track
  national-standard core;
- use GF/GB/GG language and writing standards for strokes, stroke order,
  components, radicals, independent-character status, structure, and
  decomposition;
- use dictionaries, character-origin resources, Wikipedia, and ZDIC only as
  review context or source-discovery aids unless a field is explicitly labeled
  as non-national-standard context;
- keep CNBE32 as a compact runtime carrier while preserving richer evidence for
  CNBE64/CNBE128 or review archives when 32 bits are too narrow;
- publish only checkpoints that can be traced to committed evidence, reports,
  tests, and release notes.

This makes the repository a standards-aligned research workflow rather than a
large generated table with unclear authority.

---

## Why this is interesting

Unicode tells computers *which* character this is.

CNBE-32 asks a different question:

> Can part of a CJK character's visual and structural logic be carried directly in a compact binary form?

That makes CNBE-32 interesting for experiments in CJK-aware embeddings, low-level lookup tables, hardware-friendly text features, and language-specific model inputs.

---

## The idea in one picture

```text
31              24 23        19 18     15 14                 4 3        0
┌────────────────┬────────────┬─────────┬─────────────────────┬──────────┐
│ Radical/Radix  │  Stroke    │ Struct  │     Glyph Index     │   Ext    │
│     8 bits     │  5 bits    │ 4 bits  │       11 bits       │  4 bits  │
└────────────────┴────────────┴─────────┴─────────────────────┴──────────┘
```

Think of it as a compact structural fingerprint, not a replacement for Unicode.

---

## Quick start

```bash
python -m pip install cnbe32
```

```python
from cnbe32 import encode_cnbe, decode_cnbe, bit_hamming_distance

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
```

---

## What is stable today

- CNBE-32 field encoding and decoding
- strict validation of all bitfield ranges
- true bit-level Hamming distance and legacy field-weighted distance
- optional SQLite database lookup
- explicit `SkillTable` construction for experiments
- wheel build, pip install, pytest, ruff, GitHub Actions CI

---

## What is experimental

- LLM prompting and feature experiments
- JEPA-style representation learning
- RISC-V and hardware instruction prototypes
- OS and kernel-level experiments
- finance, biology, physics, and social-science-style experiments

These should be interpreted as **preliminary research prototypes** unless the corresponding directory includes fixed datasets, reproducible scripts, baseline comparisons, random seeds, and clear train/test separation.

---

## Coverage terminology

| Term | Meaning |
|---|---|
| **8105 national-standard core** | 8,105 common standardized Chinese characters used as the release-track standards baseline |
| **Packaged Python SDK database** | 20,902 Basic CJK runtime entries shipped in the wheel |
| **Agent-standard candidate scope** | project-controlled candidate outputs that must align to 8105 before promotion |
| **Experimental extended scope** | 97,686 CJK characters as a design / research target, not a validated release claim |
| **Experiment-specific coverage** | depends on the dataset and reproduction script for each experiment |

Claims about collision rate, full coverage, or extended CJK breadth should be interpreted only within the scope of the specific dataset and script used for that experiment.

---

## Evidence level

This repository contains research prototypes and early experiments. Results should be interpreted as preliminary unless the corresponding experiment includes:

- fixed dataset versions,
- reproducible scripts,
- baseline comparisons,
- random seeds or deterministic settings,
- raw outputs or result artifacts,
- and clear train/test separation where applicable.

---

## Bitfield layout

| Field | Bits | Description |
|---|---:|---|
| Radical / Radix | 8 | Radical or structural root field |
| Stroke | 5 | Stroke-count field |
| Structure | 4 | Character structure field |
| Glyph Index | 11 | Basic CJK glyph index field |
| Extension | 4 | Experimental extension field |

---

## Python SDK example

```python
from cnbe32 import (
    encode_cnbe, decode_cnbe,
    bit_hamming_distance, field_weighted_distance,
)

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
print(field_weighted_distance(a, b))
```

---

## For geeks

| If you like... | CNBE-32 gives you... |
|---|---|
| bitfields | a fixed 32-bit CJK structure layout |
| language internals | radical, stroke, structure, glyph-index fields |
| ML features | compact CJK-aware feature inputs |
| hardware experiments | a layout testable near RISC-V / instruction prototypes |
| weird text encoding ideas | a research sandbox for Chinese-native representation |

---

## For Chinese language enthusiasts

Chinese characters are not just arbitrary symbols. Many carry visible structure: components, strokes, layout, and historical form.

CNBE-32 does not claim to fully understand characters. It simply asks whether some of that visible structure can be encoded in a way computers can use directly.

---

## Roadmap

1. Keep the Python SDK build, install, test, and lint pipeline green.
2. Add reproducible scripts for each experiment.
3. Separate stable SDK claims from experiment-specific claims.
4. Publish dataset provenance and coverage validation scripts.
5. Add golden vectors shared across Python, C, Rust, and hardware prototypes.
6. Add benchmark baselines (Unicode codepoint, one-hot, IDS, learned embeddings).

---


## Implementation consistency

CNBE-32 includes machine-readable golden vectors in [spec/golden_vectors.json](./spec/golden_vectors.json). These vectors define canonical bitfield encode/decode examples for Python, C, Rust, and hardware-oriented implementations. The same vector set is now exercised by Python tests, a minimal C consistency test, and a minimal Rust consistency test.


## Project maintenance

- [Changelog](./CHANGELOG.md)
- [Release process](./RELEASE.md)
- [v1.0.4 release notes](./docs/releases/v1.0.4.md)
- [Contributing guide](./CONTRIBUTING.md)
- [Security policy](./SECURITY.md)

## License

MulanPSL-2.0
