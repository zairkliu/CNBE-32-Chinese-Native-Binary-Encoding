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
  <img alt="Standards aligned" src="https://img.shields.io/badge/standards--aligned-in%20progress-orange">
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
> The repository database has since been migrated to **v1.1** (21,178 rows); see the confirmed state below.

## Current standards restart

CNBE is being reorganized around a stricter standards-aligned workflow.

The **8105 common standardized Chinese character table** is now the national-standard core for the rebuild. Existing CNBE rows are treated as legacy/current runtime data until they pass the renewed evidence gates. The 20,902-row Agent pre-encoding pool is a project candidate pool, and the 97,686-row full catalog remains an extended research target.

The restart target is to rebuild CNBE as a national-language-standard-aligned encoding project: the Agent performs controlled Hanzi structure work, every promoted row carries evidence and review state, and the repository separates runtime code, evidence, reports, historical experiments, and reproducible research outputs.

Current confirmed state:

- release checkpoint: `v1.0.4`
- published Python package: `cnbe32==1.0.4`
- 8105 baseline rows: `8105`
- human-approved 8105 Agent structure baseline: `8105 / 8105`
- runtime CNBE32 rows patched from the approved 8105 dry run: `6712`
- additional conservative standardized runtime repairs: `598`
- total patched 8105 runtime rows after repair: `7310`
- force-approved rows retained for later insertion/radical strategy: `795`
- runtime JSON and SQLite databases rebuilt from the approved 20,902-row source

Post-migration state (v1.1, applied 2026-07-25 under owner authorization):

- dual-source repairs applied: `620` (503 strokes, 111 structure, 6 radical)
- 8105 missing characters inserted as pending-encoding rows: `276` (`cnbe=NULL`, `needs_encoding=1`). This is a database state of **no CNBE value written yet**, not a claim that the rows are unaudited. Human structure/decomposition audit is complete for all 276 characters (the 108-character T3 baseline plus the remaining 168); the evidence policy deliberately does not auto-generate codes after review.
- dual-source disagreements held from the migration period for expert adjudication: `348`. This is a separate historical v1.1 migration queue, not a failure or revocation of the 108-character human audit.
- total runtime rows: `21178`
- track column: `standard 7327 / provisional 275 / legacy 13576`
- migration is idempotent (second dry-run plans 0 ops) and recorded in `migration_meta`

Governance documents:

- [CNBE Standards Compliance Statement](./docs/CNBE_STANDARDS_COMPLIANCE_STATEMENT.md)
- [CNBE 8105 Encoding Governance](./docs/CNBE8105_ENCODING_GOVERNANCE.md)
- [CNBE Research Position Statement](./docs/CNBE_RESEARCH_POSITION_STATEMENT.md)
- [CNBE Reproducible Agent Workflow](./docs/CNBE_REPRODUCIBLE_AGENT_WORKFLOW.md)
- [CNBE Version Governance](./docs/CNBE_VERSION_GOVERNANCE.md)
- [Repository Structure](./docs/REPOSITORY_STRUCTURE.md)
- [Repository-published Agent skill](./skill/cnbe-hanzi-structure-encoding-agent/SKILL.md)
- [GitHub Copilot Cloud Agent Status](./docs/COPILOT_CLOUD_AGENT_LIMITATION.md)
- [CNBE 8105 Encoding Comparison](./evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md)
- [CNBE 8105 Runtime Promotion](./reports/8105_CNBE32_RUNTIME_PROMOTION.md)
- [CNBE 8105 Standardized Runtime Repair](./reports/8105_STANDARDIZED_RUNTIME_REPAIR.md)
- [Field Semantics Freeze v1.1](./docs/FIELD_SEMANTICS_FREEZE_v1.1.md)
- [v1.1 Migration Tooling and Verification](./reports/MIGRATION_V1_1_WS7WS8.md)
- [276 Pending 8105 Encoding Workflow](./docs/CNBE276_PENDING_ENCODING_WORKFLOW.md) — governed plan for the 276 pending rows, with a SHA-256 pinned inventory triage
- [276-character human-review intake audit](./reports/PENC276_REMAINING_168_HUMAN_REVIEW_INTAKE_AUDIT.md) — the 168-character completion audit plus the prior 108-character baseline cover all 276 rows; no CNBE source-table or SQLite write
- [iHandian network-dictionary cross-reference rule](./skill/references/ihandian.md) — Unicode-first, single-character, read-only reference at the same review tier as dictionary/ZDIC context
- [WS-4 Benchmark Pre-Registration](./docs/benchmarks/WS4_BENCHMARK_PRE_REGISTRATION.md)

### T3 exploratory batch: human audit first

