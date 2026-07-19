# GF0017 Source Evidence Repair Plan From Existing Index

## Result

- Overall status: `PASS_GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_READY`
- Next workflow status: `STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_ALLOWED_NO_SCORING`
- Total rows: 97686
- Rows fully scored: 0
- Highest priority item: `structure_first_decomposition`
- Formal scoring allowed after plan: `False`
- CNBE row write allowed: `False`
- Database rebuild allowed: `False`

This plan uses the existing unified index and scoring report. It does
not regenerate the full Unicode catalog.

## Item Repair Queue

| Priority | GF0017 item | Points | Blocked rows | Blocked point weight | Repair class |
|---:|---|---:|---:|---:|---|
| 1 | `structure_first_decomposition` | 20 | 97686 | 1953720 | `structure_decomposition_authority_join` |
| 2 | `component_name_validity` | 8 | 97686 | 781488 | `component_name_authority_join` |
| 3 | `independent_character_rule` | 7 | 97686 | 683802 | `independent_character_join` |
| 4 | `component_validity` | 3 | 97686 | 293058 | `row_level_component_join` |
| 5 | `radical_validity` | 3 | 97686 | 293058 | `radical_authority_join` |
| 6 | `stroke_order` | 3 | 97686 | 293058 | `row_level_standard_join` |
| 7 | `stroke_shape` | 3 | 97686 | 293058 | `source_extraction_and_normalization` |
| 8 | `character_set_coverage` | 3 | 89581 | 268743 | `policy_scope_boundary` |

## Work Packages

### GER1_structure_decomposition_first

- Priority: 1
- Automation allowed: `True`
- Items: `structure_first_decomposition`
- Expected output: row-level structure/decomposition evidence status, no final labels
- Reason: 20-point item and current dominant blocker; repair here unlocks component and independent-character review.

### GER2_component_name_and_component_inventory

- Priority: 2
- Automation allowed: `True`
- Items: `component_name_validity, component_validity`
- Expected output: GF0014-aligned component/name evidence statuses, no scores
- Reason: component names carry 8 points and depend on component inventory evidence.

### GER3_independent_radical_stroke_evidence

- Priority: 3
- Automation allowed: `True`
- Items: `independent_character_rule, radical_validity, stroke_order, stroke_shape`
- Expected output: row-level evidence statuses and source anchors, no CNBE writes
- Reason: remaining row-level evidence items required before a complete 50-point score is possible.

### GER4_character_set_policy_boundary

- Priority: 4
- Automation allowed: `False`
- Items: `character_set_coverage`
- Expected output: human policy decision before outside-8105 coverage points
- Reason: outside-8105 character-set coverage requires project-scope policy, not automatic national-standard scoring.

### GER5_rescore_from_repaired_index

- Priority: 5
- Automation allowed: `False`
- Items: `structure_first_decomposition, component_name_validity, independent_character_rule, component_validity, radical_validity, stroke_order, stroke_shape, character_set_coverage`
- Expected output: explicit authorization to rescore; no CNBE/database writes
- Reason: rescore only after repaired evidence is materialized into the existing index schema.

## Decision

The scoring pass proved that source evidence, especially the 20-point structure/decomposition item, must be materialized before full GF0017 scoring. The next allowed work is read-only evidence repair, not scoring or encoding writes.

The next allowed implementation is read-only structure/decomposition
evidence repair. New GF0017 point assignment, final labels, CNBE row
writes, and database rebuilds remain blocked.
