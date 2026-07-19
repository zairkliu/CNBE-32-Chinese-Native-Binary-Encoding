# Full Catalog Parser Implementation Plan

## Purpose

This report plans parser implementation phases for outside-8105 evidence
review. It is a plan, not parser execution.

It does not assign GF0017 scores, modify source assets, modify the
workbook, change CNBE rows, rebuild databases, create tags, publish
releases, or upload to PyPI.

## Result

- Overall status: `PASS_PARSER_IMPLEMENTATION_PLAN_READY`
- Next workflow status: `PARSER_PHASE_1_PLANNING_COMPLETE_IMPLEMENTATION_REQUIRES_REVIEW`
- Outside-8105 rows: `89581`
- Phases: `7`
- Phase 1 item: `structure_first_decomposition`
- Formal GF0017 scoring allowed: `False`
- Source asset write allowed: `False`
- CNBE row write allowed: `False`

## Implementation Phases

- Phase 1: `structure_first_decomposition` -> `run_structure_decomposition_evidence_parser`; sample=300
- Phase 2: `component_name_validity` -> `run_component_name_evidence_parser`; sample=240
- Phase 3: `independent_character_rule` -> `run_independent_character_evidence_parser`; sample=200
- Phase 4: `component_validity` -> `run_component_inventory_evidence_parser`; sample=180
- Phase 5: `radical_validity` -> `run_radical_evidence_parser`; sample=160
- Phase 6: `stroke_order` -> `run_stroke_order_evidence_parser`; sample=160
- Phase 7: `stroke_shape` -> `run_stroke_shape_evidence_parser`; sample=160

## Stop Conditions

- `source_path_missing`
- `unicode_join_mismatch`
- `ambiguous_evidence_value`
- `source_grade_unresolved`
- `attempted_point_assignment`
- `attempted_cnbe_row_write`

## Decision

Parser implementation planning is ready. The next decision point is whether to implement phase 1 as a read-only structure/decomposition parser.

Phase 1 implementation is the next decision point. It must remain
read-only unless separately authorized.

## Next Artifacts

- `scripts/run_structure_decomposition_evidence_parser.py`
- `reports/structure_decomposition_evidence_parser.json`
- `reports/STRUCTURE_DECOMPOSITION_EVIDENCE_PARSER.md`
