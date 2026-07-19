# 8105 No-Legacy Standardizer Packet Audit

- Overall status: `PASS_8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT`
- Next workflow status: `READY_FOR_HUMAN_RECHECK_PACKET_REVIEW`
- Packet rows: 100
- Human recheck rows: 21
- Forbidden legacy fields: 0
- Forbidden pollution hits: 0
- Candidate/standard mismatches: 0
- Regression failures: 0

## Structure Counts

| Structure | Count |
|---|---:|
| `UNRESOLVED` | 12 |
| `上三包` | 2 |
| `上下` | 23 |
| `全包围` | 1 |
| `右上包` | 3 |
| `左上包` | 2 |
| `左下包` | 2 |
| `左右` | 55 |

## Decision

The packet is clean enough for human recheck only. GF0017 structure scoring and CNBE writes remain blocked until human review confirms the corrected structure candidates.

## Outputs

- Human recheck CSV: `review_packets/300_character_8105_pilot/8105_no_legacy_human_recheck_packet.csv`
- JSON report: `reports/8105_no_legacy_standardizer_packet_audit.json`
