# CNBE 8105 Approved Structure Model Merge

- Overall status: `PASS_8105_APPROVED_STRUCTURE_MODEL_MERGE_READY`
- Total 8105 rows: 8105
- Current model intersection rows: 7829
- Missing from current model rows: 276
- Current model confirmed rows: 593
- Structure repair candidate rows: 7236
- CNBE32 rows written: 0
- Database rebuild allowed: `False`

This merge is evidence-only. It does not modify `data/cnbe32.json`,
does not encode CNBE32 values, and does not rebuild SQLite databases.

## Merge Status Counts

| Status | Rows |
| --- | --- |
| CURRENT_MODEL_STRUCTURE_CONFIRMED | 593 |
| CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE | 7236 |
| MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE | 276 |

## Known Regression Samples

| Char | Unicode | Approved structure | Approved type | Current struct name | Current type | Current localized | Merge status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 家 | U+5BB6 | 上下 | 1 | single | 0 | 独体字 | CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE |
| 侵 | U+4FB5 | 左右 | 3 | top-wrap | 8 | 上三包 | CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE |
| 偶 | U+5076 | 左右 | 3 | top-right-wrap | 6 | 右上包 | CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE |
| 冁 | U+5181 | 左右 | 3 | single | 0 | 独体字 | CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE |
| 孓 | U+5B53 | 独体字 | 0 | top-left-wrap | 5 | 左上包 | CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE |
| 㑇 | U+3447 | 左右 | 3 |  |  |  | MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE |

## Decision

Review repair and missing-row counts, then design a separate CNBE32 dry-run encoding patch for rows whose radical, stroke, structure, and index fields can be resolved without ambiguity.
