#!/usr/bin/env python3
"""Plan parser implementation for prioritized CNBE evidence items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EVIDENCE_REVIEW = Path("reports/full_catalog_evidence_review_plan.json")
EXTRACTION_SPECS = Path("reports/full_catalog_row_level_extraction_specs.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_parser_implementation_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_PARSER_IMPLEMENTATION_PLAN.md")


PHASE_RULES = {
    "structure_first_decomposition": {
        "phase": 1,
        "implementation_unit": "structure_decomposition_parser",
        "runner_name": "run_structure_decomposition_evidence_parser",
        "review_sample_size": 300,
        "validation_focus": [
            "13_label_structure_set",
            "legacy_label_preservation",
            "decomposition_ambiguity_detection",
        ],
    },
    "component_name_validity": {
        "phase": 2,
        "implementation_unit": "component_name_parser",
        "runner_name": "run_component_name_evidence_parser",
        "review_sample_size": 240,
        "validation_focus": [
            "gf0014_name_alignment",
            "ocr_only_name_is_review_aid",
            "component_name_mismatch_detection",
        ],
    },
    "independent_character_rule": {
        "phase": 3,
        "implementation_unit": "independent_character_parser",
        "runner_name": "run_independent_character_evidence_parser",
        "review_sample_size": 200,
        "validation_focus": [
            "gf0013_status_join",
            "invalid_component_split_detection",
            "unknown_status_preserved",
        ],
    },
    "component_validity": {
        "phase": 4,
        "implementation_unit": "component_inventory_parser",
        "runner_name": "run_component_inventory_evidence_parser",
        "review_sample_size": 180,
        "validation_focus": [
            "component_inventory_join",
            "contextual_decomposition_boundary",
            "unknown_marker_detection",
        ],
    },
    "radical_validity": {
        "phase": 5,
        "implementation_unit": "radical_evidence_parser",
        "runner_name": "run_radical_evidence_parser",
        "review_sample_size": 160,
        "validation_focus": [
            "gg0011_radical_alignment",
            "numeric_radical_code_check",
            "rsindex_cross_reference_boundary",
        ],
    },
    "stroke_order": {
        "phase": 6,
        "implementation_unit": "stroke_order_parser",
        "runner_name": "run_stroke_order_evidence_parser",
        "review_sample_size": 160,
        "validation_focus": [
            "stroke_count_order_length_match",
            "normalized_stroke_code_domain",
            "outside_8105_missing_order_preserved",
        ],
    },
    "stroke_shape": {
        "phase": 7,
        "implementation_unit": "stroke_shape_parser",
        "runner_name": "run_stroke_shape_evidence_parser",
        "review_sample_size": 160,
        "validation_focus": [
            "folded_stroke_evidence_boundary",
            "shape_status_not_direct_without_anchor",
            "ambiguous_shape_detection",
        ],
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_phase(review_item: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    rule = PHASE_RULES[review_item["gf0017_item"]]
    return {
        "phase": rule["phase"],
        "gf0017_item": review_item["gf0017_item"],
        "points": review_item["points"],
        "pending_rows": review_item["pending_rows"],
        "implementation_unit": rule["implementation_unit"],
        "runner_name": rule["runner_name"],
        "input_sources": spec["input_source_paths"],
        "output_table": spec["output_table"],
        "output_fields": spec["output_fields"],
        "failure_codes": spec["failure_codes"],
        "validation_focus": rule["validation_focus"],
        "review_sample_size": rule["review_sample_size"],
        "allowed_now": True,
        "writes_source_assets": False,
        "assigns_points": False,
        "writes_cnbe_rows": False,
        "rebuilds_database": False,
        "stop_conditions": [
            "source_path_missing",
            "unicode_join_mismatch",
            "ambiguous_evidence_value",
            "source_grade_unresolved",
            "attempted_point_assignment",
            "attempted_cnbe_row_write",
        ],
    }


def build_parser_implementation_plan() -> dict[str, Any]:
    review = load_json(EVIDENCE_REVIEW)
    specs = load_json(EXTRACTION_SPECS)
    spec_by_item = {spec["gf0017_item"]: spec for spec in specs["extraction_specs"]}
    phases = [
        build_phase(item, spec_by_item[item["gf0017_item"]])
        for item in review["review_items"]
    ]
    phases = sorted(phases, key=lambda item: item["phase"])
    status = (
        "PASS_PARSER_IMPLEMENTATION_PLAN_READY"
        if review["overall_status"] == "PASS_EVIDENCE_REVIEW_PLAN_READY"
        and len(phases) == 7
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_parser_implementation_plan",
        "overall_status": status,
        "next_workflow_status": "PARSER_PHASE_1_PLANNING_COMPLETE_IMPLEMENTATION_REQUIRES_REVIEW",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": review["summary"]["outside_8105_rows"],
            "phases": len(phases),
            "phase_1_item": phases[0]["gf0017_item"],
            "policy_decision_items": review["summary"]["policy_decision_items"],
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "implementation_phases": phases,
        "agent_model_stage": {
            "stage_id": "parser_implementation_plan",
            "input": str(EVIDENCE_REVIEW),
            "outputs": [str(DEFAULT_JSON_OUTPUT), str(DEFAULT_MARKDOWN_OUTPUT)],
            "invariants": [
                "parser_plan_is_not_parser_execution",
                "source_assets_are_read_only",
                "parser_outputs_are_evidence_statuses_before_scores",
                "phase_1_targets_structure_first_decomposition",
            ],
        },
        "decision": {
            "may_start_parser_phase_1_implementation": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Parser implementation planning is ready. The next decision point is whether to implement "
                "phase 1 as a read-only structure/decomposition parser."
            ),
        },
        "next_artifacts": [
            "scripts/run_structure_decomposition_evidence_parser.py",
            "reports/structure_decomposition_evidence_parser.json",
            "reports/STRUCTURE_DECOMPOSITION_EVIDENCE_PARSER.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Parser Implementation Plan",
        "",
        "## Purpose",
        "",
        "This report plans parser implementation phases for outside-8105 evidence",
        "review. It is a plan, not parser execution.",
        "",
        "It does not assign GF0017 scores, modify source assets, modify the",
        "workbook, change CNBE rows, rebuild databases, create tags, publish",
        "releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- Phases: `{report['summary']['phases']}`",
        f"- Phase 1 item: `{report['summary']['phase_1_item']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Source asset write allowed: `{report['summary']['source_asset_write_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Implementation Phases",
        "",
    ]
    for phase in report["implementation_phases"]:
        lines.append(
            f"- Phase {phase['phase']}: `{phase['gf0017_item']}` -> "
            f"`{phase['runner_name']}`; sample={phase['review_sample_size']}"
        )

    lines.extend(["", "## Stop Conditions", ""])
    for condition in report["implementation_phases"][0]["stop_conditions"]:
        lines.append(f"- `{condition}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "Phase 1 implementation is the next decision point. It must remain",
            "read-only unless separately authorized.",
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in report["next_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_parser_implementation_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"next_workflow_status={report['next_workflow_status']}")
    if not report["overall_status"].startswith("PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
