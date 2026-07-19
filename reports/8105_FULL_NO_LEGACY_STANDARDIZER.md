# 8105 Full No-Legacy Standardizer

- Overall status: `PASS_8105_FULL_NO_LEGACY_STANDARDIZER_READY`
- Review rows: 8105
- Complete candidate rows: 6568
- Partial candidate rows: 298
- Evidence gap rows: 1239
- ZDIC/source gap queue rows: 1537
- CNBE rows written: 0
- Database rebuild allowed: `False`

Legacy CNBE structure fields are not read or emitted. Gaps are routed to
the ZDIC/source review queue rather than filled by model memory.

## Structure Counts

| Structure | Count |
|---|---:|
| `UNRESOLVED` | 1244 |
| `上三包` | 79 |
| `上下` | 1626 |
| `上中下` | 47 |
| `下三包` | 7 |
| `全包围` | 35 |
| `右上包` | 52 |
| `左三包` | 15 |
| `左上包` | 281 |
| `左下包` | 162 |
| `左中右` | 18 |
| `左右` | 4358 |
| `独体字` | 29 |
| `镶嵌` | 152 |

## Outputs

- standardizer_csv: `review_packets/8105_full/8105_full_no_legacy_standardizer.csv`
- zdic_gap_queue_csv: `review_packets/8105_full/8105_full_zdic_gap_queue.csv`
- json_report: `reports/8105_full_no_legacy_standardizer.json`
- markdown_report: `reports/8105_FULL_NO_LEGACY_STANDARDIZER.md`

## Decision

All 8105 rows were materialized without legacy structure input. Complete standard-side candidates may enter structure-item scoring; gaps route to ZDIC/source review queues.
