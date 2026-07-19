# Full Catalog GF0017 Preflight Plan

## Purpose

This plan maps the v4_fixed full-catalog workbook into the CNBE Agent
GF0017 preflight workflow. It is a planning and gate artifact only.

It does not score rows, rewrite the workbook, rebuild the SQLite
database, change CNBE32 values, create tags, publish releases, or upload
to PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `PREFLIGHT_PLAN_READY_SOURCE_ASSETS_REQUIRE_REVIEW`
- Source workbook: `data/CNBE_编码目录_修复版_v4_fixed.xlsx`
- Data rows: `97686`
- Columns: `17`
- GF0017 total points: `50`
- May start source evidence mapping: `True`
- May start batch GF0017 scoring: `False`
- May rebuild database: `False`

## Pre-Gates

| Gate | Status |
|---|:---:|
| `schema_status` | `PASS` |
| `sample_status` | `PASS` |
| `unicode_identity_status` | `PASS` |
| `agent_runtime_status` | `PASS` |
| `headers_match_expected` | `True` |

## Workbook Field Mapping

| Column | Agent role | GF0017 use | Authority boundary |
|---|---|---|---|
| `序号` | source_row_sequence | character_set_coverage | workbook_metadata_not_standard |
| `汉字` | literal_character | character_set_coverage | identity_candidate |
| `Unicode` | unicode_codepoint | character_set_coverage | identity_candidate |
| `CNBE(Hex)` | cnbe32_carrier_hex | not a scoring field | legacy_cnbe_candidate |
| `CNBE(Dec)` | cnbe32_carrier_decimal | not a scoring field | legacy_cnbe_candidate |
| `CNBE(Bin)` | cnbe32_carrier_binary | not a scoring field | legacy_cnbe_candidate |
| `部首区` | legacy_radical_code | radical_validity | legacy_cnbe_candidate |
| `笔画数` | legacy_stroke_count | stroke_shape, stroke_order | legacy_cnbe_candidate |
| `结构区(v4)` | legacy_structure_code | structure_first_decomposition, independent_character_rule | legacy_cnbe_candidate |
| `结构名称(v4)` | legacy_structure_name | structure_first_decomposition, independent_character_rule | legacy_cnbe_candidate |
| `字库索引` | legacy_catalog_index | character_set_coverage | workbook_metadata_not_standard |
| `扩展区` | legacy_extension_flags | not a scoring field | legacy_cnbe_candidate |
| `是否现代` | legacy_modern_flag | character_set_coverage | legacy_cnbe_candidate |
| `Space_Label` | legacy_space_label | not a scoring field | legacy_metadata_not_standard |
| `Category_Label` | legacy_category_label | not a scoring field | legacy_metadata_not_standard |
| `Time_Label` | legacy_time_label | not a scoring field | legacy_metadata_not_standard |
| `备注(v3原结构)` | legacy_v3_structure_note | structure_first_decomposition | legacy_metadata_not_standard |

## GF0017 Item Mapping

| Item | Points | Workbook fields | Preflight status |
|---|---:|---|---|
| `character_set_coverage` | 3 | `序号`, `汉字`, `Unicode`, `字库索引`, `是否现代` | SOURCE_EVIDENCE_REQUIRED |
| `stroke_shape` | 3 | `笔画数` | SOURCE_EVIDENCE_REQUIRED |
| `stroke_order` | 3 | `笔画数` | SOURCE_EVIDENCE_REQUIRED |
| `component_validity` | 3 | none | SOURCE_EVIDENCE_REQUIRED |
| `component_name_validity` | 8 | none | SOURCE_EVIDENCE_REQUIRED |
| `radical_validity` | 3 | `部首区` | SOURCE_EVIDENCE_REQUIRED |
| `independent_character_rule` | 7 | `结构区(v4)`, `结构名称(v4)` | SOURCE_EVIDENCE_REQUIRED |
| `structure_first_decomposition` | 20 | `结构区(v4)`, `结构名称(v4)`, `备注(v3原结构)` | SOURCE_EVIDENCE_REQUIRED |

## Known Blockers

- None.

## Stop And Resume

- Batch id: `full-catalog-v4-fixed-gf0017-preflight`
- Start offset: `0`
- End offset: `97685`
- Checkpoint file: `reports/full_catalog_gf0017_preflight_checkpoint.json`
- Resume rule: restart from last_verified_offset + 1 after blocker evidence is resolved

Stop conditions:

- Unicode identity mismatch
- source grade unresolved for a required scoring item
- legacy structure label without Agent localization
- Agent standard mapping mislabeled as national standard
- database rewrite attempted before explicit authorization

## Next Artifacts

- `reports/full_catalog_gf0017_source_mapping.json`
- `reports/FULL_CATALOG_GF0017_SOURCE_MAPPING.md`
- `scripts/map_full_catalog_gf0017_sources.py`

## Decision

The workbook can enter source-evidence mapping, but final GF0017 scoring is blocked until required source grades and review-required asset notes are resolved or accepted.

The next allowed implementation step is source-evidence mapping.
Batch GF0017 scoring remains blocked.
