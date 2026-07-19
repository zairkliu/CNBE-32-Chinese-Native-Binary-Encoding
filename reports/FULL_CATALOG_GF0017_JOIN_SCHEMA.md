# Full Catalog GF0017 Join Schema

## Purpose

This report defines the row-level join contract for connecting v4_fixed
workbook rows with Unicode identity, GF0017 source items, Agent structure
localization, standard Hanzi knowledge, and CNBE32 carrier snapshots.

It is read-only. It does not score rows, modify the workbook, rebuild
databases, change CNBE32 values, create tags, publish releases, or upload
to PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `JOIN_SCHEMA_READY_BLOCKER_RECONCILIATION_REQUIRED`
- Data rows: `97686`
- Workbook columns: `17`
- GF0017 items: `8`
- Evidence tables: `5`
- Knowledge blockers: `3`
- May start blocker reconciliation: `True`
- May start batch GF0017 scoring: `False`

## Evidence Tables

| Table | Join key | Status policy |
|---|---|---|
| `unicode_identity` | `char`, `unicode` | BLOCKER on mismatch |
| `gf0017_source_items` | `gf0017_item_id` | SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED must be preserved |
| `agent_structure_localization` | `legacy_structure_label` | BLOCKER if a legacy label has no Agent localization |
| `standard_hanzi_knowledge` | `char`, `unicode` | BLOCKER if required source grade is unresolved |
| `cnbe32_carrier_snapshot` | `char`, `unicode` | review signal only; cannot prove normative correctness |

## Required Row Fields

- `row_offset`
- `worksheet_row`
- `char`
- `unicode`
- `codepoint`
- `normalization_status`
- `scope_status`
- `workbook_fields`
- `source_evidence`
- `agent_localization`
- `gf0017_items`
- `blockers`
- `checkpoint`

## Blocker Rules

| Code | Gate | Action |
|---|---|---|
| `UNICODE_IDENTITY_MISMATCH` | Unicode identity | stop batch and write checkpoint |
| `SOURCE_GRADE_UNRESOLVED` | Source evidence | stop or isolate affected row/item before scoring |
| `LEGACY_STRUCTURE_NOT_LOCALIZED` | Agent standard localization | stop until legacy label maps to one of the 13 Agent labels |
| `AGENT_STANDARD_MISLABELED_AS_NATIONAL` | Authority boundary | stop and correct standard_level |
| `CNBE32_WRITE_ATTEMPT` | No-write boundary | stop; this phase cannot modify workbook/database/CNBE rows |
| `KNOWLEDGE_ASSET_BLOCKER` | Knowledge inventory | reconcile or explicitly exclude the blocker before batch scoring |

## Score Policy

- Score values allowed in this phase: `False`
- Numeric score before batch phase: `FORBIDDEN`
- Source gap as pass: `FORBIDDEN`

## Decision

The join schema is explicit, but knowledge blockers and source-evidence joins must be reconciled before row scoring.

The next allowed step is blocker reconciliation and source-evidence join
readiness. Batch GF0017 scoring remains blocked.

## Next Artifacts

- `reports/full_catalog_gf0017_blocker_reconciliation.json`
- `reports/FULL_CATALOG_GF0017_BLOCKER_RECONCILIATION.md`
- `scripts/reconcile_full_catalog_gf0017_blockers.py`
