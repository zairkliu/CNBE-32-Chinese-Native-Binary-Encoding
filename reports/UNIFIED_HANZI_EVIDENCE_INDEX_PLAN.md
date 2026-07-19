# Unified Hanzi Evidence Index Plan

## Purpose

Plan a Unicode-keyed evidence graph before any CNBE row repair, formal GF0017 scoring, or database reconstruction.

The planned index is evidence infrastructure only. It does not assign
GF0017 scores, emit final structure labels, repair CNBE rows, or rebuild
databases.

## Result

- Overall status: `PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY`
- Next workflow status: `UNIFIED_EVIDENCE_INDEX_BUILD_READY_FORMAL_SCORING_BLOCKED`
- May build unified evidence index: `True`
- May start formal GF0017 scoring: `False`
- May write CNBE rows: `False`
- May rebuild database: `False`

## Input Layers

| Layer | Count | Role |
|---|---:|---|
| `base_character_data` | 8105 | national_standard_core |
| `cnbe_character_knowledge` | 8105 | national_standard_core_enriched |
| `dictionary_context_index` | 49085 | dictionary_cross_reference_context |
| `yuanliu_index` | 9574 | character_origin_cross_reference |
| `cihai_index` | 5423 | dictionary_cross_reference_context |
| `wikipedia_corpus` | 1489790 | lowest_tier_semantic_cross_reference |
| `unihan2_archive` | n/a | unicode_identity_cross_reference |
| `legacy_unihan_archive` | n/a | excluded_legacy_artifact |

## Planned Entry Fields

- `unicode`
- `char`
- `codepoint`
- `catalog_scope`
- `national_standard_core`
- `dictionary_context`
- `origin_context`
- `wiki_context`
- `legacy_cnbe_context`
- `agent_standard_context`
- `gf0017_item_statuses`
- `evidence_gaps`
- `review_status`
- `allowed_next_action`

## Forbidden Before Later Gates

- `gf0017_score`
- `final_structure_label`
- `cnbe32_repair_value`
- `database_write_record`

## Checks

- `unicode_identity_passed`: True
- `full_catalog_rows_match`: True
- `knowledge_inventory_review_required`: True
- `knowledge_inventory_no_blockers`: True
- `source_audit_passed`: True
- `source_audit_review_required`: True
- `dictionary_merge_audited`: True
- `base_8105_count`: True
- `cnbe_8105_count`: True
- `dictionary_context_count`: True
- `agent_join_ready`: True
- `formal_scoring_blocked`: True

## Decision

Source gates are now REVIEW_REQUIRED rather than NO_GO, so a read-only evidence index may be materialized. Scoring and database work remain blocked until the index is audited.
