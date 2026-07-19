# 300 Character Pilot Evidence Join

## Result

- Overall status: `PASS_300_CHARACTER_PILOT_EVIDENCE_JOIN_READY_FOR_REVIEW`
- Next workflow status: `PILOT_EVIDENCE_JOIN_READY_FOR_HUMAN_REVIEW_NO_SCORING`
- Pilot rows: 300
- Dictionary context rows: 190
- Yuanliu context rows: 97
- Cihai context rows: 59
- Wiki context rows: 18
- ZDIC URL rows: 300
- ZDIC snapshot rows: 3
- GF0017 points assigned: 0
- Final structure labels emitted: 0
- CNBE rows written: 0
- Database rebuild allowed: `False`
- XLSX generated: `False`

## Join Status Counts

- Strata: `{'8105_core_control': 100, 'outside_8105_extension_or_gap': 100, 'outside_8105_strong_dictionary_context': 100}`
- Authority layers: `{'agent_standard_candidate_not_national_standard': 98, 'national_standard_core_pending_item_join': 100, 'standard_aligned_or_cross_reference_review_context': 102}`
- GF0017 join statuses: `{'AGENT_STANDARD_QUEUE_NOT_SCORABLE': 98, 'PENDING_STANDARD_DERIVED_ITEM_JOIN': 100, 'REVIEW_CONTEXT_AVAILABLE_NOT_SCORABLE': 102}`
- Structure statuses: `{'CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED': 100, 'STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY': 98, 'STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED': 4, 'STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY': 9, 'STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT': 89}`

## Sample Joined Rows

| Pilot ID | Unicode | Char | Authority Layer | GF0017 Join Status | Next Action |
|---|---|---|---|---|---|
| `8105_core_control_001` | `U+3447` | 㑇 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_002` | `U+4E09` | 三 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_003` | `U+4EA1` | 亡 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_004` | `U+4F25` | 伥 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_005` | `U+4FB5` | 侵 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_006` | `U+5076` | 偶 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_007` | `U+5181` | 冁 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_008` | `U+522B` | 别 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_009` | `U+52FE` | 勾 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_010` | `U+53A5` | 厥 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_011` | `U+542B` | 含 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_012` | `U+54B3` | 咳 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_013` | `U+5555` | 啕 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_014` | `U+5600` | 嘀 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_015` | `U+5704` | 圄 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_016` | `U+579F` | 垟 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_017` | `U+5851` | 塑 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |
| `8105_core_control_018` | `U+5951` | 契 | `national_standard_core_pending_item_join` | `PENDING_STANDARD_DERIVED_ITEM_JOIN` | `join_8105_standard_sources_before_scoring` |

## Decision

The 300-row pilot evidence join is ready for human review. It shows which evidence layers are present and which standard joins remain blocked, but it is not a scoring result or encoding table.
