# CNBE 8105 Approved CNBE32 Dry-Run Patch

- Overall status: `PASS_8105_APPROVED_CNBE32_DRY_RUN_READY`
- Total rows: 8105
- Dry-run ready rows: 6712
- Dry-run blocked rows: 1393
- Source table rows written: 0
- CNBE32 source rows written: 0
- Database rebuild allowed: `False`

This artifact previews CNBE32 field values only. It preserves the
current model index and extension bits, uses the approved 8105 Agent
structure baseline, and blocks missing or ambiguous rows.

## Block Reasons

| Reason | Rows |
| --- | --- |
| missing_approved_radical | 964 |
| missing_current_model_row | 276 |
| radical_resolution_blocked | 153 |

## Changed Field Counts

| Field | Rows |
| --- | --- |
| cnbe | 6711 |
| radix | 6682 |
| radix_name | 6696 |
| strokes | 6500 |
| struct_name | 6712 |
| struct_type | 6189 |

## Known Samples

| Char | Unicode | Status | Block reason | Approved structure | Approved type | Current CNBE | Proposed CNBE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 家 | U+5BB6 | DRY_RUN_READY |  | 上下 | 1 | 0x57405B60 | 0x2850DB60 |
| 侵 | U+4FB5 | DRY_RUN_READY |  | 左右 | 3 | 0x0A241B50 | 0x09499B50 |
| 偶 | U+5076 | DRY_RUN_READY |  | 左右 | 3 | 0xCB5B2760 | 0x0959A760 |
| 冁 | U+5181 | DRY_RUN_BLOCKED | radical_resolution_blocked | 左右 | 3 | 720386064 |  |
| 孓 | U+5B53 | DRY_RUN_READY |  | 独体字 | 0 | 0xCA12D530 | 0x27185530 |
| 㑇 | U+3447 | DRY_RUN_BLOCKED | missing_current_model_row | 左右 | 3 |  |  |

## Decision

Review dry-run ready and blocked rows. A future write phase must copy the source table first, resolve blocked radicals and missing current-model indices, then regenerate dependent artifacts in a separate authorization step.
