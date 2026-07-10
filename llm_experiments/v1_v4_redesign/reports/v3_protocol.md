# v3 Protocol: CNBE Injection Format Ablation

Status: protocol draft

This document defines the redesigned v3 experiment.

It does not report completed results.

## Purpose

v3 compares annotation formats.

It should not be used as the primary evidence that CNBE itself helps.

The goal is to find a format with low distraction and reasonable token cost.

## Research Question

Which CNBE injection format provides the best tradeoff among:

- task score,
- distraction,
- token overhead,
- robustness across model families?

## Conditions

Every sample should appear in these formats:

- `inline_full`,
- `inline_compact`,
- `prefix_table`,
- `side_channel_json`,
- `selective_annotation`,
- `random_same_length_annotation`.

All formats use the same underlying sentence.

Only the annotation representation changes.

## Dataset

Use the v2 sentence pool.

Do not change the sentence set after seeing v2 results.

Include multiple source types:

- classical Chinese,
- modern news,
- science text,
- spoken dialogue,
- rare-character dense sentences.

## Prompting

Use `prompts/v3_format_ablation.yaml`.

The model must be asked to perform the same sentence-comprehension task in every condition.

The prompt should not tell the model to prefer a format.

The output must include `metadata_used` as a self-report field, but this field is not the primary metric.

## Primary Score

The primary score is:

```text
score_gain - distraction_penalty - token_cost_penalty
```

Where:

```text
score_gain = treatment_score - pure_text_score
distraction_penalty = distraction_rate * distraction_weight
token_cost_penalty = token_overhead_ratio * token_cost_weight
```

Weights must be fixed before evaluation.

## Secondary Metrics

Secondary metrics include:

- key-point recall,
- semantic correctness,
- factual consistency,
- distraction rate,
- hallucination rate,
- metadata-used self report,
- token overhead,
- output validity.

## Format-Specific Risks

Inline full may increase token load.

Inline compact may lose useful field detail.

Prefix table may pull attention away from the sentence.

Side-channel JSON may be robust for API models but unnatural for smaller models.

Selective annotation may be the most practical if it keeps useful signal at lower cost.

Random same-length annotation detects whether length and formatting alone explain gains.

## Statistical Tests

Use paired bootstrap confidence intervals over sample IDs.

Use paired comparisons between each format and:

- pure text,
- random same-length annotation,
- inline full.

Report model-family-specific results.

## Interpretation

Allowed conclusion template:

```text
Under the tested models, the best format by cost-adjusted score was X. This indicates a practical prompt design preference, not a universal property of CNBE.
```

If the random same-length annotation is competitive, the report must say that format or length effects may explain the gain.

## Failure Conditions

The v3 run is invalid if:

- token overhead is not measured,
- random same-length annotation is missing,
- only one format is tested,
- the task changes between formats,
- judge labels reveal format names.

## Expected Report Sections

A completed v3 report should include:

- format definitions,
- sample count,
- token overhead table,
- distraction table,
- primary score table,
- per-model ranking,
- examples of distraction,
- recommendation for v4 format choice.
