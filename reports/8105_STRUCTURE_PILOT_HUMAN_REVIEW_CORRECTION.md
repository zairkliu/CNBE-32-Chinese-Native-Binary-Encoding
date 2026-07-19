# 8105 Structure Pilot Human Review Correction

## Result

Human review found a blocking structure-quality problem in the first bounded
pilot review packet.

The main failure was legacy structure pollution: old CNBE generated structure
fields were visible in the packet and could be mistaken for usable evidence.
Examples:

| Character | Legacy wrong structure | Correct standard candidate |
|---|---|---|
| `侵` | `右下包` | `左右` |
| `偶` | `右上包` | `左右` |
| `冁` | `独体字` | `左右` |

This is a blocking issue. The old packet must not be used for scoring,
encoding, or source-table repair.

## Corrected Rule

Legacy CNBE structure fields are now fully discarded for structure generation.
They may be used only in separated error-localization audits.

All future structure work must use the three-tier logic:

1. `national_standard`
2. `core_reference`
3. `network_cross_reference`

Network, dictionary, and encyclopedia references are review context only. They
do not promote a national-standard structure label by themselves.

## Corrected Pilot Output

The corrected 100-row packet was regenerated with:

- no `legacy_cnbe32` field;
- no `legacy_structure_label` field;
- no old generated CNBE structure input;
- review-only standard candidates from the 8105 comparison evidence;
- unchanged no-write and no-database policy.

Regression checks now assert:

- `侵` -> `左右`, `⿰亻⿳彐冖又`
- `偶` -> `左右`, `⿰亻禺`
- `冁` -> `左右`, `⿰单展`

## Outputs

- Corrected CSV packet:
  `review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.csv`
- Corrected XLSX packet:
  `review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.xlsx`
- Corrected pilot report:
  `reports/8105_CORE_BOUNDED_STANDARDIZER_PILOT.md`

## Decision

The previous pilot packet is superseded. Continue only with the corrected
no-legacy-structure packet.
