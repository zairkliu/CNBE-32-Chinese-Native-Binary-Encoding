# External Dictionary Source Candidate Evaluation

## Purpose

This report evaluates external Kangxi and Zhonghua Dazidian resources
as dictionary context candidates for CNBE human review and source-gap
resolution.

It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit
final structure labels, write CNBE rows, or rebuild databases.

## Result

- Overall status: `PASS_EXTERNAL_DICTIONARY_SOURCE_EVALUATION_READY`
- Next workflow status: `DICTIONARY_CONTEXT_IMPORT_PLAN_ALLOWED_KNOWLEDGE_WRITE_BLOCKED`
- Recommended primary source: `leechenhwa2/nlp-han-dicts`
- Recommended supporting source: `kanripo/KR1j0048`
- Recommended secondary comparison source: `he426100/kangxi`

## Candidate Summary

| Candidate | Role | License | Shape | Human 150 hit rate | Remaining 73,831 hit rate |
|---|---|---|---|---:|---:|
| leechenhwa2/nlp-han-dicts | primary_structured_dictionary_context_source | BSD-2-Clause | SQLite Kangxi + Zhonghua Dazidian | 0.693333 | 0.392247 |
| he426100/kangxi | secondary_comparison_only_until_license_and_quality_are_resolved | not_found_in_repository_snapshot | PostgreSQL dump/MDB | 0.0 | 0.0 |
| kanripo/KR1j0048 | primary_text_witness_for_spot_validation_after_parser_design | not_found_in_repository_snapshot | 41 Mandoku text files | n/a text hits 92 | n/a |

## Checks

- `nlp_kangxi_sqlite_exists`: True
- `nlp_zhonghua_dazidian_sqlite_exists`: True
- `nlp_license_is_declared_bsd_2_clause`: True
- `human_review_packet_rows_150`: True
- `remaining_feature_rows_73831`: True
- `no_formal_scoring_allowed`: True
- `no_knowledge_write_performed`: True

## Decision

Use nlp-han-dicts as the primary structured dictionary context source because it contains licensed SQLite Kangxi and Zhonghua Dazidian databases. Use KR1j0048 as a primary-text witness after parser design. Keep he426100/kangxi as secondary comparison only until licensing and data-quality blockers are resolved.
