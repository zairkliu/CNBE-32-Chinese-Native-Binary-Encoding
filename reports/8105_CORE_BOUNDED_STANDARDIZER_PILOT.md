# 8105 Core Bounded Standardizer Pilot

## Result

- Overall status: `PASS_8105_BOUNDED_STANDARDIZER_PILOT_REVIEW_PACKET_READY`
- Next workflow status: `READY_FOR_HUMAN_REVIEW_OF_8105_BOUNDED_STANDARDIZER_PACKET`
- Review rows: 100
- Rows with component candidates: 88
- Rows with dictionary context: 57
- Rows with standard structure candidates: 88
- Rows with standard decomposition candidates: 88
- New GF0017 points assigned: 0
- CNBE rows written: 0
- Database rebuild allowed: `False`

This is a bounded 100-row candidate review packet. It fully discards
legacy CNBE structure fields and uses only national-standard, core
reference, and network/dictionary cross-reference evidence. Candidate
structure values are review-only; the script does not write CNBE32
values or rebuild the SQLite database.

## Candidate Status Counts

| Status | Count |
|---|---:|
| `CANDIDATE_COMPONENTS_REVIEW_REQUIRED` | 32 |
| `CANDIDATE_COMPONENTS_WITH_DICTIONARY_CONTEXT_REVIEW_REQUIRED` | 56 |
| `DICTIONARY_CONTEXT_ONLY_REVIEW_REQUIRED` | 1 |
| `STANDARDIZER_EVIDENCE_GAP` | 11 |

## Outputs

- JSON report: `reports/8105_core_bounded_standardizer_pilot.json`
- Markdown report: `reports/8105_CORE_BOUNDED_STANDARDIZER_PILOT.md`
- Review packet CSV: `review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.csv`
- Optional review packet XLSX: `review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.xlsx`
- Copied work table CSV: `outputs/8105_core_bounded_standardizer_work_table.csv`

## Decision

The packet contains candidate decomposition/component evidence only. Legacy CNBE structure fields are not read. Human review and standards-source adjudication are required before GF0017 points or CNBE32 values can be promoted.
