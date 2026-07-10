# CNBE-32 v5-v10 Confirmatory Protocol

Status: protocol draft

This document defines the shared confirmatory protocol for redesigned v5-v10 experiments.

It is a design document only.

It does not report completed results.

## 1. Research Questions

RQ1: Do controlled model-comparison experiments show stable CNBE-related effects across model families?

RQ2: Do CNBE numerical fields add measurable signal after controlling for annotation length and prompt format?

RQ3: Can CNBE-related hardware instructions be specified, encoded, decoded, and executed reproducibly?

RQ4: Can a CNBE-oriented language or system prototype pass defined compiler and runtime tests?

RQ5: Do CNBE-derived representations improve prediction under leakage-safe temporal validation?

RQ6: Do cross-domain experiments show domain-specific utility beyond native baselines?

## 2. Evidence Separation

The protocol separates six evidence classes:

- LLM prompt behavior,
- numeric annotation behavior,
- ISA and emulator conformance,
- compiler and system integration,
- predictive representation utility,
- cross-domain applied modeling.

These evidence classes must not be merged into one headline score.

Each class has its own baselines, risks, and failure conditions.

## 3. Shared Rules

Every experiment must define:

- task,
- input source,
- sample split,
- baseline,
- treatment,
- model or runtime version,
- random seed,
- metric,
- failure condition,
- reporting boundary.

Every experiment must retain:

- raw input manifest,
- raw outputs,
- scoring outputs,
- environment information,
- code revision,
- data revision.

## 4. Baseline Requirements

No experiment may proceed without a baseline.

Acceptable baseline classes include:

- plain text,
- Unicode-only,
- radical-only,
- same-length random annotation,
- shuffled CNBE fields,
- non-CNBE numeric features,
- native domain model,
- naive persistence forecast,
- standard RISC-V instruction,
- reference compiler output,
- emulator trace without custom instruction.

The chosen baseline must match the research question.

## 5. Randomization

LLM experiments must randomize:

- sample order,
- condition order,
- prompt ordering when few-shot examples are used.

Prediction experiments must not randomize temporal order in ways that leak future information.

Hardware experiments must use deterministic traces.

Compiler experiments must use deterministic fixture ordering.

## 6. Split Discipline

Dataset splits must be fixed before scoring.

Temporal datasets must use time-aware splits.

Cross-domain datasets must use domain-specific holdout rules.

No final result should use pilot data.

No threshold should be tuned on the final test split.

## 7. Evaluation Discipline

The primary metric must be selected before execution.

Secondary metrics must be labeled as secondary.

Exploratory analyses must be labeled as exploratory.

Human or judge-assisted scoring must be blinded when condition labels could bias scoring.

## 8. Statistical Requirements

Reports must include:

- sample count,
- baseline score,
- treatment score,
- delta,
- confidence interval when applicable,
- test type when applicable,
- effect size,
- failure-rate table,
- per-stratum breakdown.

Small demonstrations may be labeled as smoke tests only.

Smoke tests must not be used as confirmatory evidence.

## 9. Reproducibility Requirements

Every completed run must record:

- repository commit,
- branch,
- command line,
- dependency versions,
- operating system,
- hardware or API provider,
- model IDs,
- random seeds,
- input manifest hash,
- output artifact hash.

For hardware and compiler experiments, reports must include exact toolchain versions.

For API model experiments, reports must include run date and provider model ID.

## 10. Failure Criteria

The protocol fails if:

- no baseline is present,
- condition labels leak into blinded scoring,
- final data are edited after seeing outputs,
- a single demo is reported as broad validation,
- future data leak into predictive training,
- hardware trace logs are missing,
- compiler outputs are manually corrected without audit,
- prompt templates change mid-run,
- model versions are not recorded.

## 11. Reporting Boundaries

Allowed language:

```text
Under the tested dataset, model/runtime, and protocol, the treatment showed / did not show a measurable effect relative to the stated baseline.
```

Disallowed language:

- universal effectiveness,
- production readiness,
- financial forecasting reliability,
- scientific proof,
- complete hardware validation,
- complete operating-system readiness,
- complete CJK coverage.
