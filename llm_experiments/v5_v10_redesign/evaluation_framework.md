# Evaluation Framework for v5-v10

Status: protocol draft

This document defines shared evaluation rules for redesigned v5-v10 experiments.

## Metric Classes

The redesigned stages use separate metric classes:

- classification metrics,
- generation-quality metrics,
- cost-adjusted prompt metrics,
- compiler correctness metrics,
- hardware trace metrics,
- prediction metrics,
- domain-specific scientific or operational metrics.

Metrics from different classes must not be added into a single universal score.

## Classification Metrics

Use for v5 intent classification and similar tasks.

Recommended metrics:

- accuracy,
- macro F1,
- per-class recall,
- confusion matrix,
- invalid-output rate,
- refusal rate.

Macro F1 is preferred when class imbalance exists.

The final report must include per-class metrics.

## Generation Metrics

Use for explanation, summary, and reasoning tasks.

Recommended metrics:

- key-point recall,
- factual consistency,
- hallucination rate,
- distraction rate,
- judge agreement,
- human-audited subset score.

Automated judge scores must be described as assisted evaluation.

They should not be treated as ground truth without audit.

## Cost-Adjusted Metrics

Use for numerical feature and annotation-format experiments.

Recommended formula:

```text
quality_gain = treatment_score - baseline_score
token_overhead_ratio = (treatment_tokens - baseline_tokens) / max(baseline_tokens, 1)
cost_adjusted_gain = quality_gain - alpha * token_overhead_ratio
```

`alpha` must be fixed before evaluation.

Reports should include sensitivity analysis when annotation overhead is large.

## Compiler Metrics

Use for v8 compiler and language experiments.

Recommended metrics:

- parse success rate,
- type or semantic check success rate when applicable,
- generated assembly correctness,
- fixture pass rate,
- runtime output match,
- negative-test rejection rate.

Compiler demos must include negative tests.

Passing only happy-path fixtures is insufficient.

## Hardware Metrics

Use for v7 and hardware-related v8 experiments.

Recommended metrics:

- encode/decode round-trip pass rate,
- emulator trace match,
- register-state match,
- memory-state match,
- instruction latency when measured,
- toolchain reproducibility.

Every trace comparison must specify the expected trace.

Prototype results must identify simulator, FPGA, or physical hardware.

## Prediction Metrics

Use for v9 and predictive v10 experiments.

Recommended metrics:

- mean absolute error,
- root mean squared error,
- calibration error,
- directional accuracy,
- Brier score for probabilistic events,
- precision and recall for rare events,
- benchmark-relative skill score.

The baseline must be domain-appropriate.

For time series, naive persistence and seasonal baselines are often required.

## Cross-Domain Metrics

Use for v10 domain-specific tasks.

Each domain needs native metrics.

Examples:

- finance: out-of-sample return, drawdown, turnover, benchmark-relative performance.
- typhoon: track error by forecast horizon.
- protein: Q3 or secondary-structure accuracy against held-out labels.
- physics simulation: conservation residual and numerical error versus reference.
- social decision: regret, fairness metric, and intervention stability.
- math reasoning: exact-match and step-validity score.

Domain metrics must be reported separately.

## Confidence Intervals

Use bootstrap intervals when sample pairing is available.

Use temporal block bootstrap for time-series data when appropriate.

Report:

- interval method,
- resampling count,
- seed,
- unit of resampling.

## Multiple Comparisons

When many models, formats, or domains are compared, the report must identify:

- primary comparison,
- secondary comparisons,
- exploratory comparisons.

Adjusted interpretation is required for large comparison families.

## Minimum Result Table

Every confirmatory report should include:

- stage,
- dataset or fixture version,
- baseline,
- treatment,
- sample count,
- primary metric,
- baseline score,
- treatment score,
- delta,
- confidence interval,
- failure rate,
- environment ID,
- commit SHA.
