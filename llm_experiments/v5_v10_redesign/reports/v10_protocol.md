# v10 Protocol: Cross-Domain Validation

Status: protocol draft

This document defines the redesigned v10 experiment family.

It does not report completed results.

## Purpose

v10 tests whether CNBE-derived features or protocols have measurable utility in specific non-text domains.

The historical v10 series spans market backtests, A-share validation, time-scale tests, typhoon paths, protein structure, black-hole simulation, social decision systems, pretraining bases, and mathematical reasoning.

The redesigned protocol requires one domain protocol per domain.

## Research Question

Does a CNBE-derived representation or method improve a specific domain task relative to a domain-native baseline under leakage-safe validation?

## Domain Separation

Each domain must be evaluated separately.

Required domain groups:

- finance and market backtesting,
- meteorology and typhoon tracking,
- protein secondary structure,
- physical simulation,
- social decision or information distribution,
- pretraining representation,
- mathematical reasoning.

No aggregate v10 score may hide per-domain failures.

## Finance Protocol

Required controls:

- time-based split,
- transaction cost,
- turnover,
- benchmark index,
- drawdown,
- walk-forward validation.

Disallowed claims:

- investment advice,
- guaranteed return,
- deployable trading strategy.

## Typhoon Protocol

Required controls:

- forecast horizon,
- track-error metric,
- official or standard baseline,
- storm-wise split,
- no future track leakage.

Report errors by forecast horizon.

## Protein Protocol

Required controls:

- train/test sequence split,
- homology leakage audit when possible,
- Q3 or task-native accuracy,
- comparison to simple sequence baseline.

Do not claim biological discovery from toy validation.

## Physical Simulation Protocol

Required controls:

- reference solver or analytic baseline,
- conservation residual,
- numerical error,
- timestep sensitivity,
- parameter range.

Do not claim scientific proof from visual similarity.

## Social Decision Protocol

Required controls:

- simulated policy baseline,
- fairness or allocation metric,
- regret or utility metric,
- stability under perturbation,
- harm analysis.

Do not claim social deployment readiness.

## Pretraining and Math Protocol

Required controls:

- non-CNBE tokenization or representation baseline,
- model-size control,
- data-budget control,
- exact-match and step-validity metrics,
- held-out test set.

Do not claim a better foundation model from prompt-only evidence.

## Metrics

Each domain report must include:

- primary domain metric,
- baseline,
- treatment,
- delta,
- confidence interval or uncertainty,
- failure rate,
- limitations.

## Failure Conditions

The v10 run is invalid if:

- domains are merged without per-domain tables,
- domain-native baselines are missing,
- time leakage exists,
- uncertainty is omitted,
- a demo is described as scientific proof,
- financial results are framed as advice,
- negative domains are hidden.

## Reporting Boundary

Allowed conclusion:

```text
In the tested domain and split, the CNBE-derived method showed / did not show measurable utility relative to the stated domain baseline.
```

Disallowed conclusions:

- universal cross-domain validation,
- guaranteed forecasting ability,
- scientific proof,
- deployable decision system,
- general pretraining superiority.
