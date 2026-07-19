# Structure/Decomposition Evidence Parser

## Purpose

This report is Phase 1 of the full-catalog parser workflow. It parses
structure and decomposition evidence for outside-8105 Agent-standard
candidate rows.

It does not assign GF0017 scores, modify cnbe-research source assets,
modify CNBE rows, rebuild databases, create tags, publish releases, or
upload to PyPI.

## Result

- Overall status: `PASS_PHASE_1_STRUCTURE_DECOMPOSITION_EVIDENCE_PARSED`
- Next workflow status: `PHASE_1_EVIDENCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- GF0017 item: `structure_first_decomposition`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`
- Source asset write allowed: `False`
- CNBE row write allowed: `False`

## Evidence Status Counts

- `STRUCTURE_DECOMPOSITION_EVIDENCE_GAP`: 85001
- `STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW`: 2551
- `STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED`: 2029

## Failure Code Counts

- `AMBIGUOUS_DECOMPOSITION`: 148
- `MISSING_DECOMPOSITION_COMPONENTS`: 84773
- `MISSING_STRUCTURE`: 84936

## Source Hit Counts

- `cjk_decomp`: 2635
- `component_mapping`: 2663
- `dictionary_record`: 2699

## Structure Label Counts

- `UNRESOLVED`: 84936
- `上三包`: 63
- `上下`: 1846
- `上中下`: 42
- `下三包`: 1
- `全包围`: 145
- `右上包`: 73
- `左三包`: 37
- `左上包`: 259
- `左下包`: 50
- `左中右`: 12
- `左右`: 2059
- `独体字`: 4
- `镶嵌`: 54

## Decision

Phase 1 parser produced read-only structure/decomposition evidence statuses. Human evidence review is required before any GF0017 score assignment or CNBE row repair.

Next allowed work is Phase 1 evidence review. Formal GF0017 scoring,
CNBE row writes, source-asset edits, and database rebuilds remain
blocked.
