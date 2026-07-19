# 8105 Runtime Blocker Resolution Plan

- Status: `PASS_8105_RUNTIME_BLOCKER_RESOLUTION_PLAN_READY`
- Total blocked rows: 1393
- Source-table rows written: 0
- SQLite rebuild allowed: false
- Scope: remaining force-approved 8105 rows left out of runtime promotion.

## Block Reasons

| Block reason | Rows |
| --- | --- |
| radical_resolution_blocked | 153 |
| missing_approved_radical | 964 |
| missing_current_model_row | 276 |

## Resolution Classes

| Resolution class | Rows |
| --- | --- |
| requires_radical_alias_extension_review | 9 |
| requires_shape_group_disambiguation | 4 |
| requires_component_to_radical_policy_review | 16 |
| requires_position_sensitive_radical_rule | 124 |
| requires_standard_radical_and_stroke_join | 964 |
| requires_index_allocation_and_source_row_insertion_plan | 276 |

## Recommended Policy Order

| Step | Resolution class | Rows | Gate |
| --- | --- | --- | --- |
| 1 | requires_standard_radical_and_stroke_join | 964 | join standard radical and stroke evidence; no CNBE32 writes |
| 2 | requires_position_sensitive_radical_rule | 124 | audit 阝 side rule against decomposition/source evidence |
| 3 | requires_component_to_radical_policy_review | 16 | decide whether component-like labels may map to canonical radicals |
| 4 | requires_shape_group_disambiguation | 4 | resolve 己/已/巳 and similar groups from standard sources |
| 5 | requires_radical_alias_extension_review | 9 | extend radical alias map only with explicit evidence |
| 6 | requires_index_allocation_and_source_row_insertion_plan | 276 | design insertion/index policy before adding missing 8105 rows |

## Sample Queue Rows

| Char | Unicode | Block reason | Resolution class | Source presence | Current index |
| --- | --- | --- | --- | --- | --- |
| 刁 | U+5201 | radical_resolution_blocked | requires_radical_alias_extension_review | present | 1025 |
| 巳 | U+5DF3 | radical_resolution_blocked | requires_shape_group_disambiguation | present | 2035 |
| 卫 | U+536B | radical_resolution_blocked | requires_component_to_radical_policy_review | present | 1387 |
| 也 | U+4E5F | radical_resolution_blocked | requires_component_to_radical_policy_review | present | 95 |
| 飞 | U+98DE | radical_resolution_blocked | requires_radical_alias_extension_review | present | 734 |
| 长 | U+957F | radical_resolution_blocked | requires_radical_alias_extension_review | present | 1919 |
| 巴 | U+5DF4 | radical_resolution_blocked | requires_shape_group_disambiguation | present | 2036 |
| 队 | U+961F | radical_resolution_blocked | requires_position_sensitive_radical_rule | present | 31 |
| 邓 | U+9093 | radical_resolution_blocked | requires_position_sensitive_radical_rule | present | 659 |
| 兰 | U+5170 | radical_resolution_blocked | requires_component_to_radical_policy_review | present | 880 |
| 民 | U+6C11 | radical_resolution_blocked | requires_component_to_radical_policy_review | present | 1553 |
| 邦 | U+90A6 | radical_resolution_blocked | requires_position_sensitive_radical_rule | present | 678 |

## Decision Boundary

This report is a read-only blocker-resolution plan. It does not change `data/cnbe32.json`, does not rebuild SQLite databases, and does not turn force approval into missing numeric CNBE32 fields. A later write phase still requires explicit authorization plus passing remediation evidence for radical/stroke joins, radical mapping policy, and index allocation.
