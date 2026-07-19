# Full Catalog Source Resolution Plan

## Purpose

This report plans how to resolve source gaps and row-level evidence
pending statuses for the 89,581 outside-8105 Agent-standard mapping
candidates.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_SOURCE_RESOLUTION_PLAN_READY`
- Next workflow status: `ROW_LEVEL_EXTRACTION_SPECS_ALLOWED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- GF0017 items: `8`
- Automated resolution items: `7`
- Policy decision items: `1`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Resolution Classes

- `POLICY_DECISION_REQUIRED`: 1
- `ROW_LEVEL_EXTRACTION_REQUIRED`: 6
- `SOURCE_EXTRACTION_SPEC_REQUIRED`: 1

## GF0017 Item Plan

- `character_set_coverage` (3 pts): `POLICY_DECISION_REQUIRED`; rows=89581; next=`define_project_scope_scoring_policy_before_points`
- `stroke_shape` (3 pts): `SOURCE_EXTRACTION_SPEC_REQUIRED`; rows=89581; next=`build_stroke_shape_extraction_spec`
- `stroke_order` (3 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_stroke_order_join_runner`
- `component_validity` (3 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_component_inventory_join_runner`
- `component_name_validity` (8 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_component_name_validation_join_runner`
- `radical_validity` (3 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_radical_evidence_join_runner`
- `independent_character_rule` (7 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_independent_character_join_runner`
- `structure_first_decomposition` (20 pts): `ROW_LEVEL_EXTRACTION_REQUIRED`; rows=89581; next=`build_structure_decomposition_join_runner`

## Work Packages

- `SRP1_policy_scope_boundary`: automation_allowed=`False`; items=character_set_coverage
- `SRP2_row_level_extraction_specs`: automation_allowed=`True`; items=stroke_shape, stroke_order, component_validity, component_name_validity, radical_validity, independent_character_rule, structure_first_decomposition
- `SRP3_evidence_join_runners`: automation_allowed=`True`; items=stroke_shape, stroke_order, component_validity, component_name_validity, radical_validity, independent_character_rule, structure_first_decomposition
- `SRP4_scoring_gate_review`: automation_allowed=`False`; items=character_set_coverage, stroke_shape, stroke_order, component_validity, component_name_validity, radical_validity, independent_character_rule, structure_first_decomposition

## Agent Model Stage

- Stage id: `source_resolution`
- Automatic until: `row_level_extraction_specs`
- Invariants:
  - `unicode_identity_is_preserved`
  - `national_standard_and_agent_standard_are_distinct`
  - `source_gap_is_not_success`
  - `row_level_pending_evidence_is_not_a_score`
  - `cnbe_rows_are_not_modified`
  - `database_is_not_rebuilt`

## Decision

Source-resolution planning is ready. The Agent may continue with read-only row-level extraction specs, but formal scoring remains blocked by scope policy and unresolved row-level evidence.

The next allowed implementation step is a read-only row-level
extraction-spec design. Formal scoring, database reconstruction, and
CNBE row writes remain blocked.

## Next Artifacts

- `scripts/design_full_catalog_row_level_extraction_specs.py`
- `reports/full_catalog_row_level_extraction_specs.json`
- `reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_SPECS.md`
- `docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md`
