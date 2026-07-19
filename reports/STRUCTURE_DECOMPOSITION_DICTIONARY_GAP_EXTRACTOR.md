# Structure/Decomposition Dictionary Gap Extractor

## Purpose

This report extracts read-only review context from 汉字源流 and 辞海
indexes for Phase 1 structure/decomposition source gaps.

It does not assign GF0017 scores, modify source assets, write CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_DICTIONARY_GAP_REVIEW_PACKET_READY`
- Next workflow status: `DICTIONARY_REVIEW_PACKET_READY_WIKI_INDEX_PLAN_OPTIONAL_FORMAL_SCORING_BLOCKED`
- Source-gap rows: `85001`
- Score values assigned: `0`
- Formal GF0017 scoring allowed: `False`

## Review Status Counts

- `DICTIONARY_AND_YUANLIU_REVIEW_READY`: 2
- `DICTIONARY_CONTEXT_REVIEW_READY`: 30
- `NO_DICTIONARY_REVIEW_HIT`: 84939
- `YUANLIU_REVIEW_READY`: 30

## Source Hit Counts

- `cihai`: 32
- `yuanliu`: 32

## Decision

Dictionary and character-origin review packets are available for the small subset of source-gap rows with hits. Remaining rows still need source expansion or an optional offline-Wiki streaming index plan.
