# v1 Protocol: Single-Character Incremental Signal

Status: protocol draft

This document defines the redesigned v1 experiment.

It does not report completed results.

## Purpose

v1 tests whether CNBE fields provide measurable incremental information for single-character semantic tasks.

The earlier exploratory experiment asked whether an LLM could produce plausible semantic descriptions from CNBE-like annotations.

The redesigned experiment asks a stricter question:

Do CNBE fields outperform Unicode-only and radical-only baselines under blind evaluation?

## Research Question

Do CNBE fields provide measurable incremental signal over:

- character-only input,
- Unicode code point input,
- radical-only input,
- shuffled CNBE fields,
- random CNBE-like fields?

## Hypothesis

CNBE full fields should improve semantic category accuracy relative to radical-only and Unicode-only baselines.

If shuffled or random CNBE performs similarly, the result should be interpreted as a prompt-format or metadata-length effect.

## Sample Design

Use stratified character sampling:

- common Basic CJK,
- rare Basic CJK,
- extension characters,
- polysemous characters,
- radical-misleading characters.

Each stratum should contribute enough samples for paired analysis.

Each sample must have:

- target character,
- Unicode code point,
- radical label,
- stroke count,
- structure label,
- CNBE fields,
- semantic category,
- reference gloss,
- ambiguity notes.

## Conditions

Every sample must appear in every condition:

- `character_only`,
- `unicode_only`,
- `radical_only`,
- `cnbe_full`,
- `shuffled_cnbe`,
- `random_cnbe`.

The condition label must be hidden from judges.

## Prompting

Use `prompts/v1_single_char.yaml`.

The task output must be JSON with:

- semantic category,
- confidence,
- short reason.

No few-shot examples should be used in the confirmatory test unless they are fixed before the test split is scored.

## Models

Run at least:

- one Qwen small model,
- one Qwen medium model,
- one DeepSeek small model,
- one DeepSeek medium model.

Record exact model identifiers.

Do not aggregate across model families without showing per-model results.

## Metrics

Primary metric:

- semantic category accuracy.

Secondary metrics:

- top-k semantic category hit,
- refusal rate,
- hallucination rate,
- confidence calibration,
- delta versus radical-only,
- delta versus shuffled CNBE.

## Statistical Tests

Use paired comparisons over sample IDs.

Use McNemar tests for binary accuracy.

Use bootstrap confidence intervals for deltas.

Report model-specific confidence intervals.

## Interpretation

Allowed conclusion template:

```text
Under the tested models and samples, CNBE full fields show / do not show measurable incremental signal over radical-only and Unicode baselines.
```

Disallowed conclusion patterns:

- universal LLM effectiveness,
- deployment readiness,
- replacing Unicode,
- completed validation across all Chinese characters.

## Failure Conditions

The v1 run is invalid if:

- there is no radical-only baseline,
- there is no shuffled or random CNBE control,
- the model sees the answer category in the prompt,
- the judge sees the condition label,
- outputs are filtered after scoring begins,
- only validity rate is reported.

## Expected Report Sections

A completed v1 report should include:

- model manifest,
- dataset manifest,
- prompt template hash,
- sample counts by stratum,
- metric table by model,
- paired baseline comparisons,
- failure analysis,
- limitations,
- raw output availability.
