# 8105 Core Structure Decomposition Source Extraction Plan

Overall status: `PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY`
Next workflow status: `READY_FOR_BOUNDED_STANDARDIZER_EXTRACTION_RUN_NO_SCORING`

## Scope

This is a bounded plan for the 100-row `8105_core_control` pilot stratum.
It prepares the input contract for `cnbe-hanzi-decomposition-standardizer`.
It does not extract final labels, assign GF0017 points, write CNBE rows, rebuild databases, or duplicate the full catalog.

## Summary

- Input rows: 100
- Handoff rows: 100
- Standard source records available: 8 / 8
- Unicode identity pass rows: 100
- Structure source required rows: 100
- Decomposition source required rows: 100
- Component-name source required rows: 100
- GF0017 points assigned: 0
- Final structure labels emitted: 0
- CNBE rows written: 0

## Standardizer Call

```text
skill: cnbe-hanzi-decomposition-standardizer
task_type: batch
input_path: review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv
input_scope: 8105_core_control
join_key: unicode
mode: evidence_only_no_score
allowed_outputs: ['bounded_json_report', 'bounded_csv_review_packet', 'markdown_summary']
forbidden_outputs: ['full_catalog_copy', 'gf0017_points', 'final_encoding_table', 'database']
```

## Gate Checks

- previous_standard_join_passed: `True`
- input_row_count_matches: `True`
- handoff_row_count_matches: `True`
- all_standard_sources_available: `True`
- all_rows_have_unicode_identity: `True`
- all_rows_remain_structure_pending: `True`
- all_rows_remain_decomposition_pending: `True`
- component_name_gate_pending: `True`
- no_gf0017_points_assigned: `True`
- no_final_structure_labels: `True`
- no_cnbe_rows_written: `True`
- no_database_rebuild: `True`
- no_full_catalog_copy: `True`
- no_source_asset_write: `True`

## Standard Sources

- `GF0014_2009_COMPONENT_NAMES`: exists=`True`, size=5872, sha256=`8da9fc36e1d62c5229e17ac2f00746dc84a6ecb6ea039b61f6c0f52aadadf981`
- `GB13000_COMPONENT_SPEC_1998`: exists=`True`, size=2142, sha256=`f6a53cc8b0b14c573845a1336de14df4c46d33a2cb18592e6450ef0c790002bb`
- `GF0013_2009_SINGLE_COMPONENT`: exists=`True`, size=1102, sha256=`8f0d92116f1e3513bc06230860f83416fb93e16045a49531099f0f21a55aae16`
- `GG0011_2009_RADICALS`: exists=`True`, size=798, sha256=`3eb0f09fa13884230f06a2b917587cc8f7005aa109cbf4fe4677c636b207a241`
- `GF0031_2026_STROKE_ORDER`: exists=`True`, size=616160, sha256=`5601c38ed5ec76bdc4770a281c54a0cbc6f2836d95f3b19d3853200c3ae2ae74`
- `GF3002_1999_STROKE_ORDER`: exists=`True`, size=688, sha256=`1bd050e042f246351cf4a09ef39c3ad18019cb252aa319a7a22028b852f210dd`
- `GB13000_FOLDED_STROKE`: exists=`True`, size=840, sha256=`c1cdbc03f2ee9d5c42a69ec53dac9db2eefed4e6173da720c4c59df533f67feb`
- `GF3003_1999_STROKE_ORDERING`: exists=`True`, size=808, sha256=`ce56632108e32458837bc6e9dffe62f87cc0cfb24909692bb016e38dabf79ac9`
