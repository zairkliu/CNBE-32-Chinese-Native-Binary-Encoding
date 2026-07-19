#!/usr/bin/env python3
"""Plan evidence review after row-level extraction-status materialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXTRACTION_RESULTS = Path("reports/full_catalog_row_level_extraction_results.json")
EXTRACTION_SPECS = Path("reports/full_catalog_row_level_extraction_specs.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_evidence_review_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_EVIDENCE_REVIEW_PLAN.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581


REVIEW_PRIORITY = {
    "structure_first_decomposition": {
        "priority": 1,
        "points": 20,
        "reason": "largest GF0017 item and depends on structure/decomposition correctness",
        "parser_phase": "implement_structure_decomposition_parser",
    },
    "component_name_validity": {
        "priority": 2,
        "points": 8,
        "reason": "largest non-structure item and depends on component-name authority",
        "parser_phase": "implement_component_name_parser",
    },
    "independent_character_rule": {
        "priority": 3,
        "points": 7,
        "reason": "blocks invalid splitting of independent characters",
        "parser_phase": "implement_independent_character_parser",
    },
    "component_validity": {
        "priority": 4,
        "points": 3,
        "reason": "component inventory supports structure and component-name checks",
        "parser_phase": "implement_component_inventory_parser",
    },
    "radical_validity": {
        "priority": 5,
        "points": 3,
        "reason": "legacy CNBE radical code needs source-backed validation",
        "parser_phase": "implement_radical_parser",
    },
    "stroke_order": {
        "priority": 6,
        "points": 3,
        "reason": "stroke-order source exists but outside-8105 coverage needs review",
        "parser_phase": "implement_stroke_order_parser",
    },
    "stroke_shape": {
        "priority": 7,
        "points": 3,
        "reason": "source extraction specification is available, but folded-stroke policy remains sensitive",
        "parser_phase": "implement_stroke_shape_parser",
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


def build_review_items(results: dict[str, Any], specs: dict[str, Any]) -> list[dict[str, Any]]:
    spec_by_item = {spec["gf0017_item"]: spec for spec in specs["extraction_specs"]}
    items: list[dict[str, Any]] = []
    for item_name, priority in sorted(REVIEW_PRIORITY.items(), key=lambda pair: pair[1]["priority"]):
        counts = results["summary"]["item_status_counts"][item_name]
        spec = spec_by_item[item_name]
        pending_rows = counts.get("SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING", 0)
        items.append(
            {
                "gf0017_item": item_name,
                "priority": priority["priority"],
                "points": priority["points"],
                "pending_rows": pending_rows,
                "current_status_counts": counts,
                "parser_phase": priority["parser_phase"],
                "review_reason": priority["reason"],
                "input_sources": spec["input_source_paths"],
                "output_table": spec["output_table"],
                "failure_codes": spec["failure_codes"],
                "requires_human_before_scoring": True,
                "can_assign_points_now": False,
            }
        )
    return items


def build_work_packages(review_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": "ERP1_high_value_structure_review",
            "items": ["structure_first_decomposition", "component_name_validity", "independent_character_rule"],
            "automation_allowed": True,
            "purpose": "Implement highest-value parsers first and keep outputs as evidence statuses.",
            "blocks_formal_scoring": True,
        },
        {
            "id": "ERP2_supporting_component_radical_review",
            "items": ["component_validity", "radical_validity"],
            "automation_allowed": True,
            "purpose": "Implement supporting component and radical evidence parsers.",
            "blocks_formal_scoring": True,
        },
        {
            "id": "ERP3_stroke_review",
            "items": ["stroke_order", "stroke_shape"],
            "automation_allowed": True,
            "purpose": "Implement stroke-order and stroke-shape evidence parsers after structure priorities.",
            "blocks_formal_scoring": True,
        },
        {
            "id": "ERP4_policy_review",
            "items": ["character_set_coverage"],
            "automation_allowed": False,
            "purpose": "Human review of scope policy before the 3-point character-set item can be scored.",
            "blocks_formal_scoring": True,
        },
    ]


def build_evidence_review_plan() -> dict[str, Any]:
    results = load_json(EXTRACTION_RESULTS)
    specs = load_json(EXTRACTION_SPECS)
    review_items = build_review_items(results, specs)
    pending_rows_total = sum(item["pending_rows"] for item in review_items)
    status = (
        "PASS_EVIDENCE_REVIEW_PLAN_READY"
        if results["overall_status"] == "PASS_ROW_LEVEL_EXTRACTION_STATUS_MATERIALIZED"
        and results["summary"]["outside_8105_rows"] == EXPECTED_OUTSIDE_8105_ROWS
        and len(review_items) == 7
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_evidence_review_plan",
        "overall_status": status,
        "next_workflow_status": "PARSER_IMPLEMENTATION_PLAN_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": results["summary"]["outside_8105_rows"],
            "review_items": len(review_items),
            "pending_item_rows_total": pending_rows_total,
            "highest_priority_item": review_items[0]["gf0017_item"],
            "policy_decision_items": ["character_set_coverage"],
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
        },
        "review_items": review_items,
        "work_packages": build_work_packages(review_items),
        "agent_model_stage": {
            "stage_id": "evidence_review_plan",
            "input": str(EXTRACTION_RESULTS),
            "outputs": [str(DEFAULT_JSON_OUTPUT), str(DEFAULT_MARKDOWN_OUTPUT)],
            "invariants": [
                "pending_source_availability_is_not_evidence_value",
                "review_plan_does_not_assign_points",
                "character_set_coverage_remains_policy_decision",
                "parser_outputs_must_remain_auditable",
            ],
        },
        "decision": {
            "may_start_parser_implementation_plan": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Evidence-review planning is ready. The next safe step is parser implementation planning "
                "for high-priority evidence items, with formal scoring still blocked."
            ),
        },
        "next_artifacts": [
            "scripts/plan_full_catalog_parser_implementation.py",
            "reports/full_catalog_parser_implementation_plan.json",
            "reports/FULL_CATALOG_PARSER_IMPLEMENTATION_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Evidence Review Plan",
        "",
        "## Purpose",
        "",
        "This report reviews row-level extraction-status results and prioritizes",
        "the next parser implementation work for outside-8105 Agent-standard",
        "mapping candidates.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- Review items: `{report['summary']['review_items']}`",
        f"- Highest-priority item: `{report['summary']['highest_priority_item']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Priority Order",
        "",
    ]
    for item in report["review_items"]:
        lines.append(
            f"- {item['priority']}. `{item['gf0017_item']}` ({item['points']} pts): "
            f"pending_rows={item['pending_rows']}; phase=`{item['parser_phase']}`"
        )

    lines.extend(["", "## Work Packages", ""])
    for package in report["work_packages"]:
        lines.append(
            f"- `{package['id']}`: automation_allowed=`{package['automation_allowed']}`; "
            f"items={', '.join(package['items'])}"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is parser implementation",
            "planning. Formal scoring, database reconstruction, and CNBE row",
            "writes remain blocked.",
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
    report = build_evidence_review_plan()
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
