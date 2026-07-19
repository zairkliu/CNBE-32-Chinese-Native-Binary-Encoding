#!/usr/bin/env python3
"""Plan source resolution for outside-8105 Agent mapping evidence gaps."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

EVIDENCE_JOIN = Path("reports/full_catalog_agent_mapping_evidence_join.json")
JOIN_DESIGN = Path("reports/full_catalog_agent_mapping_evidence_join_design.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_source_resolution_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_SOURCE_RESOLUTION_PLAN.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581


RESOLUTION_RULES = {
    "character_set_coverage": {
        "resolution_class": "POLICY_DECISION_REQUIRED",
        "automation_allowed": False,
        "why": (
            "GF0017 references specific required character sets, while this project "
            "uses 8105 as baseline and treats outside-8105 rows as Agent scope."
        ),
        "next_action": "define_project_scope_scoring_policy_before_points",
        "safe_agent_action": "keep_not_scorable_and_document_scope_boundary",
    },
    "stroke_shape": {
        "resolution_class": "SOURCE_EXTRACTION_SPEC_REQUIRED",
        "automation_allowed": True,
        "why": (
            "Folded-stroke and stroke-shape sources exist, but row-level normalized "
            "stroke-shape evidence has not been extracted for outside-8105 rows."
        ),
        "next_action": "build_stroke_shape_extraction_spec",
        "safe_agent_action": "design_parser_and_validation_without_scoring",
    },
    "stroke_order": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "Stroke-order sources exist, but row-level joins are pending.",
        "next_action": "build_stroke_order_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
    "component_validity": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "Component sources exist, but row-level component inventories are pending.",
        "next_action": "build_component_inventory_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
    "component_name_validity": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "Component-name authority exists, but names must be normalized per row.",
        "next_action": "build_component_name_validation_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
    "radical_validity": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "Radical sources exist, but numeric legacy radical fields require row-level validation.",
        "next_action": "build_radical_evidence_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
    "independent_character_rule": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "Independent-character evidence must be joined before split/decomposition checks.",
        "next_action": "build_independent_character_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
    "structure_first_decomposition": {
        "resolution_class": "ROW_LEVEL_EXTRACTION_REQUIRED",
        "automation_allowed": True,
        "why": "The 20-point item requires standard-backed decomposition and Agent 13-label localization.",
        "next_action": "build_structure_decomposition_join_runner",
        "safe_agent_action": "materialize evidence_status_without_points",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_or_build_evidence_join() -> dict[str, Any]:
    if EVIDENCE_JOIN.exists():
        return load_json(EVIDENCE_JOIN)

    from scripts.run_full_catalog_agent_mapping_evidence_join import build_evidence_join

    return build_evidence_join()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_path_list(item_design: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for kind in ["controlling_sources", "supporting_sources"]:
        for source in item_design.get(kind, []):
            sources.append(
                {
                    "kind": kind,
                    "relative_path": source["relative_path"],
                    "exists": source["exists"],
                    "grade_status": source["grade_status"],
                    "line_count": source.get("line_count"),
                }
            )
    return sources


def build_resolution_items(join_design: dict[str, Any], evidence_join: dict[str, Any]) -> list[dict[str, Any]]:
    item_counts = evidence_join["summary"]["item_evidence_counts"]
    designs = {item["item"]: item for item in join_design["gf0017_item_join_designs"]}
    items: list[dict[str, Any]] = []
    for item_name, rule in RESOLUTION_RULES.items():
        design = designs[item_name]
        evidence_counts = item_counts[item_name]
        blocked_rows = sum(evidence_counts.values())
        items.append(
            {
                "item": item_name,
                "points": design["points"],
                "current_source_status": design["current_source_status"],
                "evidence_counts": evidence_counts,
                "blocked_rows": blocked_rows,
                "resolution_class": rule["resolution_class"],
                "automation_allowed": rule["automation_allowed"],
                "why": rule["why"],
                "next_action": rule["next_action"],
                "safe_agent_action": rule["safe_agent_action"],
                "source_paths": source_path_list(design),
                "score_allowed_after_this_plan": False,
            }
        )
    return items


def build_work_packages(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    automatic_items = [
        item["item"]
        for item in items
        if item["automation_allowed"]
    ]
    policy_items = [
        item["item"]
        for item in items
        if not item["automation_allowed"]
    ]
    return [
        {
            "id": "SRP1_policy_scope_boundary",
            "items": policy_items,
            "automation_allowed": False,
            "purpose": "Resolve scoring policy for source gaps that cannot be treated as automatic passes.",
            "output": "human-reviewed scope and scoring boundary decision",
            "blocks_formal_scoring": True,
        },
        {
            "id": "SRP2_row_level_extraction_specs",
            "items": automatic_items,
            "automation_allowed": True,
            "purpose": "Create read-only extraction specs for row-level evidence joins.",
            "output": "parser/join specifications and validation fixtures",
            "blocks_formal_scoring": True,
        },
        {
            "id": "SRP3_evidence_join_runners",
            "items": automatic_items,
            "automation_allowed": True,
            "purpose": "Materialize source-backed evidence status rows without assigning points.",
            "output": "row-level evidence tables with source anchors",
            "blocks_formal_scoring": True,
        },
        {
            "id": "SRP4_scoring_gate_review",
            "items": [item["item"] for item in items],
            "automation_allowed": False,
            "purpose": "Review whether enough row-level evidence exists to authorize formal GF0017 scoring.",
            "output": "human authorization or blocker report",
            "blocks_formal_scoring": True,
        },
    ]


def build_agent_model_stage() -> dict[str, Any]:
    return {
        "stage_id": "source_resolution",
        "inputs": [
            str(EVIDENCE_JOIN),
            str(JOIN_DESIGN),
            str(SOURCE_MAPPING),
        ],
        "outputs": [
            str(DEFAULT_JSON_OUTPUT),
            str(DEFAULT_MARKDOWN_OUTPUT),
        ],
        "invariants": [
            "unicode_identity_is_preserved",
            "national_standard_and_agent_standard_are_distinct",
            "source_gap_is_not_success",
            "row_level_pending_evidence_is_not_a_score",
            "cnbe_rows_are_not_modified",
            "database_is_not_rebuilt",
        ],
        "automatic_until": "row_level_extraction_specs",
        "human_decision_required_for": [
            "character_set_coverage_scoring_policy",
            "formal_gf0017_scoring_authorization",
            "cnbe_row_write_authorization",
            "database_rebuild_authorization",
        ],
    }


def build_source_resolution_plan() -> dict[str, Any]:
    evidence_join = load_or_build_evidence_join()
    join_design = load_json(JOIN_DESIGN)
    source_mapping = load_json(SOURCE_MAPPING)
    items = build_resolution_items(join_design, evidence_join)
    class_counts = Counter(item["resolution_class"] for item in items)
    automated_items = [item["item"] for item in items if item["automation_allowed"]]
    policy_items = [item["item"] for item in items if not item["automation_allowed"]]
    blocked_rows_by_item = {
        item["item"]: item["blocked_rows"]
        for item in items
    }
    status = (
        "PASS_SOURCE_RESOLUTION_PLAN_READY"
        if evidence_join["overall_status"] == "PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED"
        and evidence_join["summary"]["outside_8105_rows"] == EXPECTED_OUTSIDE_8105_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_source_resolution_plan",
        "overall_status": status,
        "next_workflow_status": "ROW_LEVEL_EXTRACTION_SPECS_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": evidence_join["summary"]["outside_8105_rows"],
            "gf0017_items": len(items),
            "resolution_class_counts": dict(sorted(class_counts.items())),
            "automated_resolution_items": automated_items,
            "policy_decision_items": policy_items,
            "blocked_rows_by_item": blocked_rows_by_item,
            "source_mapping_status": source_mapping["overall_status"],
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
        },
        "resolution_items": items,
        "work_packages": build_work_packages(items),
        "agent_model_stage": build_agent_model_stage(),
        "decision": {
            "may_start_row_level_extraction_specs": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "requires_human_policy_decision_before_scoring": True,
            "reason": (
                "Source-resolution planning is ready. The Agent may continue with read-only "
                "row-level extraction specs, but formal scoring remains blocked by scope policy "
                "and unresolved row-level evidence."
            ),
        },
        "next_artifacts": [
            "scripts/design_full_catalog_row_level_extraction_specs.py",
            "reports/full_catalog_row_level_extraction_specs.json",
            "reports/FULL_CATALOG_ROW_LEVEL_EXTRACTION_SPECS.md",
            "docs/CNBE_HANZI_STRUCTURE_AGENT_MODEL.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Source Resolution Plan",
        "",
        "## Purpose",
        "",
        "This report plans how to resolve source gaps and row-level evidence",
        "pending statuses for the 89,581 outside-8105 Agent-standard mapping",
        "candidates.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- GF0017 items: `{report['summary']['gf0017_items']}`",
        f"- Automated resolution items: `{len(report['summary']['automated_resolution_items'])}`",
        f"- Policy decision items: `{len(report['summary']['policy_decision_items'])}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Resolution Classes",
        "",
    ]
    for key, value in report["summary"]["resolution_class_counts"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## GF0017 Item Plan", ""])
    for item in report["resolution_items"]:
        lines.append(
            f"- `{item['item']}` ({item['points']} pts): "
            f"`{item['resolution_class']}`; rows={item['blocked_rows']}; "
            f"next=`{item['next_action']}`"
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
            "## Agent Model Stage",
            "",
            f"- Stage id: `{report['agent_model_stage']['stage_id']}`",
            f"- Automatic until: `{report['agent_model_stage']['automatic_until']}`",
            "- Invariants:",
        ]
    )
    for invariant in report["agent_model_stage"]["invariants"]:
        lines.append(f"  - `{invariant}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is a read-only row-level",
            "extraction-spec design. Formal scoring, database reconstruction, and",
            "CNBE row writes remain blocked.",
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
    report = build_source_resolution_plan()
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
