# CNBE 20,902 Agent Pre-Encoding Test

## Scope

This is a read-only pressure test of `cnbe-hanzi-structure-encoding-agent` on the repository's 20,902-row CNBE dataset.
It does not modify CNBE source tables, databases, generated code, releases, or package artifacts.

## Summary

- Rows scanned: 20902
- Unique chars: 20902
- Unique Unicode code points: 20902
- Duplicate chars: 0
- Duplicate code points: 0
- First strict blocker offset: None
- First strict blocker char: None None

## Agent Status Counts

| Status | Rows |
| --- | --- |
| CNBE32_REVIEW_REQUIRED | 4058 |
| EVIDENCE_GAP | 14042 |
| HUMAN_REVIEW_REQUIRED | 292 |
| SOURCE_GAP | 2510 |

## Issue Counts

| Issue | Rows |
| --- | --- |
| gf0017_cnbe32_field_repair_candidate | 6314 |
| gf0017_evidence_gap_present | 969 |
| gf0017_human_review_required | 292 |
| gf0017_source_gap_present | 7829 |
| outside_8105_gf0017_score_scope | 13073 |
| struct_type_name_mismatch_after_normalization | 12864 |
| structure_label_requires_localization | 20902 |

## Raw Structure Label Counts

| Raw structure label | Rows |
| --- | --- |
| bottom-left-wrap | 1608 |
| bottom-wrap | 1608 |
| full-wrap | 1607 |
| left-mid-right | 1608 |
| left-right | 1608 |
| left-wrap | 1608 |
| single | 1608 |
| top-left-wrap | 1608 |
| top-right-wrap | 1608 |
| top-wrap | 1608 |
| triangle | 1607 |
| up-down | 1608 |
| up-mid-down | 1608 |

## Checkpoint

```json
{
  "batch_id": "cnbe20902-agent-preencoding-test",
  "blocker_char": null,
  "blocker_offset": null,
  "blocker_unicode": null,
  "failed_gate": null,
  "last_verified_offset": 20901,
  "mode": "scan_all_with_strict_stop_simulation",
  "resume_from": 20902
}
```

## First Rows

| Offset | Char | Unicode | Status | Raw structure | Normalized structure | GF0017 | Issues |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 一 | U+4E00 | HUMAN_REVIEW_REQUIRED | single | 独体字 | 47 | gf0017_human_review_required, gf0017_source_gap_present, structure_label_requires_localization |
| 1 | 丁 | U+4E01 | EVIDENCE_GAP | left-right | 左右 | 46 | gf0017_evidence_gap_present, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 2 | 丂 | U+4E02 | EVIDENCE_GAP | left-mid-right | 左中右 | None | outside_8105_gf0017_score_scope, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 3 | 七 | U+4E03 | CNBE32_REVIEW_REQUIRED | up-down | 上下 | 45 | gf0017_cnbe32_field_repair_candidate, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 4 | 丄 | U+4E04 | EVIDENCE_GAP | up-mid-down | 上中下 | None | outside_8105_gf0017_score_scope, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 5 | 丅 | U+4E05 | EVIDENCE_GAP | top-left-wrap | 左上包 | None | outside_8105_gf0017_score_scope, structure_label_requires_localization |
| 6 | 丆 | U+4E06 | EVIDENCE_GAP | top-right-wrap | 右上包 | None | outside_8105_gf0017_score_scope, structure_label_requires_localization |
| 7 | 万 | U+4E07 | HUMAN_REVIEW_REQUIRED | bottom-left-wrap | 左下包 | 42 | gf0017_human_review_required, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 8 | 丈 | U+4E08 | CNBE32_REVIEW_REQUIRED | top-wrap | 上三包 | 45 | gf0017_cnbe32_field_repair_candidate, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 9 | 三 | U+4E09 | CNBE32_REVIEW_REQUIRED | bottom-wrap | 下三包 | 45 | gf0017_cnbe32_field_repair_candidate, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 10 | 上 | U+4E0A | CNBE32_REVIEW_REQUIRED | left-wrap | 左三包 | 45 | gf0017_cnbe32_field_repair_candidate, gf0017_source_gap_present, struct_type_name_mismatch_after_normalization, structure_label_requires_localization |
| 11 | 下 | U+4E0B | SOURCE_GAP | full-wrap | 全包围 | 45 | gf0017_cnbe32_field_repair_candidate, gf0017_source_gap_present, structure_label_requires_localization |

## First Blockers

| Offset | Char | Unicode | Status | Issues |
| --- | --- | --- | --- | --- |

## Workflow Problems Found

1. The 20,902-row repository table uses legacy English structure labels; the agent needs a formal localization layer before production repair.
2. Many rows outside the 8105 GF0017 report have no standard-side score yet, so they must be treated as `EVIDENCE_GAP` rather than encoded automatically.
3. The strict stop-on-blocker rule is useful for production batches, but a diagnostic full-scan mode is also needed to discover systemic issues in one run.
4. Current CNBE32 rows can pass raw bit-range checks while still failing professional pre-encoding gates; this confirms that bit validity is not enough.

## Next Recommendation

Add a dedicated checkpointed batch runner with two modes: `strict` for production and `diagnostic-scan` for workflow discovery. Before any repair, create a structure-label localization layer and extend GF0017 scoring beyond the 8105 scope.
