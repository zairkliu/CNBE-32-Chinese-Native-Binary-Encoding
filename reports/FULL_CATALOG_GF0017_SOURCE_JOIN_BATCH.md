# Full Catalog GF0017 Source-Join Batch

## Purpose

This report runs a full 97,686-row source-join assessment for the v4_fixed
catalog. It separates rows with direct 8105 structured evidence from rows
that require Agent-standard mapping.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_SOURCE_JOIN_BATCH_ASSESSED`
- Next workflow status: `FORMAL_SCORING_BLOCKED_SOURCE_EVIDENCE_JOIN_REQUIRED`
- Total rows: `97686`
- Blocker count: `0`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`

## Join Status Counts

- `JOINED_8105_STANDARD_DERIVED_KNOWLEDGE`: 8105
- `OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED`: 89581

## GF0017 Source Item Statuses

- `character_set_coverage`: `SOURCE_GAP`
- `stroke_shape`: `SOURCE_GAP`
- `stroke_order`: `SOURCE_EVIDENCE_REQUIRED`
- `component_validity`: `SOURCE_EVIDENCE_REQUIRED`
- `component_name_validity`: `SOURCE_EVIDENCE_REQUIRED`
- `radical_validity`: `SOURCE_EVIDENCE_REQUIRED`
- `independent_character_rule`: `SOURCE_EVIDENCE_REQUIRED`
- `structure_first_decomposition`: `SOURCE_EVIDENCE_REQUIRED`

## Decision

Source-join batch assessment completed. Formal scoring remains blocked because SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED item statuses must be resolved into per-row evidence.

The next allowed step is Agent-standard mapping design for rows outside
the direct 8105 baseline. Formal scoring and database reconstruction
remain blocked.

## Next Artifacts

- `reports/full_catalog_agent_standard_mapping_plan.json`
- `reports/FULL_CATALOG_AGENT_STANDARD_MAPPING_PLAN.md`
- `scripts/plan_full_catalog_agent_standard_mapping.py`
