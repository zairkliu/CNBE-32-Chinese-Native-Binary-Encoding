# Sampling Plan for Redesigned v1-v4 Experiments

Status: protocol draft

This document defines dataset sampling rules for confirmatory v1-v4 experiments.

No samples are drawn by this document.

## General Rules

All samples must receive stable sample IDs.

All samples must record source, split, condition eligibility, and reference material.

Sampling must be complete before model outputs are inspected.

The evaluation split must not be edited after early results are known.

Each sample must be usable across all relevant conditions.

Each sample must preserve enough metadata for blind review.

## Splits

Recommended split names:

- `pilot`,
- `dev`,
- `test`.

The pilot split is used only to test infrastructure.

The dev split is used to finalize prompts and rubric.

The test split is used for confirmatory claims.

No final claim should use pilot data.

## Random Seeds

Recommended seeds:

- sample selection: 20260710,
- split assignment: 20260711,
- condition order: 20260712,
- bootstrap resampling: 20260713.

Every future report must list the actual seeds.

## v1 Single-Character Sampling

v1 tests single-character incremental information.

Required strata:

- common Basic CJK,
- rare Basic CJK,
- extension characters,
- polysemous characters,
- radical-misleading characters.

Recommended minimum test samples:

- 100 common Basic CJK,
- 100 rare Basic CJK,
- 100 extension characters,
- 100 polysemous characters,
- 100 radical-misleading characters.

Each character record should include:

- character,
- Unicode code point,
- radical,
- stroke count,
- structure type,
- CNBE fields,
- semantic category,
- reference gloss,
- ambiguity notes.

The target character may be visible or hidden depending on the condition.

When the character is hidden, the model receives only encoded or baseline metadata.

## v2 Sentence Sampling

v2 tests sentence-level comprehension.

Required strata:

- classical Chinese,
- modern news,
- science text,
- spoken dialogue,
- rare-character dense sentence.

Recommended minimum test samples:

- 60 classical sentences,
- 60 modern news sentences,
- 60 science sentences,
- 60 spoken dialogue sentences,
- 60 rare-character dense sentences.

Every sentence needs:

- reference answer,
- key points,
- disallowed hallucination notes,
- expected difficulty rating,
- token count without annotation,
- token count with each annotation format.

## v3 Format-Ablation Sampling

v3 reuses the v2 sentence pool.

The goal is to vary annotation format while holding text constant.

Every v3 sample must appear in all format conditions:

- inline full,
- inline compact,
- prefix table,
- side-channel JSON,
- selective annotation,
- random same-length annotation.

Condition order must be randomized for each model.

The scoring team must not see format labels.

## v4 Long-Context Sampling

v4 tests long-context robustness.

Required source types:

- classical argument text,
- modern policy or news article,
- technical explanatory text.

Each source should be segmented into:

- paragraph-level units,
- section-level units,
- full-document units.

Tasks must include:

- paragraph summary,
- argument extraction,
- concept question answering,
- cross-paragraph evidence lookup,
- distractor robustness.

The long-context plan must record:

- original source,
- segment boundaries,
- reference answers,
- evidence spans,
- expected answer style,
- token budget.

## Leakage Control

Reference answers must not appear in prompts.

Condition names must not appear in judge prompts.

CNBE condition labels must be replaced with blind IDs before scoring.

Prompt examples must not include test samples.

Generated random annotations must be stable and reproducible.

## Dataset Manifest

Each dataset release should include:

- schema version,
- sample count by split,
- sample count by source type,
- random seeds,
- generation script hash,
- reviewer names or reviewer IDs,
- known limitations.
