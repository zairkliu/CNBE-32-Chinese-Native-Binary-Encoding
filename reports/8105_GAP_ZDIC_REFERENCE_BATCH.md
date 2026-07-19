# 8105 Gap ZDIC Reference Batch

- Overall status: `PASS_8105_GAP_ZDIC_REFERENCE_BATCH_READY`
- Requested rows: 50
- Parsed with normalized structure: 22
- Records with any fields: 22
- Failed or missing records: 28
- CNBE rows written: 0
- Database rebuild allowed: `False`

ZDIC remains `network_cross_reference` only. It may reduce manual lookup
work, but it cannot assign national-standard structure, GF0017 points,
or CNBE rows without later standard-aware review.

## Status Counts

| Status | Rows |
|---|---:|
| `NETWORK_OR_PARSE_GAP` | 28 |
| `PARSED_WITH_STRUCTURE` | 22 |

## Outputs

- json_report: `reports/8105_gap_zdic_reference_batch.json`
- csv: `review_packets/8105_full/8105_gap_zdic_reference_batch.csv`
- markdown_report: `reports/8105_GAP_ZDIC_REFERENCE_BATCH.md`
- cache_dir: `reports/zdic_8105_gap_cache`
