# External Dictionary Context Import Manifest

## Purpose

This manifest records a staging-only dictionary context database built
from selected external Kangxi and Zhonghua Dazidian sources.

It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit
final structure labels, write CNBE rows, or rebuild CNBE databases.

## Result

- Overall status: `PASS_DICTIONARY_CONTEXT_STAGING_READY`
- Next workflow status: `STAGING_READY_KNOWLEDGE_IMPORT_REQUIRES_AUTHORIZATION`
- Staging DB: `build/dictionary_context_staging/dictionary_context_entries.sqlite`
- Staged rows: `68395`
- Unique chars: `49085`

## Source Counts

- `nlp_han_dicts_kangxi_4w`: 48708
- `nlp_han_dicts_zhonghua_dazidian`: 19687

## Checks

- `plan_passed`: True
- `staging_db_created`: True
- `staged_rows_positive`: True
- `unique_chars_positive`: True
- `knowledge_write_blocked`: True
- `formal_scoring_blocked`: True
