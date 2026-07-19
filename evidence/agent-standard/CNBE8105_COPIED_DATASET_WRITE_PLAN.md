# CNBE 8105 Copied Dataset Write Plan

- Overall status: `PASS_8105_CNBE32_COPIED_DATASET_WRITE_PLAN_READY`
- Source rows: 20902
- Copy rows: 20902
- Patched rows in copy: 6712
- Force-approved not patched rows: 1393
- Source table rows written: 0
- Database rebuild allowed: `False`

The copied dataset is an evidence artifact. It is not the production
`data/cnbe32.json` source table and does not trigger SQLite rebuilds.

## Outputs

- Copied dataset: `evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy.json`
- Patch CSV: `evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy_patch.csv`
- Blocked CSV: `evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy_blocked_queue.csv`

## Changed Field Counts

| Field | Rows |
| --- | --- |
| cnbe | 6711 |
| radix | 6682 |
| radix_name | 6696 |
| strokes | 6500 |
| struct_name | 6712 |
| struct_type | 6189 |

## Blocked Reason Counts

| Reason | Rows |
| --- | --- |
| missing_approved_radical | 964 |
| missing_current_model_row | 276 |
| radical_resolution_blocked | 153 |

## Known Samples

| Char | Unicode | Status | Current/Reason | Proposed CNBE | Structure |
| --- | --- | --- | --- | --- | --- |
| 家 | U+5BB6 | PATCHED_IN_COPY | 0x57405B60 | 0x2850DB60 | 上下 |
| 侵 | U+4FB5 | PATCHED_IN_COPY | 0x0A241B50 | 0x09499B50 | 左右 |
| 偶 | U+5076 | PATCHED_IN_COPY | 0xCB5B2760 | 0x0959A760 | 左右 |
| 孓 | U+5B53 | PATCHED_IN_COPY | 0xCA12D530 | 0x27185530 | 独体字 |
| 冁 | U+5181 | FORCE_APPROVED_BUT_NOT_COPIED_DATASET_PATCHED | radical_resolution_blocked |  | 左右 |
| 㑇 | U+3447 | FORCE_APPROVED_BUT_NOT_COPIED_DATASET_PATCHED | missing_current_model_row |  | 左右 |

## Decision

Review the copied dataset and blocked queue. A later source-table write requires explicit authorization plus a strategy for 964 missing radicals, 276 missing current-model rows, and 153 non-conservative radical mappings.
