# 8105 Core Standard Source Join Pilot Plan

Overall status: `PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY`
Next workflow status: `READY_FOR_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_NO_SCORING`

## Scope

This report covers only the 100-row `8105_core_control` stratum from the existing 300-character pilot.
It does not regenerate the 97,686-row catalog, assign GF0017 points, emit final structure labels, write CNBE rows, rebuild a database, or generate an XLSX workbook.

## Summary

- Core pilot rows: 100
- Base 8105 rows: 8105
- Base Unicode matches: 100
- Stroke count/order joined: 100
- Structure standard-source extraction required: 100
- Decomposition standard-source extraction required: 100
- Dictionary context rows: 57
- GF0017 points assigned: 0
- Final structure labels emitted: 0
- CNBE rows written: 0

## Gate Checks

- core_row_count_matches: `True`
- base_8105_count_matches: `True`
- all_core_rows_found_in_base: `True`
- all_core_unicode_values_match: `True`
- all_core_stroke_fields_joined: `True`
- structure_decomposition_kept_pending: `True`
- no_gf0017_points_assigned: `True`
- no_final_structure_labels: `True`
- no_cnbe_rows_written: `True`
- no_database_rebuild: `True`
- no_xlsx_generated: `True`
- no_source_asset_write: `True`

## Boundary

`base_character_data.json` supplies standard-derived Unicode identity, 8105 level/rank, stroke count, and stroke order for this pilot control set.
`cnbe_character_knowledge.json` supplies dictionary context but no source-audited structure or decomposition fields for these rows.
The next allowed step is a separate standard-source extraction plan for structure and decomposition.
