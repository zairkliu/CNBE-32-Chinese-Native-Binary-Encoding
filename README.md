# CNBE-32 Chinese Native Binary Encoding

> **Project status:** research prototype.
>
> **Current packaged Python SDK database:** 20,902 Basic CJK entries.
>
> The broader **97,686 CJK** figure refers to an intended / experimental extended encoding scope, not the current packaged Python SDK database coverage.
>
> **Stable:** Python bitfield encoder/decoder, distance utilities, and Basic CJK lookup when the database is available.
>
> **Experimental:** LLM, JEPA, RISC-V, OS, finance, biology, physics, and other research prototypes.

CNBE-32 is a 32-bit structural encoding experiment for CJK characters. It explores whether CJK-specific structural fields such as radical/radix, stroke count, character structure, glyph index, and extension bits can be represented in a compact binary format for AI and hardware-oriented experiments.

This repository currently provides a hardened Python SDK baseline and a collection of research prototypes. The Python SDK is the most stable part of the repository. Other directories should be treated as experimental unless they include their own reproducible scripts, datasets, and validation notes.

---

## Why CNBE-32?

Most general-purpose text encodings represent characters as identifiers. CNBE-32 experiments with a different idea: encode selected structural properties of CJK characters directly into a fixed-width 32-bit value.

The goal is not to replace Unicode. Instead, CNBE-32 is intended as an auxiliary representation for experiments involving:

- CJK-aware model inputs,
- structural character features,
- compact lookup tables,
- hardware-oriented encoding tests,
- and reproducible CJK feature benchmarks.

---

## Current stable scope

The current stable Python SDK supports:

- CNBE-32 field encoding and decoding,
- strict validation of all bitfield ranges,
- true bit-level Hamming distance,
- legacy field-weighted distance,
- optional SQLite database lookup,
- explicit `SkillTable` construction for experiments,
- wheel build and installation,
- pytest coverage,
- ruff linting,
- and GitHub Actions CI.

The packaged SDK currently targets the **20,902-entry Basic CJK database**.

---

## Experimental scope

The repository also contains exploratory work around:

- LLM prompting and feature experiments,
- JEPA-style representation learning,
- RISC-V and hardware instruction prototypes,
- OS and kernel-level experiments,
- finance, biology, physics, and social-science-style experiments.

These experiments should be interpreted as **preliminary research prototypes** unless the corresponding directory includes:

- fixed dataset versions,
- reproducible scripts,
- baseline comparisons,
- random seeds or deterministic settings,
- raw result artifacts,
- and clear train/test separation where applicable.

---

## Coverage terminology

CNBE-32 uses several coverage terms that should not be mixed:

- **Packaged Python SDK database:** currently 20,902 Basic CJK entries.
- **Experimental extended scope:** 97,686 CJK characters as a design / research target.
- **Experiment-specific coverage:** depends on the dataset and reproduction script for each experiment.

Unless otherwise stated, examples in the Python SDK documentation refer to the packaged 20,902-entry Basic CJK database.

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

The Python SDK hardening work focuses on making the core encoder, decoder, distance utilities, database loading, and tests reproducible.

---

## Bitfield layout

CNBE-32 uses a 32-bit layout:

| Field | Bits | Description |
|---|---:|---|
| Radical / Radix | 8 | Radical or structural root field |
| Stroke | 5 | Stroke-count field |
| Structure | 4 | Character structure field |
| Glyph Index | 11 | Basic CJK glyph index field |
| Extension | 4 | Experimental extension field |

The current Python SDK validates all fields before encoding. Invalid values raise a `CNBEValueError`; values are not silently truncated.

---

## Python SDK installation

From a local checkout:

```bash
python -m pip install .
```

For development:

```bash
python -m pip install -U pip build pytest ruff
python -m pip install -e .
```

---

## Python SDK example

```python
from cnbe32 import (
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
)

a = encode_cnbe(radix=72, stroke=8, struct=1, index=123, ext=0)
b = encode_cnbe(radix=72, stroke=9, struct=1, index=124, ext=0)

print(decode_cnbe(a))
print(bit_hamming_distance(a, b))
print(field_weighted_distance(a, b))
```

---

## Distance functions

Use:

* `bit_hamming_distance(a, b)` for true bit-level Hamming distance.
* `field_weighted_distance(a, b)` for the legacy CNBE field-weighted distance.

Deprecated:

* `hamming_distance(a, b)`

`hamming_distance` is retained for compatibility but is not a true bit-level Hamming distance.

---

## Database loading

The Python SDK resolves `cnbe32.db` in this order:

1. `CNBE32_DB_PATH`
2. packaged data: `cnbe32/data/cnbe32.db`
3. source checkout fallback: `data/cnbe32.db`

Example:

```bash
export CNBE32_DB_PATH=/path/to/cnbe32.db
```

If the database is missing, database lookup functions raise a clear error explaining how to provide the file.

---

## SkillTable

`SkillTable` is intended for experiments over Basic CJK code point offsets.

Use:

```python
from cnbe32 import SkillTable

table = SkillTable.empty()
```

or:

```python
table = SkillTable.from_file("skill_table.npy")
```

Direct `SkillTable()` construction without a table is intentionally unsupported. This avoids silently creating an all-zero table when a real table was expected.

---

## Development checks

Run the full local validation suite:

```bash
python -m compileall src tests
python -m build
python -m pip install --force-reinstall dist/*.whl
pytest
ruff check src tests
```

The CI workflow runs compile, build, wheel installation, pytest, and ruff checks on Python 3.10, 3.11, and 3.12.

---

## Repository status

Recommended interpretation of repository areas:

| Area                                    | Status                            |
| --------------------------------------- | --------------------------------- |
| Python SDK bitfield encode/decode       | Stable baseline                   |
| Python SDK tests and CI                 | Stable baseline                   |
| Basic CJK database lookup               | Stable when database is available |
| Extended CJK coverage                   | Experimental target               |
| LLM / JEPA experiments                  | Research prototype                |
| RISC-V / hardware experiments           | Research prototype                |
| OS / kernel experiments                 | Research prototype                |
| Finance / biology / physics experiments | Research prototype                |

---

## Roadmap

Suggested next steps:

1. Keep the Python SDK build, install, test, and lint pipeline green.
2. Add reproducible scripts for each experiment.
3. Separate stable SDK claims from experiment-specific claims.
4. Publish dataset provenance and coverage validation scripts.
5. Add golden vectors shared across Python, C, Rust, and hardware prototypes.
6. Add benchmark baselines such as Unicode codepoint features, one-hot, IDS-style features, and learned embeddings.

---

## License

MulanPSL-2.0
