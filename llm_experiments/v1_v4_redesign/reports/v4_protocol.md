# v4 Protocol: Long-Context Robustness

Status: protocol draft

This document defines the redesigned v4 experiment.

It does not report completed results.

## Purpose

v4 tests whether CNBE annotation remains useful in longer contexts.

It also tests whether full annotation becomes too expensive compared with selective annotation.

## Research Question

Does CNBE annotation improve long-context tasks after accounting for context length and annotation overhead?

## Hypothesis

Full annotation may help short passages but become costly in long contexts.

Selective annotation may offer a better practical tradeoff.

Random annotation should not provide the same evidence-grounded gains if CNBE fields are useful.

## Source Types

Use at least three source types:

- classical argument text,
- modern policy or news article,
- technical explanatory text.

Each source should be segmented into:

- paragraph-level units,
- section-level units,
- full-document units.

## Conditions

Every sample appears in:

- pure text,
- selective CNBE,
- full CNBE,
- random annotation with similar length.

Optional:

- radical-only selective annotation.

## Tasks

v4 must include:

- paragraph summary,
- argument extraction,
- concept question answering,
- cross-paragraph evidence lookup,
- distractor robustness.

Each task needs reference answers and evidence spans.

## Prompting

Use `prompts/v4_long_context.yaml`.

The model must cite evidence IDs when the task asks for evidence.

Condition labels must be hidden from judges.

The prompt should not imply that metadata is helpful.

## Metrics

Primary metric:

- evidence-grounded correctness.

Secondary metrics:

- key-point recall,
- factual consistency,
- hallucination rate,
- evidence precision,
- evidence recall,
- refusal rate,
- token overhead adjusted score,
- long-context degradation.

## Long-Context Degradation

Compute degradation by comparing performance across:

- paragraph context,
- section context,
- full-document context.

Formula:

```text
degradation = score(paragraph) - score(full_document)
```

Report degradation per condition.

## Evidence Grounding

A correct answer should cite relevant evidence.

For each answer, record:

- required evidence IDs,
- cited evidence IDs,
- evidence precision,
- evidence recall.

If an answer is correct but unsupported by cited evidence, report the split.

## Statistical Tests

Use paired bootstrap intervals for score deltas.

Use McNemar tests for binary correctness and hallucination.

Stratify results by:

- source type,
- context level,
- task type,
- model family.

## Interpretation

Allowed conclusion template:

```text
Under the tested long-context tasks, selective CNBE showed / did not show a better cost-adjusted tradeoff than full CNBE.
```

It is acceptable for the final result to be null or mixed.

It is acceptable to conclude that annotation overhead dominates in long contexts.

## Failure Conditions

The v4 run is invalid if:

- evidence spans are missing,
- no random annotation control is used,
- token overhead is not reported,
- long-context levels are mixed without stratification,
- the model relies on outside knowledge and the report ignores that issue.

## Expected Report Sections

A completed v4 report should include:

- source manifest,
- segmentation method,
- task definitions,
- model matrix,
- context-length table,
- evidence-grounded score table,
- selective versus full annotation comparison,
- failure analysis,
- practical recommendation.
