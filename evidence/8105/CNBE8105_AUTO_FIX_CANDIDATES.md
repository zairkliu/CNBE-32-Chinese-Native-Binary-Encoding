# CNBE-32 8105 Auto-Fix Candidates

## Scope

This report designs a read-only auto-fix candidate pool from the 8105 comparison output.
It does not rewrite `cnbe32_updated.json`, does not recalculate 32-bit CNBE values, and does not assign numeric radical codes.

## Gate

- Comparison rows: 8105
- Candidate rows: 6314
- Excluded rows: 1791
- Apply gate: NO_APPLY_IN_THIS_PHASE

## Candidate Issue Counts

| Issue | Rows |
| --- | --- |
| radical_mismatch | 6301 |
| stroke_count_mismatch | 6123 |
| structure_mismatch | 4420 |

## Candidate Structure Counts

| Structure | Rows |
| --- | --- |
| 上三包 | 72 |
| 上下 | 1465 |
| 上中下 | 36 |
| 下三包 | 5 |
| 全包围 | 32 |
| 右上包 | 40 |
| 左三包 | 13 |
| 左上包 | 251 |
| 左下包 | 156 |
| 左中右 | 18 |
| 左右 | 4115 |
| 镶嵌 | 111 |

## Exclusion Counts

| Reason | Rows |
| --- | --- |
| status_EVIDENCE_GAP | 1244 |
| status_FAIL_REVIEW_REQUIRED | 547 |

## Known Candidate Samples

| Char | Unicode | Current Radical | Proposed Radical | Current Strokes | Proposed Strokes | Current Structure | Proposed Structure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 家 | U+5BB6 | 爪 | 宀 | 8 | 10 | 左右 | 上下 |
| 遛 | U+905B | 毛 | 辶 | 31 | 13 | 上下 | 左下包 |
| 涡 | U+6DA1 | 音 | 氵 | 7 | 10 | 全包围 | 左右 |
| 焱 | U+7131 | 匚 | 火 | 20 | 12 | 独体字 | 上下 |
| 衍 | U+884D | 辛 | 行 | 15 | 9 | 上下 | 镶嵌 |

## Blocked Fields

- `cnbe`: not recalculated in this phase.
- `radix`: numeric radical codes require a separately validated radical-code mapping table.

## Next Gate

Before any write patch is allowed, build and validate a radical-code mapping table, then design a dry-run patch against a copy of the CNBE dataset.
