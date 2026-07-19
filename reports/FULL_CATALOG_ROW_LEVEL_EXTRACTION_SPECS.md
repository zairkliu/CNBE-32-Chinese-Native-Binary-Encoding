# Full Catalog Row-Level Extraction Specs

## Purpose

This report defines read-only extraction specifications for the seven
automatable GF0017 evidence items identified by the source-resolution
plan.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_ROW_LEVEL_EXTRACTION_SPECS_READY`
- Next workflow status: `ROW_LEVEL_EVIDENCE_JOIN_RUNNERS_ALLOWED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- Extraction specs: `7`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Extraction Specs

- `stroke_shape`: `extract_stroke_shape_evidence_v1` -> `stroke_evidence`; blocked_rows=89581
- `stroke_order`: `extract_stroke_order_evidence_v1` -> `stroke_evidence`; blocked_rows=89581
- `component_validity`: `extract_component_inventory_v1` -> `component_evidence`; blocked_rows=89581
- `component_name_validity`: `extract_component_name_validation_v1` -> `component_evidence`; blocked_rows=89581
- `radical_validity`: `extract_radical_evidence_v1` -> `radical_evidence`; blocked_rows=89581
- `independent_character_rule`: `extract_independent_character_status_v1` -> `structure_evidence`; blocked_rows=89581
- `structure_first_decomposition`: `extract_structure_decomposition_v1` -> `structure_evidence`; blocked_rows=89581

## Validation Rules

### stroke_shape
- unicode must match source character when present
- stroke_shape must be non-empty before item validation
- cross-reference evidence cannot become direct_standard without source anchor
### stroke_order
- stroke_order length must equal stroke_count when both are present
- stroke order values must use the normalized stroke code domain
- missing outside-8105 evidence remains ROW_LEVEL_EVIDENCE_JOIN_PENDING
### component_validity
- component list must preserve raw source form
- component evidence must distinguish standard-derived and contextual sources
- unknown decomposition markers remain blockers
### component_name_validity
- component names must be traceable to component-name inventory
- OCR-only names remain review aids
- name mismatch does not auto-repair CNBE rows
### radical_validity
- numeric radical code must be validated separately from radical text
- RSIndex is cross-reference unless promoted by explicit project policy
- radical mismatch remains a repair candidate only after evidence review
### independent_character_rule
- independent characters must not be split into invalid non-stroke components
- unknown independent status remains pending
- structure labels do not override independent-character evidence
### structure_first_decomposition
- final structure label must be one of the 13 approved Agent labels
- legacy English labels must be preserved as raw evidence
- decomposition ambiguity blocks scoring

## Decision

Extraction specifications are ready for read-only evidence join runners. Formal scoring remains blocked until runner output is reviewed and policy items are resolved.

The next allowed implementation step is a read-only evidence join
runner. Formal scoring, database reconstruction, and CNBE row writes
remain blocked.

## Next Artifacts

- `scripts/run_full_catalog_row_level_extraction_specs.py`
- `reports/full_catalog_row_level_extraction_results.json`
- `reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_RESULTS.md`
