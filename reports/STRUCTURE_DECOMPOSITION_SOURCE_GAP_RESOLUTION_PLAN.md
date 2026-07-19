# Structure/Decomposition Source-Gap Resolution Plan

## Purpose

This report plans how the Agent should resolve Phase 1 structure and
decomposition source gaps using standards first, then dictionary and
character-origin evidence, and only then offline Wiki as the lowest-tier
cross-reference.

It does not assign GF0017 scores, modify source assets, write CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_STRUCTURE_SOURCE_GAP_RESOLUTION_PLAN_READY`
- Next workflow status: `READ_ONLY_SOURCE_GAP_EXTRACTORS_ALLOWED_FORMAL_SCORING_BLOCKED`
- Source-gap rows: `85001`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`

## Source Hit Counts

- `hanzi_yuanliu_chars`: 32
- `cihai_search_index`: 32
- `definitions_index`: 0
- `wikipedia_offline_file_available`: 1

## Source Policy

- `national_standards`: direct evidence for standard fields when present
- `hanzi_yuanliu`: character-origin and decomposition clue source for review, not direct national-standard authority
- `cihai`: dictionary meaning and usage context for review, not direct structure authority
- `wikipedia_offline`: lowest-tier cross-reference only after standards and dictionaries; never direct scoring authority
- `llm_memory`: not an evidence source

## Resolution Phases

- Phase 1 `authoritative_standard_recheck`: 85001 eligible rows; tier `national_standard_or_standard_derived`
- Phase 2 `hanzi_yuanliu_structure_clue_extraction`: 32 eligible rows; tier `dictionary_or_character_origin_cross_reference`
- Phase 3 `cihai_definition_review_packet`: 32 eligible rows; tier `dictionary_cross_reference`
- Phase 4 `offline_wikipedia_lowest_tier_cross_reference`: 85001 eligible rows; tier `encyclopedia_lowest_tier_cross_reference`
- Phase 5 `human_review_and_rule_learning_packet`: 85001 eligible rows; tier `agent_standard_review`

## Decision

Source-gap resolution can proceed through read-only extractors and review packets. Dictionaries and Wikipedia may enrich evidence review, but they do not authorize formal scoring or CNBE row writes.
