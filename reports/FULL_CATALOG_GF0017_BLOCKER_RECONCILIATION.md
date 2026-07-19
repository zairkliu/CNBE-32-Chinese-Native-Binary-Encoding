# Full Catalog GF0017 Blocker Reconciliation

## Purpose

This report classifies the remaining knowledge/source blockers before any
full-catalog GF0017 row scoring or database reconstruction begins.

It is read-only. It does not modify `cnbe-research`, change CNBE rows,
score workbook rows, rebuild databases, create tags, publish releases,
or upload to PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `DECISION_POINT_REACHED_READ_ONLY_DIFF_ALLOWED`
- Blockers: `1`
- Batch scoring allowed: `False`
- Database rebuild allowed: `False`
- Human decision required: `True`

## Classification Counts

- `EXCLUDE_OR_REPLACE_EXTERNAL_ARCHIVE`: 1

## Blockers

| Asset | Classification | Automation | Recommended action |
|---|---|---|---|
| `Unihan.zip` | EXCLUDE_OR_REPLACE_EXTERNAL_ARCHIVE | requires_human_or_network_asset_decision | Use the already verified Unihan2.zip or exclude Unihan.zip from authoritative inputs after human approval. |

## Decision Point

Choose whether to exclude/replace the corrupt Unihan.zip and whether to authorize read-only diff packet generation for the two structured 8105 knowledge files.

Requires authorization before write:

- delete or replace Unihan.zip
- modify structured/base_character_data.json
- modify structured/cnbe_character_knowledge.json
- start batch GF0017 scoring
- rebuild database

Safe next step without data write:

- create read-only structured-knowledge diff packet

## Next Artifacts

- `reports/structured_8105_knowledge_diff_packet.json`
- `reports/STRUCTURED_8105_KNOWLEDGE_DIFF_PACKET.md`
- `scripts/diff_structured_8105_knowledge.py`
