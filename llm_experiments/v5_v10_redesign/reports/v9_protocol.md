# v9 Protocol: JEPA-Style Prediction Validation

Status: protocol draft

This document defines the redesigned v9 experiment family.

It does not report completed results.

## Purpose

v9 tests whether CNBE-derived representations improve predictive tasks under leakage-safe validation.

The historical v9 series includes JEPA prediction, lifecycle prediction, financial crisis prediction, tick-data ablation, and monthly robustness tests.

The redesigned protocol treats those as predictive modeling experiments requiring strict temporal controls.

## Research Question

Do CNBE-derived representations improve out-of-sample prediction relative to naive, domain-native, and non-CNBE representation baselines?

## Dataset Rules

Every dataset must define:

- entity ID,
- timestamp,
- feature timestamp,
- target timestamp,
- split cutoff,
- target label,
- baseline features,
- CNBE-derived features,
- missing-data policy.

Future information must not appear in features.

Random train/test splits are prohibited for temporal forecasting unless justified as non-temporal.

## Baselines

Required baselines:

- naive persistence,
- seasonal or rolling baseline when applicable,
- domain-native feature model,
- non-CNBE representation model,
- shuffled CNBE representation.

The baseline must be strong enough to be meaningful.

## Metrics

Primary metric depends on target type.

For regression:

- mean absolute error,
- root mean squared error,
- benchmark-relative skill score.

For classification:

- macro F1,
- precision,
- recall,
- Brier score when probabilistic.

For rare events:

- precision at k,
- recall at k,
- false-alarm rate,
- calibration.

## Validation

Use:

- time-based holdout,
- rolling-origin evaluation when feasible,
- no tuning on final test period,
- leakage audit,
- feature timestamp audit.

## Ablations

Required ablations:

- remove CNBE features,
- shuffle CNBE features across entities,
- use random same-dimensional features,
- compare compact versus full representation when applicable.

## Failure Conditions

The v9 run is invalid if:

- future labels leak into features,
- random split breaks temporal causality,
- no naive baseline is used,
- no non-CNBE representation baseline is used,
- financial or crisis results are framed as advice,
- only in-sample performance is reported.

## Reporting Boundary

Allowed conclusion:

```text
Under the specified temporal split and baseline set, CNBE-derived features improved / did not improve out-of-sample predictive metrics.
```

Disallowed conclusions:

- reliable crisis prediction,
- financial advice,
- causal proof,
- universal representation learning success,
- deployment readiness.
