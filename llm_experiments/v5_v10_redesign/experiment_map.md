# v5-v10 Experiment Map

Status: protocol draft

This document maps historical v5-v10 experiment artifacts to redesigned confirmatory stages.

The map is organizational only.

It does not endorse historical claims as final evidence.

## v5 Model Comparison

Historical artifacts include model comparison reports such as:

- v5 intent classification,
- v5.5 three-model comparison,
- v5.6 hybrid model comparison,
- v5.7 Qwen-family comparison,
- v5.8 Qwen-family and cross-architecture comparison,
- v5.9 seven-model comparison.

Redesigned stage:

- controlled multi-model comparison,
- fixed prompts,
- fixed input order,
- blind scoring,
- family-level and size-level stratification.

Primary evidence type:

- model behavior under controlled prompts.

Not evidence for:

- general CNBE validity,
- model training benefit,
- deployment readiness.

## v6 Numerical Features

Historical artifacts include:

- skill lookup acceleration,
- Qwen-family text understanding,
- domestic and international model comparisons,
- numerical feature validation,
- large-scale numerical feature validation,
- format comparisons,
- CNBE versus Unicode comparisons,
- hard-task comparisons.

Redesigned stage:

- numeric metadata ablation,
- same-length random control,
- shuffled numeric control,
- cost-adjusted performance analysis,
- task-type stratification.

Primary evidence type:

- whether structured numeric fields add signal beyond text, prompt length, or format effects.

Not evidence for:

- universal numerical superiority,
- complete CJK coverage,
- downstream hardware speedup.

## v7 Hardware Validation

Historical artifacts are mostly under `results/v7_riscv_hardware/`.

They include:

- initial RISC-V hardware validation,
- custom instruction validation,
- Spike integration,
- FPGA prototype validation,
- hardware encoding and feature-space cooperation.

Redesigned stage:

- ISA semantics validation,
- deterministic assembler/disassembler tests,
- emulator trace comparison,
- hardware prototype trace comparison when available.

Primary evidence type:

- implementation conformance for a defined instruction subset.

Not evidence for:

- production silicon readiness,
- operating-system readiness,
- full compiler correctness.

## v8 Hardware System

Historical artifacts include:

- Chinese programming mapping,
- compiler and skill table integration,
- Spike end-to-end validation,
- Chinese operating-system prototypes,
- text reader and Daodejing demos.

Redesigned stage:

- compiler correctness tests,
- runtime behavior tests,
- system integration smoke tests,
- reproducible emulator logs.

Primary evidence type:

- whether a defined toy language and system path can compile and execute under controlled conditions.

Not evidence for:

- complete OS maturity,
- production programming language readiness,
- broad hardware ecosystem support.

## v9 JEPA Prediction

Historical artifacts include:

- JEPA prediction ability,
- lifecycle prediction,
- financial crisis prediction,
- tick-data ablation,
- monthly robustness validation.

Redesigned stage:

- predictive modeling benchmark,
- temporal split enforcement,
- leakage audit,
- naive and domain-native baselines,
- ablation of CNBE representation.

Primary evidence type:

- predictive utility on fixed datasets under time-aware validation.

Not evidence for:

- financial advice,
- reliable crisis prediction,
- general causal understanding.

## v10 Cross-Domain Validation

Historical artifacts include:

- market backtests,
- A-share cross-market validation,
- time-scale validation,
- six-month cycle validation,
- typhoon path prediction,
- protein secondary structure prediction,
- black-hole gravitational simulation,
- social information distribution,
- pretraining base validation,
- mathematical reasoning validation.

Redesigned stage:

- domain-by-domain benchmark protocols,
- domain-native baselines,
- time or split isolation,
- uncertainty reporting,
- per-domain failure criteria.

Primary evidence type:

- whether a representation or feature scheme has measurable utility in a specific domain.

Not evidence for:

- universal cross-domain transfer,
- scientific correctness,
- deployable forecasting systems.