All 276 PENC276 characters have completed **human structure/decomposition audit**: the first 108 characters (`PENC_169`–`PENC_276`) form the T3 baseline, and the remaining 168 were completed through the same Chinese review packet. The recorded human audit is the final project working baseline. 8105 and related national language-and-writing standards, Unihan, ZDIC, dictionaries, and iHandian are used for alignment, cross-checking, and difference discovery; they are not a “gold standard” that automatically overrides human conclusions. When external sources disagree, are incomplete, or expose glyph-rendering limits, the workflow preserves the original discrepancy and pending-adjudication state. It does not generate candidate CNBE codes or write back to the source table or SQLite database.

The 168-character completion audit means all 276 rows now have human-reviewed structure/decomposition records. A stratified iHandian smoke test aligned Unicode and returned decomposition fields for 14/14 samples; 13 matched human decomposition exactly. `PENC_022` contains a human-approved nonrenderable component-glyph exception: its human decomposition is retained and it is not counted as a web-reference difference. The 348 historical migration disagreements remain a separate queue and are not closed by this result.

- [Human-audit evidence policy](./docs/PENC276_T3_HUMAN_AUDIT_EVIDENCE_POLICY.md)
- [Final 108-character human-audit baseline](./evidence/8105/pending276/T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.csv)
- [Machine-readable baseline summary](./reports/PENC276_T3_169_276_FINAL_HUMAN_AUDIT_BASELINE.json)

Mathematics and review program:

- [CNBE-32 Mathematical Structure](./docs/CNBE32_MATHEMATICAL_STRUCTURE.md) — standalone presentation of the 13 research formulas
- [Formal Mathematical Specification (EN)](./docs/specification/CNBE_FORMAL_MATHEMATICAL_SPECIFICATION.md) / [中文版](./docs/specification/CNBE_FORMAL_MATHEMATICAL_SPECIFICATION_ZH.md)
- [Formula Verification Report](./experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md) — 13/13 mathematical PASS, 0 scientific performance claims validated
- [Verification Manifest](./experiments/morphology_computing/reports/formal_formula_verification_manifest.json) — machine-readable, SHA-256 pinned
- [P1 External Review Method (EN)](./docs/specification/P1_EXTERNAL_REVIEW_METHOD.md) / [中文版](./docs/specification/P1_EXTERNAL_REVIEW_METHOD_ZH.md)
- [P1 External Review Execution Kit](./docs/review/P1_EXTERNAL_REVIEW_EXECUTION_KIT.md) — reviewer-facing instructions for the 600-row blinded packet
- [External Review Packet](./experiments/morphology_computing/review_packets/P1_EXTERNAL_INDEPENDENT_REVIEW_PACKET_EDITABLE.csv) — 600 blinded rows awaiting independent review

Earlier AI-generated catalog fields are now treated as a historical test
baseline only. They remain useful for regression localization, but they are not
used as authority for structure, radical, stroke, teaching, or research claims.

> **Wording red line**: this project is *aligning to* national language and writing standards. Until every item in the standards-alignment matrix reads "aligned", the project does not claim to "conform to national standards". Full alignment status and known gaps: [CNBE Standards Compliance Statement](./docs/CNBE_STANDARDS_COMPLIANCE_STATEMENT.md).

## Project rationale

CNBE-32 is useful only if the encoding process is stricter than the early
AI-generated catalog that inspired it. The current project rationale is:

- use Unicode as the compatibility identity, never as something CNBE replaces;
- use the 8105 common standardized Chinese character table as the release-track
  national-standard core;
