# Full Catalog Agent Mapping Evidence Join

## Purpose

This report materializes row-level evidence statuses for the 89,581
outside-8105 rows.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED`
- Next workflow status: `FORMAL_SCORING_BLOCKED_ROW_EVIDENCE_REQUIRES_SOURCE_RESOLUTION`
- Outside-8105 rows: `89581`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Row Status Counts

- `ROW_SOURCE_GAP_AND_EVIDENCE_JOIN_PENDING`: 89581

## Plane Counts

- `BMP`: 19675
- `SUPPLEMENTARY`: 69906

## GF0017 Item Evidence Counts

- `character_set_coverage`: `SOURCE_GAP_NOT_SCORABLE`=89581
- `component_name_validity`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581
- `component_validity`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581
- `independent_character_rule`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581
- `radical_validity`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581
- `stroke_order`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581
- `stroke_shape`: `SOURCE_GAP_NOT_SCORABLE`=89581
- `structure_first_decomposition`: `ROW_LEVEL_EVIDENCE_JOIN_PENDING`=89581

## Decision

Row-level evidence statuses have been materialized. Formal scoring remains blocked because SOURCE_GAP and ROW_LEVEL_EVIDENCE_JOIN_PENDING statuses remain for every outside-8105 row.

The next allowed step is a source-resolution plan. Formal scoring,
database reconstruction, and CNBE row writes remain blocked.

## Next Artifacts

- `scripts/plan_full_catalog_source_resolution.py`
- `reports/full_catalog_source_resolution_plan.json`
- `reports/FULL_CATALOG_SOURCE_RESOLUTION_PLAN.md`
