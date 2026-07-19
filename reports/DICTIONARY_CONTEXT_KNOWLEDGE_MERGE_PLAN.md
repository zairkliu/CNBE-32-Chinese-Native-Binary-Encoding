# Dictionary Context Knowledge Merge Plan

## Purpose

This plan defines how staged Kangxi and Zhonghua Dazidian context should
be merged into `cnbe-research/knowledge` after explicit authorization.

It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit
final structure labels, write CNBE rows, or rebuild CNBE databases.

## Result

- Overall status: `PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_ALREADY_EXECUTED`
- Next workflow status: `KNOWLEDGE_MERGE_ALREADY_EXECUTED_RUN_POST_MERGE_AUDIT`
- Strategy: `create_separate_dictionary_context_index`
- Planned target index: `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json`
- Staged rows: `68395`
- Unique chars: `49085`
- Overlap with 8105 base: `7321`
- Outside 8105 base: `41764`

## Planned Write Set

- `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/dictionary_context_index.json`: create (requires authorization)
- `/Users/liuzhaoqi/Documents/cnbe-research/knowledge/references.json`: backup_then_update_reference_entry (requires authorization)

## Blocked Actions

- modify base_character_data.json
- modify cnbe_character_knowledge.json
- assign GF0017 scores
- emit final structure labels
- write CNBE rows
- rebuild CNBE database

## Checks

- `review_join_passed`: True
- `staging_db_exists`: True
- `staged_rows_match_manifest`: True
- `unique_chars_match_manifest`: True
- `target_structured_root_exists`: True
- `target_index_state_valid`: True
- `core_8105_files_not_modified`: True
- `knowledge_write_blocked_pending_authorization`: False
- `formal_scoring_blocked`: True
