# v5-v10 Confirmatory Report Template

Status: protocol draft

Use this template for future v5-v10 completed reports.

Do not use this template to report planned work as completed work.

## Title

Use the format:

```text
CNBE-32 vX.Y Confirmatory Report: <short task name>
```

## Status

State exactly one:

- protocol only,
- pilot run,
- smoke test,
- confirmatory run,
- failed run,
- exploratory appendix.

## Scope

Describe:

- stage,
- research question,
- dataset or fixture,
- baseline,
- treatment,
- runtime or model family.

## Non-Goals

List what the report does not claim.

At minimum, state whether the report does not claim:

- production readiness,
- universal CNBE effectiveness,
- financial advice,
- scientific proof,
- hardware readiness,
- full CJK validation.

## Methods

Include:

- commit SHA,
- command lines,
- dependency versions,
- model IDs or toolchain versions,
- random seeds,
- input manifest,
- scoring script,
- exclusion policy.

## Dataset or Fixture

Include:

- source,
- sample count,
- split method,
- leakage control,
- class or stratum distribution,
- known limitations.

For hardware and compiler tests, list fixtures and expected outputs.

## Conditions

For each condition, include:

- name,
- description,
- input construction method,
- token count or resource cost when relevant,
- baseline relationship.

## Metrics

State:

- primary metric,
- secondary metrics,
- failure metrics,
- statistical method,
- confidence interval method.

## Results

Include tables with:

- baseline score,
- treatment score,
- delta,
- confidence interval,
- sample count,
- failure rate.

For cross-domain tests, provide one table per domain.

## Error Analysis

Include:

- representative failures,
- invalid outputs,
- hallucinations,
- trace mismatches,
- temporal leakage checks,
- domain-specific failure modes.

## Interpretation

Use bounded language:

```text
Under this dataset, runtime, and protocol, the treatment showed / did not show measurable improvement relative to the stated baseline.
```

Do not generalize beyond the tested setup.

## Reproducibility

Include:

- raw artifact locations,
- hashes,
- environment notes,
- rerun instructions.

## Approval Boundary

State whether the report authorizes:

- merge,
- tag,
- release,
- PyPI publication,
- hardware claim,
- downstream experiment.

If not explicitly authorized, the default is no.
