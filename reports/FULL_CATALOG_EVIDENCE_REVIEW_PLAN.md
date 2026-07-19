# Full Catalog Evidence Review Plan

## Purpose

This report reviews row-level extraction-status results and prioritizes
the next parser implementation work for outside-8105 Agent-standard
mapping candidates.

It does not assign GF0017 scores, modify the workbook, change CNBE rows,
rebuild databases, create tags, publish releases, or upload to PyPI.

## Result

- Overall status: `PASS_EVIDENCE_REVIEW_PLAN_READY`
- Next workflow status: `PARSER_IMPLEMENTATION_PLAN_ALLOWED_FORMAL_SCORING_BLOCKED`
- Outside-8105 rows: `89581`
- Review items: `7`
- Highest-priority item: `structure_first_decomposition`
- Formal GF0017 scoring allowed: `False`
- Database rebuild allowed: `False`
- CNBE row write allowed: `False`

## Priority Order

- 1. `structure_first_decomposition` (20 pts): pending_rows=89581; phase=`implement_structure_decomposition_parser`
- 2. `component_name_validity` (8 pts): pending_rows=89581; phase=`implement_component_name_parser`
- 3. `independent_character_rule` (7 pts): pending_rows=89581; phase=`implement_independent_character_parser`
- 4. `component_validity` (3 pts): pending_rows=89581; phase=`implement_component_inventory_parser`
- 5. `radical_validity` (3 pts): pending_rows=89581; phase=`implement_radical_parser`
- 6. `stroke_order` (3 pts): pending_rows=89581; phase=`implement_stroke_order_parser`
- 7. `stroke_shape` (3 pts): pending_rows=89581; phase=`implement_stroke_shape_parser`

## Work Packages

- `ERP1_high_value_structure_review`: automation_allowed=`True`; items=structure_first_decomposition, component_name_validity, independent_character_rule
- `ERP2_supporting_component_radical_review`: automation_allowed=`True`; items=component_validity, radical_validity
- `ERP3_stroke_review`: automation_allowed=`True`; items=stroke_order, stroke_shape
- `ERP4_policy_review`: automation_allowed=`False`; items=character_set_coverage

## Decision

Evidence-review planning is ready. The next safe step is parser implementation planning for high-priority evidence items, with formal scoring still blocked.

The next allowed implementation step is parser implementation
planning. Formal scoring, database reconstruction, and CNBE row
writes remain blocked.

## Next Artifacts

- `scripts/plan_full_catalog_parser_implementation.py`
- `reports/full_catalog_parser_implementation_plan.json`
- `reports/FULL_CATALOG_PARSER_IMPLEMENTATION_PLAN.md`
