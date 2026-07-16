# CNBE8105 GF0017 Normativity Score Report

## Scope

This report scores each 8105 character against the GF0017 50-point normativity model.
It is read-only and does not modify CNBE source data, databases, or generated code.

Important: `character_set_coverage` and `stroke_shape` retain `SOURCE_GAP` labels because standalone local sources for GB2312, 现代汉语通用字表, and 印刷通用汉字字形表 have not yet been confirmed.

## Summary

- Rows scored: 8105
- Average score: 44.4524 / 50
- Minimum score: 33 / 50
- Maximum score: 49 / 50

## Overall Status Counts

| Status | Rows |
| --- | --- |
| EVIDENCE_GAP | 1244 |
| PARTIAL | 6569 |
| REVIEW_REQUIRED | 292 |

## Repair Class Counts

| Repair class | Rows |
| --- | --- |
| ADD_OR_EXCLUDE_CHARACTER | 276 |
| CNBE32_FIELD_REPAIR_CANDIDATE | 6314 |
| COMPLETE_STANDARD_EVIDENCE_FIRST | 969 |
| HUMAN_REVIEW_REQUIRED | 292 |
| MIXED_REPAIR_REVIEW | 254 |

## Score Item Averages

| Item | Average score | Item statuses |
| --- | --- | --- |
| character_set_coverage | 2.9659 | SOURCE_GAP:8105 |
| stroke_shape | 2.0649 | SOURCE_GAP:8105 |
| stroke_order | 2.0649 | PARTIAL:7579, PASS:526 |
| component_validity | 2.8449 | EVIDENCE_GAP:1239, PASS:6573, REVIEW_REQUIRED:293 |
| component_name_validity | 6.7409 | EVIDENCE_GAP:1239, PASS:6573, REVIEW_REQUIRED:293 |
| radical_validity | 1.8832 | EVIDENCE_GAP:1239, PARTIAL:6849, PASS:17 |
| independent_character_rule | 6.9556 | EVIDENCE_GAP:1244, PARTIAL:321, PASS:6540 |
| structure_first_decomposition | 18.9321 | EVIDENCE_GAP:1244, PARTIAL:4674, PASS:1895, REVIEW_REQUIRED:292 |

## Known Character Samples

| Char | Unicode | Score | Status | Repair class | Issues | Std radical | CNBE radical | Std strokes | CNBE strokes | Std structure | CNBE structure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 一 | U+4E00 | 47 | REVIEW_REQUIRED | HUMAN_REVIEW_REQUIRED | ambiguous_decomposition | 一 | 一 | 1 | 1 | 独体字 | 独体字 |
| 家 | U+5BB6 | 46 | PARTIAL | CNBE32_FIELD_REPAIR_CANDIDATE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 宀 | 爪 | 10 | 8 | 上下 | 左右 |
| 遛 | U+905B | 46 | PARTIAL | CNBE32_FIELD_REPAIR_CANDIDATE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 辶 | 毛 | 13 | 31 | 左下包 | 上下 |
| 涡 | U+6DA1 | 46 | PARTIAL | CNBE32_FIELD_REPAIR_CANDIDATE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 氵 | 音 | 10 | 7 | 左右 | 全包围 |
| 焱 | U+7131 | 45 | PARTIAL | CNBE32_FIELD_REPAIR_CANDIDATE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 火 | 匚 | 12 | 20 | 上下 | 独体字 |
| 与 | U+4E0E | 42 | REVIEW_REQUIRED | HUMAN_REVIEW_REQUIRED | ambiguous_decomposition, radical_mismatch, stroke_count_mismatch, structure_mismatch | 一 | 冫 | 3 | 15 | 右上包 | 独体字 |
| 衍 | U+884D | 46 | PARTIAL | CNBE32_FIELD_REPAIR_CANDIDATE | radical_mismatch, stroke_count_mismatch, structure_mismatch | 行 | 辛 | 9 | 15 | 镶嵌 | 上下 |
| 鼻 | U+9F3B | 45 | PARTIAL | MIXED_REPAIR_REVIEW | invalid_current_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch | 鼻 | 女 | 14 | 26 | 上下 | 右下包 |

## Lowest Score Samples

| Char | Unicode | Rank | Score | Status | Repair class | Issues |
| --- | --- | --- | --- | --- | --- | --- |
| 浕 | U+6D55 | 4347 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 堉 | U+5809 | 4736 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 馃 | U+9983 | 4932 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 睄 | U+7744 | 5123 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 媭 | U+5AAD | 5218 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 璠 | U+74A0 | 6032 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 璘 | U+7498 | 6033 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 朸 | U+6738 | 6528 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 岠 | U+5CA0 | 6595 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 纮 | U+7EAE | 6638 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 昒 | U+6612 | 6676 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 咍 | U+548D | 6680 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |
| 侁 | U+4F81 | 6695 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 攽 | U+653D | 6708 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | invalid_current_structure, missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch |
| 姈 | U+59C8 | 6743 | 33 | EVIDENCE_GAP | COMPLETE_STANDARD_EVIDENCE_FIRST | missing_decomposition, missing_standard_radical, missing_standard_structure, radical_mismatch, stroke_count_mismatch, structure_mismatch |

## Next Gate

Use `CNBE32_FIELD_REPAIR_CANDIDATE` rows for a dry-run repair plan only after the radical-code map is validated.
`EVIDENCE_GAP`, `SOURCE_GAP`, and `HUMAN_REVIEW_REQUIRED` rows must not be auto-rewritten.
