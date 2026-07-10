# CNBE-32 v1-v4 LLM Experiment Redesign

Status: protocol draft

This directory defines a redesigned experiment protocol for CNBE-32 v1-v4 large language model studies.

It does not report completed results.

It does not replace the historical reports under:

- `llm_experiments/v1_v4_validation/`
- `results/v1_v4_validation/`

Those earlier documents should be treated as exploratory reports.

This directory defines a confirmatory protocol that can be reviewed before new model runs are performed.

## Why Redesign

The earlier v1-v4 experiments were useful for exploration, but they mixed several effects:

- model prior knowledge of Chinese characters,
- prompt formatting effects,
- output-startup effects,
- annotation length effects,
- CNBE field information,
- evaluator subjectivity.

The redesigned protocol separates those effects with baselines, ablations, blind judging, and statistical tests.

## Scope

The protocol covers four studies:

- v1: single-character incremental information.
- v2: sentence-level comprehension gain.
- v3: annotation-format ablation.
- v4: long-context robustness.

Each study is designed to compare CNBE conditions against meaningful controls.

## Model Families

The confirmatory runs should include at least:

- two Qwen-family models,
- two DeepSeek-family models,
- at least two size bands when available,
- one deterministic configuration,
- one low-temperature stability configuration.

The exact model IDs must be recorded in the final run manifest.

## Required Controls

Every experiment must include relevant baselines:

- pure text,
- Unicode code point,
- radical-only annotation,
- CNBE full fields,
- shuffled CNBE fields,
- random annotation with matched length.

The shuffled and random controls are critical. They test whether gains come from CNBE structure or from extra tokens.

## Evaluation Principles

The evaluator must not know which condition produced an answer.

The evaluator must score answers using a predefined rubric.

The same input split must be used across model families.

The same random seeds must be reused for every condition.

The same decoding parameters must be recorded for every run.

## Statistical Plan

Reports must include:

- paired comparisons against baselines,
- bootstrap confidence intervals,
- McNemar tests for paired binary outcomes when applicable,
- paired tests for numeric scores when applicable,
- model-family stratified summaries.

No broad conclusion should be made from a single model or one run.

## Reporting Rules

A future report may say that a condition showed measurable gain under the tested setup.

A future report must not claim universal model effectiveness.

A future report must not claim deployment readiness.

A future report must separate exploratory observations from confirmatory outcomes.

## Directory Layout

- `protocol.md`: cross-study protocol.
- `datasets/sampling_plan.md`: sampling and split design.
- `datasets/annotation_schema.json`: sample metadata schema.
- `prompts/`: prompt templates by experiment.
- `evaluation/`: rubric, metrics, and blind judge prompt.
- `reports/`: per-version protocol documents.

## Non-Goals

This protocol does not:

- run a model,
- publish results,
- modify the Python SDK,
- modify CNBE-32 bitfield semantics,
- change golden vectors,
- change package data,
- edit historical reports,
- assert that CNBE is generally effective across all LLMs.
