# Dictionary Context Knowledge Merge Audit

## Purpose

This audit independently verifies that the authorized dictionary-context
knowledge merge created only the separate dictionary context index and
updated references with a backup.

It also verifies that the 8,105 core knowledge files were not modified,
and that dictionary context remains cross-reference evidence only.

## Result

- Overall status: `PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED`
- Next workflow status: `KNOWLEDGE_MERGED_REVALIDATE_SOURCE_AUDIT_BEFORE_SCORING`
- Target index: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json`
- Target index entries: `49085`
- References entries: `9`
- Reference key: `reference_9`
- Base character data unchanged: `True`
- CNBE character knowledge unchanged: `True`

## Sample Characters

| Char | Exists | Unicode | Source count | Source grade | Standard level |
|---|:---:|---|---:|---|---|
| 鑫 | True | U+946B | 2 | cross_reference_dictionary_context | cross_reference_context_not_national_standard |
| 家 | True | U+5BB6 | 2 | cross_reference_dictionary_context | cross_reference_context_not_national_standard |
| 㐀 | True | U+3400 | 2 | cross_reference_dictionary_context | cross_reference_context_not_national_standard |
| 㐁 | True | U+3401 | 2 | cross_reference_dictionary_context | cross_reference_context_not_national_standard |

## Checks

- `merge_report_executed`: True
- `merge_report_authorized`: True
- `target_index_created`: True
- `target_index_entry_count`: True
- `references_updated`: True
- `references_count_is_nine`: True
- `references_backup_created`: True
- `base_character_data_hash_unchanged`: True
- `cnbe_character_knowledge_hash_unchanged`: True
- `target_index_absent_before_merge`: True
- `target_index_present_after_merge`: True
- `dictionary_context_not_scoring_authority`: True
- `score_values_assigned`: True
- `final_structure_labels_emitted`: True
- `cnbe_rows_written`: True
- `database_rebuilds`: True

## Backups

- `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/references.json.bak.20260717T031651Z`
