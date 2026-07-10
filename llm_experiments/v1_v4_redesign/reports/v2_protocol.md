# v2 Protocol: Sentence-Level Comprehension Gain

Status: protocol draft

This document defines the redesigned v2 experiment.

It does not report completed results.

## Purpose

v2 tests whether CNBE annotation improves sentence comprehension quality.

The earlier exploratory experiment emphasized response rate.

The redesigned experiment uses semantic scoring and controls for annotation length.

## Research Question

Does CNBE annotation improve key-point recall and factual consistency over pure text and matched controls?

## Hypothesis

CNBE annotation may help most on classical, rare-character, or ambiguity-heavy sentences.

It may not help ordinary modern sentences where the model already understands the text.

## Dataset

Use stratified sentence sampling:

- classical Chinese,
- modern news,
- science text,
- spoken dialogue,
- rare-character dense sentences.

Each sample must have:

- input text,
- reference answer,
- key points,
- difficulty label,
- source type,
- token counts per condition.

## Conditions

Every sentence appears in:

- `pure_text`,
- `text_plus_cnbe`,
- `text_plus_radical_only`,
- `text_plus_shuffled_cnbe`,
- `text_plus_random_annotation`.

The random annotation condition must be similar in token length to the CNBE condition.

## Prompting

Use `prompts/v2_sentence.yaml`.

The task is to summarize sentence meaning in one or two sentences.

The prompt must not tell the model which condition is expected to help.

Output format must be JSON.

## Evaluation

Primary metric:

- key-point recall.

Secondary metrics:

- semantic correctness,
- factual consistency,
- distraction rate,
- hallucination rate,
- refusal rate,
- output validity,
- token overhead adjusted score.

Validity rate is not enough for a positive conclusion.

## Blind Review

At least two human reviewers should score a subset of samples.

Reviewers must not know the condition labels.

Reviewer agreement should be reported.

LLM judge output may assist but should not replace all human review.

## Length Control

The experiment must record:

- input tokens,
- output tokens,
- total tokens,
- annotation overhead ratio.

If CNBE improves output length but not key-point recall, the result should be described as output-startup effect, not comprehension gain.

## Statistical Tests

Use paired bootstrap intervals for numeric scores.

Use McNemar tests for binary validity, refusal, distraction, and hallucination.

Report deltas against:

- pure text,
- radical-only,
- shuffled CNBE,
- random annotation.

## Interpretation

Allowed conclusion template:

```text
Under the tested models and sentence strata, CNBE annotation improved / did not improve key-point recall after controlling for annotation length.
```

Do not treat response rate alone as comprehension improvement.

Do not generalize from one text category to all Chinese text.

## Failure Conditions

The v2 run is invalid if:

- no random annotation control is used,
- no radical-only control is used,
- output validity is the only metric,
- condition labels leak to judges,
- references are edited after model output is inspected.

## Expected Report Sections

A completed v2 report should include:

- dataset stratification,
- model matrix,
- prompt templates,
- blind scoring method,
- key-point recall table,
- cost-adjusted score table,
- qualitative error analysis,
- null and negative findings.
