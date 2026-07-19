# Full Catalog GF0017 Batch Readiness

## Purpose

This report evaluates whether the 97,686-row v4_fixed catalog can enter
a source-join batch assessment.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_READY_FOR_SOURCE_JOIN_BATCH`
- Next workflow status: `SOURCE_JOIN_BATCH_ALLOWED_FORMAL_SCORING_BLOCKED`
- Total rows: `97686`
- 8105 baseline rows: `8105`
- Source join batch allowed: `True`
- Formal GF0017 scoring allowed: `False`

## Row Status Counts

- `AGENT_STANDARD_MAPPING_REQUIRED`: 89581
- `READY_8105_DIRECT_BASELINE_ASSESSMENT`: 8105

## Remaining Source-Gate Classes

- SOURCE_GAP items: `character_set_coverage`, `stroke_shape`
- SOURCE_EVIDENCE_REQUIRED items: `stroke_order`, `component_validity`, `component_name_validity`, `radical_validity`, `independent_character_rule`, `structure_first_decomposition`

## Decision

Rows are ready for a source-join batch assessment. Formal GF0017 scoring remains blocked until SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED items are joined to per-row evidence.

The next allowed step is source-join batch assessment. Formal scoring
and database reconstruction remain blocked.

## Next Artifacts

- `reports/full_catalog_gf0017_source_join_batch.json`
- `reports/FULL_CATALOG_GF0017_SOURCE_JOIN_BATCH.md`
- `scripts/run_full_catalog_gf0017_source_join_batch.py`
