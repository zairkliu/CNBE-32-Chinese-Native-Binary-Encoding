# External Dictionary Context Import Plan

## Purpose

This plan selects dictionary context sources for a staging database. It
does not write `cnbe-research/knowledge`, assign GF0017 scores, emit
final structure labels, write CNBE rows, or rebuild CNBE databases.

## Result

- Overall status: `PASS_DICTIONARY_CONTEXT_IMPORT_PLAN_READY`
- Next workflow status: `STAGING_DICTIONARY_CONTEXT_BUILD_ALLOWED_KNOWLEDGE_WRITE_BLOCKED`
- Primary source: `leechenhwa2/nlp-han-dicts`
- Supporting source: `kanripo/KR1j0048`
- Secondary comparison source: `he426100/kangxi`
- Planned staging output: `build/dictionary_context_staging/dictionary_context_entries.sqlite`

## Source Priority

- `nlp_han_dicts_kangxi_4w`: primary_structured_kangxi_context; license `BSD-2-Clause`; allowed use: dictionary context and human-review evidence discovery.
- `nlp_han_dicts_zhonghua_dazidian`: primary_structured_zhonghua_dazidian_context; license `BSD-2-Clause`; allowed use: dictionary context and human-review evidence discovery.
- `kanripo_kr1j0048_text_witness`: supporting_primary_text_witness_after_parser_design; license `not_found_in_repository_snapshot`; allowed use: spot validation against Kangxi source text after parser design.
- `he426100_kangxi_secondary`: secondary_comparison_only; license `not_found_in_repository_snapshot`; allowed use: secondary comparison only.

## Checks

- `evaluation_passed`: True
- `primary_source_has_license`: True
- `primary_kangxi_rows_available`: True
- `primary_zhonghua_rows_available`: True
- `staging_schema_declared`: True
- `knowledge_write_blocked`: True
- `formal_scoring_blocked`: True

## Next Step

- `scripts/build_external_dictionary_context_staging.py`
