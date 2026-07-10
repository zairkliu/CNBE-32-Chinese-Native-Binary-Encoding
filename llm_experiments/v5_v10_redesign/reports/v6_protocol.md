# v6 Protocol: Numerical Feature and Format Ablation

Status: protocol draft

This document defines the redesigned v6 experiment family.

It does not report completed results.

## Purpose

v6 tests whether CNBE numerical fields add useful information beyond text, annotation length, and prompt format.

The historical v6 series explored numerical injection, skill lookup, CNBE versus Unicode, hard tasks, and model comparisons.

The redesigned protocol makes those comparisons falsifiable.

## Research Question

Do structured CNBE numeric fields improve task performance after controlling for annotation length and shuffled-field effects?

## Hypotheses

H1: Numeric fields may help tasks where radical, structure, or stroke features are relevant.

H2: Numeric fields may distract models on tasks where semantics are already obvious.

H3: Compact or selective formats may outperform full annotation by cost-adjusted score.

## Dataset

The dataset must include:

- ordinary text samples,
- rare-character samples,
- classical text samples,
- hard ambiguity samples,
- negative-control samples where numeric features should not help.

Every sample must define:

- reference answer,
- key points,
- relevant characters,
- CNBE fields,
- Unicode fields,
- radical fields,
- difficulty label.

## Conditions

Required conditions:

- text only,
- Unicode only,
- radical only,
- CNBE numeric full,
- CNBE numeric compact,
- shuffled CNBE numeric,
- random numeric same-length,
- selective CNBE numeric.

## Metrics

Primary metric:

- cost-adjusted key-point recall.

Secondary metrics:

- semantic correctness,
- factual consistency,
- distraction rate,
- token overhead,
- invalid-output rate,
- hallucination rate.

## Cost Discipline

Reports must include:

- input token count,
- output token count,
- total token count,
- overhead ratio,
- score gain,
- cost-adjusted gain.

If score improves only because output becomes longer, the report must state that.

## Statistical Plan

Use paired bootstrap intervals over sample IDs.

Compare CNBE numeric full and selective CNBE against:

- text only,
- radical only,
- shuffled CNBE,
- random same-length numeric annotation.

Report results by task type.

## Failure Conditions

The v6 run is invalid if:

- random same-length control is missing,
- shuffled numeric control is missing,
- token overhead is not reported,
- prompt formats change during final evaluation,
- hard tasks are selected after seeing model outputs,
- output validity is treated as the only success metric.

## Reporting Boundary

Allowed conclusion:

```text
Under the tested task strata, CNBE numeric fields showed / did not show cost-adjusted signal beyond matched controls.
```

Disallowed conclusions:

- CNBE numeric fields are universally better than Unicode,
- all numerical injection formats are effective,
- LLM performance implies hardware performance,
- hard-task success proves complete CJK understanding.
