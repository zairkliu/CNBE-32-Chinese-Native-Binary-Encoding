# Evaluation Rubric

Status: protocol draft

This rubric defines how outputs from the redesigned v1-v4 experiments should be scored.

The judge must not know the condition label.

The judge must score the answer, not the annotation style.

## Scoring Scale

Use a 0 to 2 scale unless a metric specifies otherwise.

- 0: absent or wrong,
- 1: partial,
- 2: correct or clearly sufficient.

Binary metrics should use:

- 0: no,
- 1: yes.

## Output Validity

An output is valid when it:

- answers the requested task,
- is not empty,
- is not only a refusal,
- is not only a restatement of metadata,
- follows the requested response format enough to score.

Invalid outputs receive zero for task-quality metrics.

## Semantic Correctness

Semantic correctness measures whether the answer captures the intended meaning.

Score 2 when:

- the central meaning is correct,
- no major contradiction is present,
- the answer is specific enough for the task.

Score 1 when:

- the answer is related but incomplete,
- one important nuance is missing,
- wording is vague but not misleading.

Score 0 when:

- the answer is unrelated,
- the answer contradicts the reference,
- the answer mostly describes metadata instead of the task.

## Key Point Recall

Key point recall measures how many reference key points are covered.

For each key point:

- 1 if clearly covered,
- 0.5 if partially covered,
- 0 if absent.

The sample score is:

covered key point credit divided by total key points.

## Factual Consistency

Factual consistency checks whether the answer stays supported by the input.

Score 2 when:

- claims are supported,
- no unsupported named entities are added,
- no unsupported causal claim is added.

Score 1 when:

- the answer is mostly supported,
- minor unsupported phrasing appears,
- no major false claim appears.

Score 0 when:

- the answer introduces a major false claim,
- the answer attributes unsupported evidence,
- the answer changes the source meaning.

## Distraction Rate

Distraction is present when the answer focuses on annotation mechanics rather than the requested task.

Mark distraction as 1 if the answer:

- describes radicals, strokes, structures, code fields, or encoding format when not requested,
- spends more than one short phrase on metadata mechanics,
- treats the annotation as the main object instead of the text.

Mark distraction as 0 if metadata is ignored or used only implicitly.

## Hallucination Rate

Hallucination is present when the answer adds unsupported content.

Examples:

- invented historical claims,
- invented definitions,
- invented source attribution,
- invented character meanings not supported by reference material,
- unsupported analysis of author intent.

Hallucination should be scored separately from semantic correctness.

## Refusal Rate

Refusal is present when the model declines despite the task being answerable.

Examples:

- "I do not know",
- "cannot determine",
- "insufficient information" when the reference is answerable,
- generic refusal not tied to a real ambiguity.

Genuine uncertainty may be acceptable when the condition hides key information.

## Evidence Grounding

Evidence grounding applies to v4.

Score 2 when:

- cited evidence supports the answer,
- evidence IDs or spans are relevant,
- the answer does not rely on outside knowledge.

Score 1 when:

- evidence is partially relevant,
- evidence supports only part of the answer,
- evidence IDs are broad but usable.

Score 0 when:

- evidence is missing,
- evidence does not support the answer,
- answer relies mostly on outside knowledge.

## Token Overhead Adjusted Score

Token overhead adjusted score penalizes large annotation cost.

The metric should compare score gain to token overhead.

A condition with large token cost and small quality gain should not be treated as a clear improvement.

## Reviewer Notes

Reviewers should record:

- unclear cases,
- possible prompt leakage,
- possible metadata distraction,
- references needed for adjudication,
- whether a second reviewer is required.

## Adjudication

Two reviewers should score a subset of samples.

Disagreements should be resolved by:

- checking the rubric,
- checking reference key points,
- recording the reason for final adjudication.

Reviewer agreement should be reported when human scoring is used.
