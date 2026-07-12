# CNBE-32 Full Catalog Reviewer Instructions

## Purpose

This file tells reviewers how to fill `reports/full_catalog_semantic_review_sample.csv`.

The sample is a review input, not a semantic authority claim. Filling the CSV does not authorize SDK replacement,
SQLite database construction, GitHub Release creation, or PyPI publication.

## Reviewer Fields

Each reviewer fills three judgment columns:

- `reviewer_a_radical` or `reviewer_b_radical`
- `reviewer_a_strokes` or `reviewer_b_strokes`
- `reviewer_a_structure` or `reviewer_b_structure`

Allowed values are:

- `agree`
- `disagree`
- `unclear`

Use `agree` when the sampled field is consistent with the cited source or review rule.

Use `disagree` when the sampled field conflicts with the cited source or review rule.

Use `unclear` when the evidence is insufficient, the source is ambiguous, or glyph interpretation requires additional
authority.

## Notes Fields

Use `reviewer_a_notes` and `reviewer_b_notes` for short evidence notes.

Good notes name the source and the reason. For example: `Unihan kTotalStrokes agrees after 31 clamp`.

Do not use notes to make project-wide claims. Notes should explain the sampled row only.

## Adjudication

Fill `adjudication` only after both reviewers finish.

Allowed values are:

- `accept`
- `revise`
- `exclude`
- `needs_source`
- `no_action`

Use `accept` when reviewers agree that the row is acceptable under the current evidence boundary.

Use `revise` when the catalog row probably needs a rule or data correction.

Use `exclude` when the row should not be used as support for semantic claims.

Use `needs_source` when a stronger external source must be cited before deciding.

Use `no_action` when a disagreement is understood but does not affect the current experimental boundary.

## Validation

Run the validator in template mode before review:

```bash
python scripts/validate_semantic_review_results.py
```

It should report `TEMPLATE_INCOMPLETE` while the reviewer columns are still blank.

Run strict mode after both reviewers and adjudication are complete:

```bash
python scripts/validate_semantic_review_results.py --strict
```

Strict mode must report `PASS` before this evidence can support any next-stage decision.

## Decision Boundary

Even a strict `PASS` does not automatically approve database construction or SDK replacement.

It only means the review CSV is complete, internally consistent, and ready for repository-admin review.

