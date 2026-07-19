# Wikipedia Structure Cross-Reference Index Plan

## Purpose

This report plans a read-only streaming index over the offline Chinese
Wikipedia corpus for structure/decomposition source gaps that still lack
dictionary or character-origin hits.

Wiki evidence is lowest-tier cross-reference only. It must not assign
GF0017 scores, modify source assets, write CNBE rows, rebuild databases,
or claim national-standard authority.

## Result

- Overall status: `PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_PLAN_READY`
- Next workflow status: `OPTIONAL_WIKI_STREAMING_INDEX_REQUIRES_REVIEW_FORMAL_SCORING_BLOCKED`
- Wiki file exists: `True`
- Wiki file size bytes: `2393692848`
- Rows without dictionary review hit: `84939`
- Score values assigned: `0`

## Index Design

- `index_mode`: streaming_read_only_target_char_index
- `target_chars_source`: reports/structure_decomposition_dictionary_gap_extractor.json rows with NO_DICTIONARY_REVIEW_HIT
- `join_key`: char and unicode after Unicode identity verification
- `search_fields`: ['title', 'tags', 'text']
- `stored_fields`: ['id', 'title', 'tags', 'snippet', 'text_len']
- `max_hits_per_char`: 3
- `evidence_grade`: lowest_tier_cross_reference
- `forbidden_uses`: ['do_not_assign_gf0017_points_from_wiki', 'do_not_claim_national_standard_evidence_from_wiki', 'do_not_write_cnbe_rows_from_wiki', 'do_not_modify_source_assets']

## Decision

Offline Wikipedia can be indexed only as a lowest-tier cross-reference for rows without dictionary hits. The index should support human review and source discovery, not scoring or encoding.
