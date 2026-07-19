# Structure/Decomposition Evidence Review Plan

## Purpose

This report turns Phase 1 parser output into review queues. It does not
accept evidence, assign GF0017 scores, modify source assets, write CNBE
rows, rebuild databases, create tags, publish releases, or upload to
PyPI.

## Result

- Overall status: `PASS_PHASE_1_EVIDENCE_REVIEW_PLAN_READY`
- Next workflow status: `SOURCE_GAP_RESOLUTION_AND_HUMAN_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- GF0017 item: `structure_first_decomposition`
- Dominant blocker: `MISSING_STRUCTURE`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`

## Review Queues

- `human_review_ready`: 2551 rows; action: review source anchors, confirm 13-label structure, keep as evidence candidate only
- `partial_evidence_review`: 2029 rows; action: inspect component-only or cross-reference evidence before accepting any structure label
- `source_gap_resolution_required`: 85001 rows; action: do not infer structure; route to source-expansion or manual evidence acquisition plan

## Failure Code Counts

- `AMBIGUOUS_DECOMPOSITION`: 148
- `MISSING_DECOMPOSITION_COMPONENTS`: 84773
- `MISSING_STRUCTURE`: 84936

## Decision

Phase 1 review planning is complete. The parser output exposes a large source gap, so formal scoring and CNBE row writes remain blocked until source-gap resolution and human review occur.
