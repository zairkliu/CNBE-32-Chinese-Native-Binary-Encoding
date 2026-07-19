# Full Catalog Agent-Standard Mapping Plan

## Purpose

This report plans the next read-only stage for the 89,581 full-catalog
rows outside the direct 8105 baseline.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_AGENT_STANDARD_MAPPING_PLAN_READY`
- Next workflow status: `ROW_LEVEL_EVIDENCE_JOIN_PLAN_REQUIRED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- Unicode identity gaps: `0`
- Agent-standard mapping design allowed: `True`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`

## Plane Counts

- `BMP`: 19675
- `SUPPLEMENTARY`: 69906

## Unicode Block Counts

- `CJK Unified Ideographs`: 13160
- `CJK Unified Ideographs Extension A`: 6515
- `CJK Unified Ideographs Extension B`: 42684
- `CJK Unified Ideographs Extension C`: 4116
- `CJK Unified Ideographs Extension D`: 214
- `CJK Unified Ideographs Extension E`: 5666
- `CJK Unified Ideographs Extension F`: 7473
- `CJK Unified Ideographs Extension G`: 4939
- `CJK Unified Ideographs Extension H`: 4192
- `CJK Unified Ideographs Extension I`: 622

## GF0017 Gate Plan

- `character_set_coverage` (3 pts): `SOURCE_GAP` -> resolve_controlling_source_or_keep_unscored
- `stroke_shape` (3 pts): `SOURCE_GAP` -> resolve_controlling_source_or_keep_unscored
- `stroke_order` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring
- `component_validity` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring
- `component_name_validity` (8 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring
- `radical_validity` (3 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring
- `independent_character_rule` (7 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring
- `structure_first_decomposition` (20 pts): `SOURCE_EVIDENCE_REQUIRED` -> build_row_level_evidence_join_before_scoring

## Work Packages

- `WP1_unicode_and_scope`: Preserve Unicode identity and classify each outside-8105 row by Unicode block and plane.
- `WP2_legacy_field_localization`: Treat legacy CNBE fields as non-authoritative hints and localize only through Agent standard tables.
- `WP3_source_evidence_join`: Join row-level stroke, component, radical, independent-character, and decomposition evidence.
- `WP4_agent_mapping_candidate_generation`: Generate Agent-standard mapping candidates only after WP3 resolves evidence status per row.

## Decision

Outside-8105 rows are stratified and ready for row-level evidence join planning. They remain Agent-standard mapping candidates, not national-standard outputs.

The next allowed implementation step is a row-level evidence join
design. Formal scoring, database reconstruction, and CNBE row writes
remain blocked.

## Next Artifacts

- `scripts/design_full_catalog_agent_mapping_evidence_join.py`
- `reports/full_catalog_agent_mapping_evidence_join_design.json`
- `reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN_DESIGN.md`
