# CNBE-32 8105 Encoding Comparison Report

## Scope

This is a read-only first-pass comparison between the 8105 standard Hanzi baseline and the current CNBE table.
It does not rewrite `cnbe32_updated.json`, does not generate new CNBE codes, and does not cover non-8105 characters.

## Gate

- Baseline expected rows: 8105
- Baseline actual rows: 8105
- Baseline row count matches expected: True
- Current rows in 8105 scope: 7829
- Missing current rows: 276
- Invalid current structure rows: 290

## Status Counts

| Status | Rows |
| --- | --- |
| EVIDENCE_GAP | 1244 |
| FAIL_FIXABLE | 6314 |
| FAIL_REVIEW_REQUIRED | 547 |

## Issue Counts

| Issue | Rows |
| --- | --- |
| ambiguous_decomposition | 293 |
| invalid_current_structure | 290 |
| missing_decomposition | 964 |
| missing_from_current_cnbe | 276 |
| missing_standard_radical | 1239 |
| missing_standard_structure | 1244 |
| radical_mismatch | 7813 |
| stroke_count_mismatch | 7579 |
| structure_mismatch | 5864 |

## Field Mismatch Counts

| Field | Rows |
| --- | --- |
| radical | 7813 |
| stroke_count | 7579 |
| structure | 5864 |

## Required Review Samples

| Char | Status | Issues | Std Radical | CNBE Radical | Std Strokes | CNBE Strokes | Std Structure | CNBE Structure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 家 | FAIL_FIXABLE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 宀 | 爪 | 10 | 8 | 上下 | 左右 |
| 遛 | FAIL_FIXABLE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 辶 | 毛 | 13 | 31 | 左下包 | 上下 |
| 涡 | FAIL_FIXABLE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 氵 | 音 | 10 | 7 | 左右 | 全包围 |
| 与 | FAIL_REVIEW_REQUIRED | ambiguous_decomposition, radical_mismatch, stroke_count_mismatch, structure_mismatch | 一 | 冫 | 3 | 15 | 右上包 | 独体字 |
| 焱 | FAIL_FIXABLE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 火 | 匚 | 12 | 20 | 上下 | 独体字 |
| 衍 | FAIL_FIXABLE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 行 | 辛 | 9 | 15 | 镶嵌 | 上下 |
| 鼻 | FAIL_REVIEW_REQUIRED | invalid_current_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch | 鼻 | 女 | 14 | 26 | 上下 | 右下包 |

## Policy Notes

- Allowed structures are: 上三包, 上下, 上中下, 下三包, 全包围, 右上包, 左三包, 左上包, 左下包, 左中右, 左右, 镶嵌; plus special `独体字`.
- Source labels such as `右下包` are not accepted as final normalized structure values.
- Decompositions containing `?` are review-required and must not be auto-fixed.
- Characters outside the 8105 baseline are out of scope for this first pass.

## Next Gate

The next phase may design an auto-fix candidate list only from `FAIL_FIXABLE` rows.
`FAIL_REVIEW_REQUIRED` and `EVIDENCE_GAP` rows must stay in manual review pools.
