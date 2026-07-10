# Metrics for Redesigned v1-v4 Experiments

Status: protocol draft

This document defines metrics for confirmatory evaluation.

The metrics should be computed from blinded scored outputs.

## Notation

Let `N` be the number of paired samples.

Let `score_i(condition)` be the numeric score for sample `i`.

Let `valid_i(condition)` be 1 if output is valid and 0 otherwise.

Let `tokens_i(condition)` be input plus output tokens for sample `i`.

## Validity Rate

Formula:

```text
validity_rate(condition) = sum(valid_i(condition)) / N
```

Use this only as a basic output-health metric.

It must not be treated as the main comprehension metric.

## Key Point Recall

Formula:

```text
key_point_recall_i = covered_key_point_credit_i / total_key_points_i
key_point_recall(condition) = mean(key_point_recall_i)
```

This is the primary metric for v2 and a secondary metric for v4.

## Semantic Correctness

Formula:

```text
semantic_correctness(condition) = mean(semantic_score_i / 2)
```

The rubric score is normalized from 0 to 1.

## Distraction Rate

Formula:

```text
distraction_rate(condition) = sum(distraction_i(condition)) / N
```

Distraction is a penalty metric.

It should be reported separately and used in cost-adjusted scoring.

## Hallucination Rate

Formula:

```text
hallucination_rate(condition) = sum(hallucination_i(condition)) / N
```

Hallucination is a safety and quality penalty.

## Refusal Rate

Formula:

```text
refusal_rate(condition) = sum(refusal_i(condition)) / N
```

Refusal rate helps distinguish low task ability from low output willingness.

## Delta Versus Baseline

Formula:

```text
delta_vs_baseline = metric(treatment) - metric(baseline)
```

Every reported treatment score should include at least one paired baseline delta.

Preferred baselines:

- pure text for text tasks,
- radical-only for single-character tasks,
- shuffled CNBE for structure-specific claims,
- random annotation for length-control claims.

## Cost Adjusted Gain

Formula:

```text
token_overhead_ratio = (tokens_treatment - tokens_baseline) / max(tokens_baseline, 1)
quality_gain = score_treatment - score_baseline
cost_adjusted_gain = quality_gain - alpha * token_overhead_ratio
```

`alpha` must be declared before scoring.

Recommended default:

```text
alpha = 0.10
```

Sensitivity analysis may report other alpha values.

## v3 Format Score

Formula:

```text
format_score = score_gain - distraction_penalty - token_cost_penalty
```

Where:

```text
score_gain = treatment_score - pure_text_score
distraction_penalty = distraction_rate * distraction_weight
token_cost_penalty = token_overhead_ratio * token_cost_weight
```

Weights must be fixed before comparing formats.

## Bootstrap Confidence Interval

Use paired bootstrap resampling over sample IDs.

Procedure:

1. Resample sample IDs with replacement.
2. Compute the metric delta for each resample.
3. Repeat at least 5,000 times.
4. Report the 2.5th and 97.5th percentiles.

Report:

- mean delta,
- median delta,
- 95 percent interval,
- number of bootstrap iterations,
- random seed.

## McNemar Test Applicability

Use McNemar tests for paired binary outcomes, such as:

- valid vs invalid,
- correct vs incorrect,
- distracted vs not distracted,
- hallucinated vs not hallucinated.

The two conditions must be evaluated on the same sample IDs.

Report the contingency table.

## Paired Test Applicability

Use paired tests for numeric outcomes, such as:

- key point recall,
- semantic correctness,
- evidence grounding,
- cost-adjusted gain.

If score distribution is skewed, prefer bootstrap intervals over parametric claims.

## Multiple Comparisons

When many formats or models are compared, report the comparison family.

Use correction or clearly label uncorrected p-values.

Recommended approach:

- primary comparison is pre-registered,
- secondary comparisons are exploratory,
- adjusted interpretation is stated.

## Minimum Reporting Table

Each future result table should include:

- model,
- split,
- condition,
- N,
- primary metric,
- baseline,
- delta,
- confidence interval,
- p-value when used,
- token overhead,
- distraction rate,
- hallucination rate.
