# Hanzi Decomp v0.3 Human-Approved 8105 Agent Structure Packet

- Overall status: `PASS_HUMAN_APPROVED_V03_8105_AGENT_STRUCTURE_PACKET_READY`
- Human decision: 孓为独体，其余审核通过，0.3为准
- Total rows: 8105
- Changed by human approval: 1191
- Source table rows written: 0
- CNBE32 rows written: 0
- Database rebuild allowed: `False`

This artifact is an Agent structure candidate baseline for the 8105
scope. It is not a national-standard source table, not a CNBE32 write,
and not a SQLite rebuild.

## Human Review Basis Counts

| Basis | Rows |
|---|---:|
| `HUMAN_CONFIRMED_EXISTING_CANDIDATE_WHEN_V03_TOOL_GAP` | 29 |
| `HUMAN_CONFIRMED_HANZI_DECOMP_V03` | 8075 |
| `HUMAN_CONFIRMED_JUE_U5B53_DUTIZI` | 1 |

## Checks

| Check | Result |
|---|---:|
| `all_structures_allowed` | `True` |
| `all_structures_have_agent_code` | `True` |
| `all_structures_nonblank` | `True` |
| `jue_is_independent` | `True` |
| `known_legacy_regressions_are_left_right` | `True` |
| `no_cnbe32_writes` | `True` |
| `no_database_rebuild` | `True` |
| `no_source_table_writes` | `True` |
| `row_count_is_8105` | `True` |
| `unique_character_count_is_8105` | `True` |
| `unique_unicode_count_is_8105` | `True` |

## Decision

Prepare a separate source-merge plan that maps the approved Agent structure candidates into the repository structure model. Do not modify source tables or rebuild databases without a new explicit authorization.
