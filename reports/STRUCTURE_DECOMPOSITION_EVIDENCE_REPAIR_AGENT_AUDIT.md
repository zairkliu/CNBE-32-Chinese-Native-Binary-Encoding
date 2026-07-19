# Structure/Decomposition Evidence Repair Agent Audit

## Result

- Overall status: `PASS_STRUCTURE_DECOMPOSITION_AGENT_AUDIT_READY_FOR_REVIEW_PACKET`
- Next workflow status: `STRUCTURE_DECOMPOSITION_REVIEW_PACKET_ALLOWED_NO_FULL_TABLE_DUPLICATION`
- Source report: `reports/gf0017_structure_decomposition_evidence_repair_from_index.json`
- Source SHA-256: `a3336ef410d8441e15a55d0bb7e5f5b42973d997337e3f7b6d0f74148cd315f5`
- Total rows audited: 97686
- May generate review packet: `True`
- May duplicate full 97,686 table: `False`
- May generate database: `False`

## Checks

| Check | Result |
|---|---:|
| `final_structure_labels_emitted_zero` | `True` |
| `forbidden_score_rows_zero` | `True` |
| `malformed_rows_zero` | `True` |
| `repair_report_passed` | `True` |
| `report_blocks_cnbe_writes` | `True` |
| `report_blocks_database_rebuild` | `True` |
| `report_blocks_scoring` | `True` |
| `required_statuses_present` | `True` |
| `row_count_match` | `True` |
| `scope_8105_count_match` | `True` |
| `score_values_assigned_zero` | `True` |

## Status Counts

| Status | Count |
|---|---:|
| `CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED` | 8105 |
| `STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY` | 44871 |
| `STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED` | 2029 |
| `STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY` | 2551 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT` | 12 |
| `STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT` | 40118 |
