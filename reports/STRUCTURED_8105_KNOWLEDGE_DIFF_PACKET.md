# Structured 8105 Knowledge Diff Packet

## Purpose

This packet compares the repository 8105 baseline with structured
`cnbe-research` knowledge files that currently block full-catalog GF0017
batch scoring.

It is read-only. It does not modify `cnbe-research`, score workbook rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `PATCH_REVIEW_REQUIRED_BEFORE_SOURCE_WRITE`
- Baseline count: `8105`
- Datasets checked: `2`
- Total missing rows: `0`
- Total extra rows: `0`
- Total Unicode label issues: `0`
- Source write allowed: `False`
- Batch scoring allowed: `False`

## Dataset Diffs

| Dataset | Count | Missing | Extra | Unicode label issues |
|---|---:|---:|---:|---:|
| `base_character_data` | 8105 | 0 | 0 | 0 |
| `cnbe_character_knowledge` | 8105 | 0 | 0 | 0 |

## Missing Characters

### base_character_data
- None.

### cnbe_character_knowledge
- None.

## Extra Characters

### base_character_data
- None.

### cnbe_character_knowledge
- None.

## Decision Point

Human authorization is required before writing to structured knowledge files.

Safe patch scope if authorized:

- add missing 8105 rows to base_character_data.json
- review or exclude extra rows that are outside the repository 8105 baseline
- add or regenerate corresponding enriched knowledge rows
- normalize Unicode labels in both structured files

Still forbidden without authorization:

- write to cnbe-research/knowledge/structured
- start full-catalog GF0017 row scoring
- rebuild CNBE SQLite database

## Next Artifacts After Authorization

- `reports/structured_8105_knowledge_patch_plan.json`
- `reports/STRUCTURED_8105_KNOWLEDGE_PATCH_PLAN.md`
- `scripts/patch_structured_8105_knowledge.py`
