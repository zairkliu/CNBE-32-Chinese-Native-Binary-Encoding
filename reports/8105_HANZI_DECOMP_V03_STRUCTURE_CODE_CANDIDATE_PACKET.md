# Hanzi Decomp v0.3 Structure-Code Candidate Packet

- Overall status: `PASS_HANZI_DECOMP_V03_STRUCTURE_CODE_PACKET_READY`
- Total rows: 8105
- Applied v0.3 gap fills: 1243
- Remaining blank structure rows: 1
- v0.3 conflict rows excluded: 357
- Structure-code candidate rows: 8104
- CNBE32 rows written: 0

This packet contains structure-code candidates only. It does not write
CNBE32 rows and does not rebuild a database.

## Materialize Status Counts

| Status | Rows |
|---|---:|
| `APPLIED_GAP_FILL_REVIEW_REQUIRED` | 1243 |
| `UNCHANGED` | 6862 |

## Decision

Human-review the 1,243 applied v0.3 gap fills and the 357 conflicts before authorizing any source merge.
