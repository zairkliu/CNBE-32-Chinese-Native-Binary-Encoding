# Full Catalog GF0017 Source Mapping

## Purpose

This report binds each GF0017 50-point normativity item to source-evidence
assets before any full-catalog row scoring begins.

It is read-only. It does not score rows, modify the workbook, rebuild
databases, alter CNBE32 values, create tags, publish releases, or upload
to PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `SOURCE_MAPPING_READY_KNOWLEDGE_BLOCKERS_REMAIN`
- GF0017 items: `8`
- GF0017 total points: `50`
- Direct-standard-backed items: `8`
- Knowledge blockers: `1`
- May start schema join design: `True`
- May start batch GF0017 scoring: `False`

## Authority Boundary

- National standards and directly derived standard extracts can control formal evidence.
- Agent-standard mappings are project outputs, not national-standard claims.
- OCR, dictionary, Wikipedia, and third-party decomposition assets remain review aids.
- Legacy CNBE fields are candidate carrier data, not proof of correctness.

## Source Status Counts

- `SOURCE_EVIDENCE_REQUIRED`: 6
- `SOURCE_GAP`: 2

## GF0017 Source Map

| Item | Points | Source status | Workbook fields | Controlling sources |
|---|---:|---|---|---|
| `character_set_coverage` | 3 | SOURCE_GAP | `序号`, `汉字`, `Unicode`, `字库索引`, `是否现代` | GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则 (direct_standard); 通用规范汉字表 8105 (cross_reference) |
| `stroke_shape` | 3 | SOURCE_GAP | `笔画数` | GF 0017-2013 识字教学用通用键盘汉字字形输入系统评测规则 (direct_standard); GB 13000.1 字符集汉字折笔规范 (cross_reference) |
| `stroke_order` | 3 | SOURCE_EVIDENCE_REQUIRED | `笔画数` | GF 0031-2026 通用规范汉字笔顺规范 (direct_standard); GF3002-1999 GB13000.1字符集汉字笔顺规范 (direct_standard) |
| `component_validity` | 3 | SOURCE_EVIDENCE_REQUIRED | none | GF 0014-2009 现代常用字部件及部件名称规范 (direct_standard); 信息处理用GB 13000.1 字符集汉字部件规范 (direct_standard) |
| `component_name_validity` | 8 | SOURCE_EVIDENCE_REQUIRED | none | GF 0014-2009 现代常用字部件及部件名称规范 (direct_standard) |
| `radical_validity` | 3 | SOURCE_EVIDENCE_REQUIRED | `部首区` | GG 0011-2009 汉字部首表 (direct_standard) |
| `independent_character_rule` | 7 | SOURCE_EVIDENCE_REQUIRED | `结构区(v4)`, `结构名称(v4)` | GF 0013-2009 现代常用独体字规范 (direct_standard); GF 0014-2009 现代常用字部件及部件名称规范 (direct_standard) |
| `structure_first_decomposition` | 20 | SOURCE_EVIDENCE_REQUIRED | `结构区(v4)`, `结构名称(v4)`, `备注(v3原结构)` | GF 0014-2009 现代常用字部件及部件名称规范 (direct_standard); 信息处理用GB 13000.1 字符集汉字部件规范 (direct_standard) |

## Known Blockers

- `Unihan.zip`: zip archive failed Python zipfile integrity check -> exclude or replace before treating as authoritative input

## Decision

The GF0017 source map is now explicit. The next allowed step is schema join design and blocker reconciliation; row scoring remains blocked.

Batch GF0017 scoring remains blocked until the join schema and source
blockers are resolved.

## Next Artifacts

- `reports/full_catalog_gf0017_join_schema.json`
- `reports/FULL_CATALOG_GF0017_JOIN_SCHEMA.md`
- `scripts/design_full_catalog_gf0017_join_schema.py`