- use GF/GB/GG language and writing standards for each Hanzi attribute (alignment status: [Standards Compliance Statement](./docs/CNBE_STANDARDS_COMPLIANCE_STATEMENT.md)):
  - structure → GF 0017-2013 §3.12 (independent + 12 compound types; the project's 13 labels map one-to-one)
  - radicals → GF 0011-2009 / GF 0012-2009 (anchoring in progress)
  - independent characters → GF 0013-2009 (direction aligned, not yet verified per character)
  - components and decomposition → GF 0014-2009 / GF 3001-1997 (direction aligned, not yet verified per character)
  - stroke order and stroke shapes → GF 0023-2020 / GF 3002-1999
- character identity is carried by the Unicode code point; a bidirectional mapping layer with GB 18030-2022 is on the roadmap;
- use dictionaries, character-origin resources, Wikipedia, and ZDIC only as
  review context or source-discovery aids unless a field is explicitly labeled
  as non-national-standard context;
- keep CNBE32 as a compact runtime carrier while preserving richer evidence for
  CNBE64/CNBE128 or review archives when 32 bits are too narrow;
- publish only checkpoints that can be traced to committed evidence, reports,
  tests, and release notes.

This makes the repository a standards-aligned research workflow rather than a
large generated table with unclear authority.

For a one-page research framing of the current direction, time point,
reproducibility path, technical feasibility, and scientific value, see
[CNBE Research Position Statement](./docs/CNBE_RESEARCH_POSITION_STATEMENT.md).

## Agent and automation boundary

The repository includes a GitHub-compatible Agent profile and Copilot
instructions, but GitHub Copilot cloud agent execution is an optional paid
integration. It is not required for open-source reproduction, research review,
or release-track CNBE work.

The project keeps its reproducible baseline in committed skills, tests,
reports, review packets, and ordinary GitHub Actions. Maintainers without
Copilot cloud agent access can still run the CNBE Agent workflow locally or
through normal pull requests. See
[GitHub Copilot Cloud Agent Status](./docs/COPILOT_CLOUD_AGENT_LIMITATION.md).

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

# Note: radix is a project-internal radical/root numbering, not yet anchored to
# GF 0011-2009; do not use it for cross-project exchange before anchoring lands.
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
- optional SQLite database lookup (v1.1 migrated schema with `track` column)
- explicit `SkillTable` construction for experiments
- wheel build, pip install, pytest, ruff, GitHub Actions CI

---

## What is experimental

- LLM prompting and feature experiments
- JEPA-style representation learning
- RISC-V and hardware instruction prototypes
- OS and kernel-level experiments (teaching proof-of-concept: the current code does not compile and serves only as an Agent-workflow research sample, not a usable system)
- finance, biology, physics, and social-science-style experiments

These should be interpreted as **preliminary research prototypes** unless the corresponding directory includes fixed datasets, reproducible scripts, baseline comparisons, random seeds, and clear train/test separation.

---

## Coverage terminology

| Term | Meaning |
|---|---|
| **8105 national-standard core** | 8,105 common standardized Chinese characters used as the release-track standards baseline |
| **Packaged Python SDK database** | 20,902 Basic CJK runtime entries shipped in the wheel |
| **Repository database (v1.1)** | 21,178 rows after migration: 7,327 standard + 275 provisional + 13,576 legacy, incl. 276 pending-encoding 8105 rows |
| **Agent-standard candidate scope** | project-controlled candidate outputs that must align to 8105 before promotion |
| **Experimental extended scope** | 97,686 CJK characters as a design / research target, not a validated release claim; the figure anchors the Unicode CJK Unified Ideographs total and must be updated with Unicode versions and GB 18030-2022 amendments |
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

## Formal mathematics (research definitions)

The encoding admits a compact formalization: bitfield extraction and binary-vector operators, a field-weighted morphological distance, and three candidate computational layers — a Poincaré-ball embedding with a morphology-alignment loss, a bitwise MoE router, and a hyperdimensional (HDC/VSA) representation.

Every formula group has a reference implementation with numerical property tests (reversibility, identity, symmetry, bounds, closure). These are **research definitions**: they do not certify the linguistic correctness of any field, and they do not by themselves demonstrate task-level gains. Candidate layers remain gated on external independent review.

Full presentation: [CNBE-32 Mathematical Structure](./docs/CNBE32_MATHEMATICAL_STRUCTURE.md). Verification evidence: [13/13 formula report](./experiments/morphology_computing/reports/FORMAL_FORMULA_VERIFICATION_REPORT.md) and [SHA-256 pinned manifest](./experiments/morphology_computing/reports/formal_formula_verification_manifest.json). Task-level evaluation is pre-registered in [WS-4](./docs/benchmarks/WS4_BENCHMARK_PRE_REGISTRATION.md) and blocked pending the [P1 external review](./docs/review/P1_EXTERNAL_REVIEW_EXECUTION_KIT.md).

---

## Python SDK example

```python
from cnbe32 import (
    encode_cnbe, decode_cnbe,
    bit_hamming_distance, field_weighted_distance,
)

# radix is a project-internal numbering; do not use it for cross-project
# exchange before GF 0011-2009 anchoring lands (see Field Semantics Freeze v1.1).
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

The project's structure taxonomy (independent, top-bottom, left-right, enclosure, and the other approved types — 13 labels in total) maps one-to-one to the Hanzi structure classification in GF 0017-2013.

---

## Roadmap

1. Keep the Python SDK build, install, test, and lint pipeline green.
2. Add reproducible scripts for each experiment.
3. Separate stable SDK claims from experiment-specific claims.
4. Publish dataset provenance and coverage validation scripts.
5. Add golden vectors shared across Python, C, Rust, and hardware prototypes.
6. Add benchmark baselines (Unicode codepoint, one-hot, IDS, learned embeddings).
7. Run the P1 external independent review, then execute the pre-registered WS-4 benchmarks.
8. Use the completed 276-character human-audit record as the project baseline for separately authorized radical/stroke adjudication and CNBE candidate generation through the [governed encoding workflow](./docs/CNBE276_PENDING_ENCODING_WORKFLOW.md). Any source-table or database write still requires separate written authorization ([SHA-256 pinned inventory](./evidence/8105/PENDING_276_ENCODING_INVENTORY.csv)).

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
