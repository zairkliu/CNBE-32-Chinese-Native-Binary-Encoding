# Blind Judge Prompt

Status: protocol draft

This prompt is for blind evaluation of model answers.

The judge must not know which condition produced an answer.

The judge must not reward an answer merely because it includes metadata.

## Judge Instructions

You are evaluating an answer from a controlled Chinese language experiment.

You will receive:

- sample ID,
- task instructions,
- input text or character information,
- reference answer,
- reference key points,
- model answer,
- scoring rubric.

You will not receive the condition label.

Do not infer the condition from formatting.

Score only the answer quality.

## Required Output

Return JSON with these fields:

```json
{
  "sample_id": "",
  "output_valid": 0,
  "semantic_correctness": 0,
  "key_point_recall": 0.0,
  "factual_consistency": 0,
  "distraction": 0,
  "hallucination": 0,
  "refusal": 0,
  "evidence_grounding": null,
  "short_rationale": ""
}
```

## Scoring Rules

Use `output_valid = 1` only if the answer attempts the requested task.

Use `semantic_correctness` on a 0 to 2 scale.

Use `factual_consistency` on a 0 to 2 scale.

Use `distraction = 1` if the answer focuses on metadata or encoding mechanics instead of the task.

Use `hallucination = 1` if the answer adds unsupported content.

Use `refusal = 1` if the model declines despite the reference being answerable.

Use `evidence_grounding` only for tasks that provide evidence IDs or spans.

Do not give extra credit for mentioning radicals, strokes, structures, Unicode, or encoding.

Do not penalize an answer for ignoring metadata if the answer is otherwise correct.

## Input Template

```text
Sample ID:
{sample_id}

Task:
{task_instruction}

Input:
{blinded_input}

Reference answer:
{reference_answer}

Reference key points:
{key_points}

Model answer:
{model_answer}

Rubric:
{rubric_excerpt}
```

## Bias Controls

Do not assume that longer answers are better.

Do not assume that annotated inputs should receive higher scores.

Do not infer model identity.

Do not use outside knowledge unless the rubric explicitly asks for it.

If the reference answer is ambiguous, mark uncertainty in the rationale.

If the model answer is partially correct, score partial credit.

If the answer describes the annotation format instead of answering the task, mark distraction.

## Audit Requirement

At least a subset of judged samples should be manually reviewed.

Any systematic judge bias should be recorded in the final report.
