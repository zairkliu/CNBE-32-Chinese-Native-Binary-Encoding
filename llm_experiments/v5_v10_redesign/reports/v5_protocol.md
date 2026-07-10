# v5 Protocol: Controlled Model Comparison

Status: protocol draft

This document defines the redesigned v5 experiment family.

It does not report completed results.

## Purpose

v5 tests whether CNBE-related prompt conditions change model behavior in controlled classification and interpretation tasks.

The historical v5 series compared multiple models and prompt variants.

The redesigned v5 protocol separates model-family effects from CNBE-condition effects.

## Research Question

Do CNBE treatment prompts produce measurable gains over text-only and same-length controls across model families?

## Hypotheses

H1: CNBE treatment may improve certain ambiguity-heavy tasks relative to plain text.

H2: Same-length random annotation may explain some apparent gains if output-startup or formatting effects dominate.

H3: Effects will vary by model family and size.

## Model Matrix

The model matrix must include:

- Qwen-family model A,
- Qwen-family model B,
- DeepSeek-family model A,
- DeepSeek-family model B.

Optional additions:

- one non-Qwen non-DeepSeek model,
- one small local model,
- one API-hosted reference model.

Every run must record:

- exact model ID,
- provider,
- version or digest,
- temperature,
- context limit,
- run date.

## Dataset

The dataset must include:

- stable sample IDs,
- class labels,
- class balance summary,
- difficulty tags,
- source notes,
- train/dev/test split if examples are used.

The final test split must not be edited after pilot runs.

## Conditions

Every sample must appear in:

- plain text,
- Unicode metadata,
- CNBE metadata,
- shuffled CNBE metadata,
- random same-length metadata.

When few-shot examples are used, example order must be fixed before final scoring.

## Metrics

Primary metric:

- macro F1.

Secondary metrics:

- accuracy,
- per-class recall,
- invalid-output rate,
- refusal rate,
- hallucination rate,
- output-length distribution.

## Blinding

Scoring should be blind to condition labels.

Condition names must be replaced by neutral IDs in scorer inputs.

## Statistical Plan

Use paired comparisons over sample IDs.

Use bootstrap confidence intervals for macro F1 deltas.

Report per-model and per-family results.

Do not report a single aggregate without showing model-level variation.

## Failure Conditions

The v5 run is invalid if:

- no same-length random control is used,
- model IDs are missing,
- prompt templates change after seeing test outputs,
- scoring sees condition labels,
- only one model family is tested,
- invalid outputs are manually discarded without reporting.

## Reporting Boundary

Allowed conclusion:

```text
Under the tested model matrix and dataset, CNBE metadata showed / did not show a measured effect relative to stated baselines.
```

Disallowed conclusions:

- CNBE is generally model-readable,
- CNBE improves all LLMs,
- one model family proves global validity,
- classification demos imply production readiness.
