# 300 Character 8105 Pilot Plan

## Result

- Overall status: `PASS_300_CHARACTER_8105_PILOT_PLAN_READY`
- Next workflow status: `READY_FOR_300_CHARACTER_PILOT_EVIDENCE_JOIN_NO_SCORING`
- Source rows referenced: 97686
- Pilot rows: 300
- GF0017 points assigned: 0
- Final structure labels emitted: 0
- CNBE rows written: 0
- Database rebuild allowed: `False`
- XLSX generated: `False`

## Strata

| Stratum | Rows | Selection |
|---|---:|---|
| `8105_core_control` | 100 | catalog_scope == 8105_core |
| `outside_8105_strong_dictionary_context` | 100 | outside_8105 with dictionary, Cihai, or origin context |
| `outside_8105_extension_or_gap` | 100 | outside_8105 supplementary-plane rows with source-gap or Agent queue status |

## Counts

- Catalog scopes: `{'8105_core': 100, 'outside_8105_agent_candidate': 200}`
- Structure statuses: `{'CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED': 100, 'STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY': 98, 'STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED': 4, 'STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY': 9, 'STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT': 89}`
- Source grades: `{'agent_standard_candidate_not_national_standard': 98, 'cross_reference': 13, 'cross_reference_context': 89, 'standard_derived_join_pending': 100}`

## Sample Rows

| Pilot ID | Unicode | Char | Scope | Structure Status | Evidence Role |
|---|---|---|---|---|---|
| `8105_core_control_001` | `U+3447` | 㑇 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_002` | `U+4E09` | 三 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_003` | `U+4EA1` | 亡 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_004` | `U+4F25` | 伥 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_005` | `U+4FB5` | 侵 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_006` | `U+5076` | 偶 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_007` | `U+5181` | 冁 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_008` | `U+522B` | 别 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_009` | `U+52FE` | 勾 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_010` | `U+53A5` | 厥 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_011` | `U+542B` | 含 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_012` | `U+54B3` | 咳 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_013` | `U+5555` | 啕 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_014` | `U+5600` | 嘀 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_015` | `U+5704` | 圄 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_016` | `U+579F` | 垟 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_017` | `U+5851` | 塑 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |
| `8105_core_control_018` | `U+5951` | 契 | `8105_core` | `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | `national_standard_core_control` |

## Decision

The bounded 300-character pilot is ready for read-only evidence join testing. It is not an encoding result and cannot be used as a source table until a later human review and merge-audit gate.
