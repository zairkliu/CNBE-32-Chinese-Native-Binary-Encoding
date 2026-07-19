# External Dictionary Context Review Join

## Purpose

This report joins staged Kangxi and Zhonghua Dazidian dictionary context
to the current human-review packet and remaining Agent-standard rows.

It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit
final structure labels, write CNBE rows, or rebuild CNBE databases.

## Result

- Overall status: `PASS_DICTIONARY_CONTEXT_REVIEW_JOIN_READY`
- Next workflow status: `DICTIONARY_CONTEXT_REVIEW_PACKET_READY_KNOWLEDGE_IMPORT_BLOCKED`
- Dictionary context unique chars: `49085`
- Human review hit rows: `104` / `150`
- Human review hit rate: `0.693333`
- Remaining hit rows: `28960` / `73831`
- Remaining hit rate: `0.392247`
- Human dual-source rows: `61`
- Human single-source rows: `43`
- Human gap rows: `46`

## Checks

- `staging_db_exists`: True
- `human_review_rows_match_expected`: True
- `remaining_feature_rows_match_expected`: True
- `human_join_rows_match_expected`: True
- `dictionary_context_loaded`: True
- `knowledge_write_blocked`: True
- `formal_scoring_blocked`: True
- `final_structure_labels_blocked`: True

## Decision

Export reviewer-facing XLSX/CSV with dictionary context columns, then merge human review results in a later audited gate.
