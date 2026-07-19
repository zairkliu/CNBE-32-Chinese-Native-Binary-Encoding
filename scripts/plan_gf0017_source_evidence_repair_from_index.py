#!/usr/bin/env python3
"""Plan GF0017 source-evidence repair from the existing unified index.

The plan reads the current GF0017 scoring report and existing extraction specs.
It does not regenerate Unicode identity, write CNBE rows, or rebuild databases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCORING_REPORT = Path("reports/unified_hanzi_gf0017_scoring_from_index.json")
UNIFIED_INDEX = Path("reports/unified_hanzi_evidence_index.json")
EXTRACTION_SPECS = Path("reports/full_catalog_row_level_extraction_specs.json")

DEFAULT_JSON_OUTPUT = Path("reports/gf0017_source_evidence_repair_plan_from_index.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_FROM_INDEX.md")

GF0017_ITEM_ORDER = [
    "structure_first_decomposition",
    "component_name_validity",
    "independent_character_rule",
    "component_validity",
    "radical_validity",
    "stroke_order",
    "stroke_shape",
    "character_set_coverage",
]

ITEM_LABELS = {
    "character_set_coverage": "字符集覆盖",
    "stroke_shape": "笔形",
    "stroke_order": "笔顺",
    "component_validity": "汉字部件",
    "component_name_validity": "部件名称",
    "radical_validity": "部首",
    "independent_character_rule": "独体字规则",
    "structure_first_decomposition": "结构优先拆分",
}

ITEM_REPAIR_STRATEGIES = {
    "character_set_coverage": {
        "repair_class": "policy_scope_boundary",
        "automation_allowed": False,
        "evidence_target": "outside-8105 project scope policy and inclusion/exclusion review",
        "primary_sources": ["8105 baseline", "project scope manifest", "Unicode block classification"],
        "blocked_by": "outside-8105 rows are Agent candidates, not national-standard coverage rows",
    },
    "stroke_shape": {
        "repair_class": "source_extraction_and_normalization",
        "automation_allowed": True,
        "evidence_target": "row-level stroke-shape or folded-stroke status",
        "primary_sources": ["GB 13000.1 字符集汉字折笔规范", "GF0017 normative item"],
        "blocked_by": "stroke-shape source has not been materialized into the unified index",
    },
    "stroke_order": {
        "repair_class": "row_level_standard_join",
        "automation_allowed": True,
        "evidence_target": "stroke count and stroke-order sequence with source anchor",
        "primary_sources": ["GF3002", "GF0031", "8105 structured stroke-order extracts"],
        "blocked_by": "stroke-order source evidence has not been joined into the unified index",
    },
    "component_validity": {
        "repair_class": "row_level_component_join",
        "automation_allowed": True,
        "evidence_target": "component inventory, basic components, and unresolved-marker status",
        "primary_sources": ["GF0014", "GB13000.1 component specification", "review-only decomposition cross-references"],
        "blocked_by": "component inventory is not present as scoring evidence",
    },
    "component_name_validity": {
        "repair_class": "component_name_authority_join",
        "automation_allowed": True,
        "evidence_target": "component names normalized to GF0014 naming inventory",
        "primary_sources": ["GF0014 现代常用字部件及部件名称规范"],
        "blocked_by": "component names are not joined and source-graded per row",
    },
    "radical_validity": {
        "repair_class": "radical_authority_join",
        "automation_allowed": True,
        "evidence_target": "radical identity and radical-system source grade",
        "primary_sources": ["GG0011 汉字部首表", "8105 structured data", "Unicode RSIndex as cross-reference only"],
        "blocked_by": "radical evidence is not present in the scoring index",
    },
    "independent_character_rule": {
        "repair_class": "independent_character_join",
        "automation_allowed": True,
        "evidence_target": "独体字 status and component-split rule compliance",
        "primary_sources": ["GF0013 现代常用独体字规范", "GF0014 component/decomposition evidence"],
        "blocked_by": "independent-character status is not materialized per row",
    },
    "structure_first_decomposition": {
        "repair_class": "structure_decomposition_authority_join",
        "automation_allowed": True,
        "evidence_target": "13-label structure, decomposition tree, and source-grade status",
        "primary_sources": ["GF0014", "GB13000.1 component specification", "Agent 13-label localization"],
        "blocked_by": "structure/decomposition evidence is missing or only review-context for most rows",
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


def load_specs_by_item() -> dict[str, dict[str, Any]]:
    if not EXTRACTION_SPECS.is_file():
        return {}
    specs = load_json(EXTRACTION_SPECS)
    return {
        spec["gf0017_item"]: spec
        for spec in specs.get("extraction_specs", [])
    }


def blocked_rows_for_item(item: str, counts: dict[str, int]) -> int:
    return sum(
        count
        for status, count in counts.items()
        if status.startswith("NOT_SCORABLE")
    )


def assigned_rows_for_item(counts: dict[str, int]) -> int:
    return sum(
        count
        for status, count in counts.items()
        if status.startswith("PASS") or status.startswith("READY")
    )


def build_item_plans(scoring: dict[str, Any], specs_by_item: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    item_plans: list[dict[str, Any]] = []
    points = scoring["gf0017_points"]
    for item in GF0017_ITEM_ORDER:
        counts = scoring["item_status_counts"][item]
        strategy = ITEM_REPAIR_STRATEGIES[item]
        spec = specs_by_item.get(item, {})
        blocked_rows = blocked_rows_for_item(item, counts)
        item_plans.append(
            {
                "item": item,
                "label_zh": ITEM_LABELS[item],
                "points": points[item],
                "blocked_rows": blocked_rows,
                "assigned_or_ready_rows": assigned_rows_for_item(counts),
                "blocked_point_weight": blocked_rows * points[item],
                "current_status_counts": counts,
                "repair_class": strategy["repair_class"],
                "automation_allowed": strategy["automation_allowed"],
                "evidence_target": strategy["evidence_target"],
                "primary_sources": strategy["primary_sources"],
                "blocked_by": strategy["blocked_by"],
                "existing_spec_id": spec.get("spec_id"),
                "existing_spec_input_paths": spec.get("input_source_paths", []),
                "required_output_status": "ROW_LEVEL_EVIDENCE_MATERIALIZED_NOT_SCORED",
                "score_allowed_after_repair_plan": False,
            }
        )
    return item_plans


def build_work_packages(item_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policy_items = [item for item in item_plans if not item["automation_allowed"]]
    return [
        {
            "id": "GER1_structure_decomposition_first",
            "priority": 1,
            "items": ["structure_first_decomposition"],
            "reason": "20-point item and current dominant blocker; repair here unlocks component and independent-character review.",
            "automation_allowed": True,
            "expected_output": "row-level structure/decomposition evidence status, no final labels",
        },
        {
            "id": "GER2_component_name_and_component_inventory",
            "priority": 2,
            "items": ["component_name_validity", "component_validity"],
            "reason": "component names carry 8 points and depend on component inventory evidence.",
            "automation_allowed": True,
            "expected_output": "GF0014-aligned component/name evidence statuses, no scores",
        },
        {
            "id": "GER3_independent_radical_stroke_evidence",
            "priority": 3,
            "items": ["independent_character_rule", "radical_validity", "stroke_order", "stroke_shape"],
            "reason": "remaining row-level evidence items required before a complete 50-point score is possible.",
            "automation_allowed": True,
            "expected_output": "row-level evidence statuses and source anchors, no CNBE writes",
        },
        {
            "id": "GER4_character_set_policy_boundary",
            "priority": 4,
            "items": [item["item"] for item in policy_items],
            "reason": "outside-8105 character-set coverage requires project-scope policy, not automatic national-standard scoring.",
            "automation_allowed": False,
            "expected_output": "human policy decision before outside-8105 coverage points",
        },
        {
            "id": "GER5_rescore_from_repaired_index",
            "priority": 5,
            "items": [item["item"] for item in item_plans],
            "reason": "rescore only after repaired evidence is materialized into the existing index schema.",
            "automation_allowed": False,
            "expected_output": "explicit authorization to rescore; no CNBE/database writes",
        },
    ]


def build_repair_plan() -> dict[str, Any]:
    scoring = load_json(SCORING_REPORT)
    unified_index = load_json(UNIFIED_INDEX)
    specs_by_item = load_specs_by_item()
    item_plans = build_item_plans(scoring, specs_by_item)
    total_blocked_point_weight = sum(item["blocked_point_weight"] for item in item_plans)
    automatic_items = [item["item"] for item in item_plans if item["automation_allowed"]]
    policy_items = [item["item"] for item in item_plans if not item["automation_allowed"]]
    checks = {
        "scoring_report_passed_with_source_gaps": scoring["overall_status"]
        == "PASS_GF0017_SCORING_FROM_EXISTING_INDEX_WITH_SOURCE_GAPS",
        "uses_existing_unified_index_only": scoring["checks"]["uses_existing_unified_index_only"],
        "unified_index_row_count_match": unified_index["summary"]["total_entries"] == 97_686,
        "does_not_regenerate_unicode": True,
        "does_not_assign_new_points": True,
        "does_not_write_cnbe_rows": True,
        "does_not_rebuild_database": True,
    }
    status = "PASS_GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_gf0017_source_evidence_repair_plan_from_existing_index",
        "overall_status": status,
        "next_workflow_status": "STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_ALLOWED_NO_SCORING",
        "authority_boundary": {
            "uses_existing_unified_index_only": True,
            "does_not_regenerate_full_unicode_catalog": True,
            "does_not_assign_new_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "summary": {
            "total_rows": scoring["summary"]["total_rows_evaluated"],
            "rows_with_any_assigned_points": scoring["summary"]["rows_with_any_assigned_points"],
            "rows_fully_scored": scoring["summary"]["rows_fully_scored"],
            "automatable_repair_items": automatic_items,
            "policy_decision_items": policy_items,
            "total_blocked_point_weight": total_blocked_point_weight,
            "highest_priority_item": item_plans[0]["item"],
            "formal_scoring_allowed_after_plan": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "item_repair_plans": item_plans,
        "work_packages": build_work_packages(item_plans),
        "decision": {
            "may_start_structure_decomposition_evidence_repair": status.startswith("PASS"),
            "may_assign_new_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The scoring pass proved that source evidence, especially the "
                "20-point structure/decomposition item, must be materialized "
                "before full GF0017 scoring. The next allowed work is read-only "
                "evidence repair, not scoring or encoding writes."
            ),
        },
        "next_artifacts": [
            "scripts/repair_structure_decomposition_evidence_from_index.py",
            "reports/gf0017_structure_decomposition_evidence_repair_from_index.json",
            "reports/GF0017_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_FROM_INDEX.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GF0017 Source Evidence Repair Plan From Existing Index",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total rows: {report['summary']['total_rows']}",
        f"- Rows fully scored: {report['summary']['rows_fully_scored']}",
        f"- Highest priority item: `{report['summary']['highest_priority_item']}`",
        f"- Formal scoring allowed after plan: `{report['summary']['formal_scoring_allowed_after_plan']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "This plan uses the existing unified index and scoring report. It does",
        "not regenerate the full Unicode catalog.",
        "",
        "## Item Repair Queue",
        "",
        "| Priority | GF0017 item | Points | Blocked rows | Blocked point weight | Repair class |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for priority, item in enumerate(report["item_repair_plans"], start=1):
        lines.append(
            f"| {priority} | `{item['item']}` | {item['points']} | "
            f"{item['blocked_rows']} | {item['blocked_point_weight']} | "
            f"`{item['repair_class']}` |"
        )
    lines.extend(["", "## Work Packages", ""])
    for package in report["work_packages"]:
        lines.extend(
            [
                f"### {package['id']}",
                "",
                f"- Priority: {package['priority']}",
                f"- Automation allowed: `{package['automation_allowed']}`",
                f"- Items: `{', '.join(package['items'])}`",
                f"- Expected output: {package['expected_output']}",
                f"- Reason: {package['reason']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation is read-only structure/decomposition",
            "evidence repair. New GF0017 point assignment, final labels, CNBE row",
            "writes, and database rebuilds remain blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_repair_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"highest_priority={report['summary']['highest_priority_item']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
