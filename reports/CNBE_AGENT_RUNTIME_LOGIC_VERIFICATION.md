# CNBE Agent Runtime Logic Verification

## Purpose

This report verifies that the CNBE Hanzi structure Agent follows the
current runtime gate order before the project moves from preparation
into source-evidence and GF0017 preflight planning.

The verification is read-only. It does not generate CNBE rows, rebuild
databases, modify workbooks, create tags, publish releases, or upload to
PyPI.

## Result

- Overall status: `PASS`
- Next workflow status: `PREFLIGHT_ALLOWED_BATCH_SCORING_BLOCKED`
- May start GF0017 preflight plan: `True`
- May start batch GF0017 scoring: `False`
- May rebuild database: `False`

## Gate Results

| Gate | Status | Meaning |
|---|:---:|---|
| `unicode_first_agent_gate` | PASS | 20,902 legacy CNBE rows have unique Unicode identity and no Unicode blocker. |
| `legacy_structure_localization_gate` | PASS | All legacy English structure labels are localized and preserved as review signals. |
| `cnbe32_carrier_separation_gate` | PASS | CNBE32 bitfield review is separated from Unicode identity and cannot silently repair rows. |
| `checkpoint_resume_gate` | PASS | Checkpoint reports a complete no-blocker scan and a resume offset after the final row. |
| `knowledge_asset_stop_gate` | PASS | Knowledge assets preserve a gated state before scoring or database generation. |
| `full_catalog_pre_gf0017_gate` | PASS | Full catalog preparation passes schema, sample, and Unicode identity gates. |
| `gf0017_status_preservation_gate` | PASS | GF0017 scoring preserves EVIDENCE_GAP, REVIEW_REQUIRED, and repair-candidate statuses. |

## Key Counts

- `agent_rows`: 20902
- `agent_unicode_pass`: 20902
- `legacy_structure_localization_required`: 20902
- `cnbe32_review_required`: 12864
- `full_catalog_rows`: 97686
- `gf0017_rows`: 8105
- `knowledge_blockers`: 0
- `knowledge_warnings`: 1

## Expected NO-GO Reasons

- None.

## Decision

Runtime logic passes, but source evidence mapping and review-required asset notes must be handled before batch scoring or database reconstruction.

The Agent runtime logic is acceptable for the next preflight planning
step, but it correctly blocks batch scoring and database reconstruction.
