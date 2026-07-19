# Full Catalog Agent Mapping Evidence Join Design

## Purpose

This report designs the row-level evidence join needed before the
89,581 outside-8105 rows can be considered for Agent-standard mapping
candidates.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_EVIDENCE_JOIN_DESIGN_READY`
- Next workflow status: `ROW_LEVEL_EVIDENCE_JOIN_IMPLEMENTATION_ALLOWED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- Join output tables: `7`
- GF0017 items: `8`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Join Output Tables

- `unicode_identity`: one row per full-catalog character
- `scope_membership`: one row per character per scope source
- `stroke_evidence`: one row per character per stroke source
- `component_evidence`: one row per character per decomposition source
- `radical_evidence`: one row per character per radical source
- `structure_evidence`: one row per character per structure source
- `gf0017_item_evidence_status`: one row per character per GF0017 item

## GF0017 Item Join Rules

- `character_set_coverage` (3 pts): `SOURCE_GAP` -> `resolve_source_gap_before_scoring`
- `stroke_shape` (3 pts): `SOURCE_GAP` -> `resolve_source_gap_before_scoring`
- `stroke_order` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`
- `component_validity` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`
- `component_name_validity` (8 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`
- `radical_validity` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`
- `independent_character_rule` (7 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`
- `structure_first_decomposition` (20 pts): `SOURCE_EVIDENCE_REQUIRED` -> `build_row_level_evidence_join_before_scoring`

## Implementation Order

- Step 1: `materialize_unicode_identity_view`; allowed now: `True`
- Step 2: `materialize_scope_membership_view`; allowed now: `True`
- Step 3: `materialize_stroke_component_radical_structure_views`; allowed now: `True`
- Step 4: `join_gf0017_item_evidence_status`; allowed now: `True`
- Step 5: `assign_formal_gf0017_scores`; allowed now: `False`
- Step 6: `generate_or_repair_cnbe_rows`; allowed now: `False`

## Decision

The join design is ready for a read-only implementation pass. Formal scoring remains blocked until each row receives item-level evidence status.

The next allowed implementation step is a read-only row-level evidence
join runner. Formal scoring, database reconstruction, and CNBE row
writes remain blocked.

## Next Artifacts

- `scripts/run_full_catalog_agent_mapping_evidence_join.py`
- `reports/full_catalog_agent_mapping_evidence_join.json`
- `reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN.md`
