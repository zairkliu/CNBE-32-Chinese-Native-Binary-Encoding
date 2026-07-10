# CNBE-32 v5-v10 Experiment Redesign

Status: protocol draft

This directory defines a redesigned protocol layer for CNBE-32 v5-v10 experiments.

It does not report completed results.

It does not replace historical reports under:

- `llm_experiments/v5_model_comparison/`
- `llm_experiments/v6_numerical_features/`
- `llm_experiments/v8_hardware_system/`
- `llm_experiments/v9_jepa_prediction/`
- `llm_experiments/v10_cross_domain/`
- `results/v5_model_comparison/`
- `results/v6_numerical_features/`
- `results/v7_riscv_hardware/`
- `results/v8_hardware_system/`
- `results/v9_jepa_prediction/`
- `results/v10_cross_domain/`

The historical reports remain exploratory artifacts.

The redesigned documents define what a confirmatory rerun must prove, what it must control, and what it must not claim.

## Coverage

The redesign covers six experiment families:

- v5: model comparison and intent classification.
- v6: numerical features and annotation format effects.
- v7: RISC-V hardware instruction validation.
- v8: Chinese programming and system integration.
- v9: JEPA-style predictive representation experiments.
- v10: cross-domain forecasting and simulation experiments.

## Redesign Goal

The goal is to separate evidence types.

LLM prompt behavior, numerical metadata effects, compiler correctness, ISA behavior, predictive modeling, and cross-domain forecasting should not be collapsed into one broad validation claim.

Each stage must define:

- a falsifiable research question,
- a baseline,
- a leakage-control rule,
- a metric,
- a failure condition,
- a reporting boundary.

## Key Principle

Every future report must distinguish:

- protocol,
- implementation,
- run environment,
- raw outputs,
- scoring,
- interpretation.

No future report should use a single positive demo as evidence for general CNBE effectiveness.

## Required Baselines

Every experiment family must include domain-appropriate controls.

Examples:

- v5 requires model-family and prompt-order controls.
- v6 requires same-length random numeric annotation controls.
- v7 requires baseline RISC-V instruction behavior and deterministic emulator logs.
- v8 requires clean-language and non-CNBE compiler baselines.
- v9 requires naive forecasting and non-CNBE representation baselines.
- v10 requires domain-native baselines and time-split validation.

## Non-Goals

This redesign does not:

- run any model,
- train any model,
- publish new benchmark scores,
- alter SDK behavior,
- change CNBE bit layout,
- change golden vectors,
- modify package data,
- tag a release,
- publish to PyPI,
- assert hardware readiness,
- assert forecasting reliability,
- assert universal LLM benefit.

## File Layout

- `protocol.md`: shared v5-v10 confirmatory protocol.
- `experiment_map.md`: mapping from historical experiment groups to redesigned stages.
- `evaluation_framework.md`: metrics and statistical requirements.
- `risk_register.md`: known validity risks and mitigations.
- `report_template.md`: required final report structure.
- `reports/v5_protocol.md`: model comparison protocol.
- `reports/v6_protocol.md`: numerical feature protocol.
- `reports/v7_protocol.md`: hardware validation protocol.
- `reports/v8_protocol.md`: system integration protocol.
- `reports/v9_protocol.md`: JEPA prediction protocol.
- `reports/v10_protocol.md`: cross-domain validation protocol.
