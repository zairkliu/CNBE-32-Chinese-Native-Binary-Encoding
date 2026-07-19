# Full Catalog Row-Level Extraction Results

## Purpose

This report materializes read-only extraction-status rows for the seven
automatable GF0017 evidence items.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_ROW_LEVEL_EXTRACTION_STATUS_MATERIALIZED`
- Next workflow status: `EVIDENCE_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- Extraction specs: `7`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Row Status Counts

- `ROW_EXTRACTION_SOURCES_AVAILABLE_PENDING`: 89581

## Item Status Counts

- `component_name_validity`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `component_validity`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `independent_character_rule`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `radical_validity`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `stroke_order`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `stroke_shape`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581
- `structure_first_decomposition`: `SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING`=89581

## Output Table Counts

- `component_evidence`: 179162
- `radical_evidence`: 89581
- `stroke_evidence`: 179162
- `structure_evidence`: 179162

## Decision

Extraction-status rows have been materialized from read-only specs. They confirm source availability and pending extraction work, but do not assign evidence values or points.

The next allowed implementation step is an evidence-review plan.
Formal scoring, database reconstruction, and CNBE row writes remain
blocked.

## Next Artifacts

- `scripts/plan_full_catalog_evidence_review.py`
- `reports/full_catalog_evidence_review_plan.json`
- `reports/FULL_CATALOG_EVIDENCE_REVIEW_PLAN.md`
