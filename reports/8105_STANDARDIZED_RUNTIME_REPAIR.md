# 8105 Standardized Runtime Repair

- Overall status: `PASS_8105_STANDARDIZED_RUNTIME_REPAIR`
- Runtime rows: 20902
- Applied repair rows: 598
- Patched 8105 rows after repair: 7310
- Remaining force-approved not-patched rows: 795
- Databases rebuilt: 2

This release-track repair keeps 8105 as the core baseline and
treats ZDIC/cache data only as cross-reference context. It does not
insert characters missing from the current runtime model and does
not authorize tag, release, or PyPI publication.

## Applied Radical Sources

| Source | Rows |
| --- | --- |
| approved_8105_packet | 123 |
| zdic_cached_cross_reference_radical | 475 |

## Applied Radical Resolution

| Resolution | Rows |
| --- | --- |
| ALIAS | 166 |
| DIRECT | 299 |
| POSITION_LEFT_ALIAS | 61 |
| POSITION_RIGHT_ALIAS | 72 |

## Remaining Blockers

| Reason | Rows |
| --- | --- |
| invalid_or_missing_stroke_count | 1 |
| missing_current_model_row | 276 |
| missing_radical_after_cross_reference_join | 486 |
| radical_resolution_blocked | 32 |

## Known Samples

| Char | Unicode | CNBE | Radical | Strokes | Structure | Type |
| --- | --- | --- | --- | --- | --- | --- |
| 队 | U+961F | 0xAA2181F0 | 阜 | 4 | 左右 | 3 |
| 玕 | U+7395 | 0x5F39D950 | 王 | 7 | 左右 | 3 |
| 刁 | U+5201 | 0xAA1DC010 | 阜 | 3 | full-wrap | 11 |
| 冁 | U+5181 | 0x2AF03810 | 小 | 30 | single | 0 |
| 㑇 |  | missing |  |  |  |  |
| 家 | U+5BB6 | 0x2850DB60 | 宀 | 10 | 上下 | 1 |
| 侵 | U+4FB5 | 0x09499B50 | 亻 | 9 | 左右 | 3 |
| 偶 | U+5076 | 0x0959A760 | 亻 | 11 | 左右 | 3 |
| 孓 | U+5B53 | 0x27185530 | 子 | 3 | 独体字 | 0 |
