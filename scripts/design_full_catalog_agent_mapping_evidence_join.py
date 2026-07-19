#!/usr/bin/env python3
"""Design row-level evidence joins for outside-8105 Agent mappings.

The output is a read-only implementation design. It defines how future scripts
should join national-standard, standard-derived, and contextual knowledge to
the 89,581 outside-8105 rows. It does not assign GF0017 scores or write CNBE
encoding rows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
MAPPING_PLAN = Path("reports/full_catalog_agent_standard_mapping_plan.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")
JOIN_SCHEMA = Path("reports/full_catalog_gf0017_join_schema.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_agent_mapping_evidence_join_design.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN_DESIGN.md")


JOIN_OUTPUT_TABLES = [
    {
        "name": "unicode_identity",
        "grain": "one row per full-catalog character",
        "primary_key": ["unicode"],
        "required_fields": ["char", "unicode", "codepoint", "worksheet_row", "offset"],
        "authority": "identity_only",
    },
    {
        "name": "scope_membership",
        "grain": "one row per character per scope source",
        "primary_key": ["unicode", "scope_source"],
        "required_fields": ["scope_source", "membership_status", "source_grade", "source_anchor"],
        "authority": "direct_or_project_scope",
    },
    {
        "name": "stroke_evidence",
        "grain": "one row per character per stroke source",
        "primary_key": ["unicode", "stroke_source"],
        "required_fields": ["stroke_count", "stroke_order", "stroke_shape", "source_grade", "source_anchor"],
        "authority": "standard_derived_or_contextual",
    },
    {
        "name": "component_evidence",
        "grain": "one row per character per decomposition source",
        "primary_key": ["unicode", "component_source"],
        "required_fields": ["components", "component_names", "basic_components", "source_grade", "source_anchor"],
        "authority": "standard_derived_or_contextual",
    },
    {
        "name": "radical_evidence",
        "grain": "one row per character per radical source",
        "primary_key": ["unicode", "radical_source"],
        "required_fields": ["radical", "radical_code", "rs_index", "source_grade", "source_anchor"],
        "authority": "direct_standard_or_cross_reference",
    },
    {
        "name": "structure_evidence",
        "grain": "one row per character per structure source",
        "primary_key": ["unicode", "structure_source"],
        "required_fields": ["structure_label", "decomposition", "independent_status", "source_grade", "source_anchor"],
        "authority": "agent_standard_after_validation",
    },
    {
        "name": "gf0017_item_evidence_status",
        "grain": "one row per character per GF0017 item",
        "primary_key": ["unicode", "gf0017_item"],
        "required_fields": ["item_status", "points_possible", "evidence_sources", "blocker_code"],
        "authority": "audit_gate",
    },
]


ITEM_JOIN_RULES = {
    "character_set_coverage": {
        "join_tables": ["unicode_identity", "scope_membership"],
        "join_keys": ["unicode"],
        "source_policy": "Resolve required scope first. 8105 is project baseline; outside-8105 rows stay Agent scope.",
        "required_source_status_before_points": "resolved_scope_policy",
        "blocker_code": "SOURCE_GAP_CHARACTER_SET_COVERAGE",
    },
    "stroke_shape": {
        "join_tables": ["unicode_identity", "stroke_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join folded-stroke and stroke-shape evidence before assigning the 3-point item.",
        "required_source_status_before_points": "row_level_stroke_shape_evidence",
        "blocker_code": "SOURCE_GAP_STROKE_SHAPE",
    },
    "stroke_order": {
        "join_tables": ["unicode_identity", "stroke_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join GF0031/GF3002-derived stroke-order records and compare only after source row is anchored.",
        "required_source_status_before_points": "row_level_stroke_order_evidence",
        "blocker_code": "MISSING_STROKE_ORDER_EVIDENCE",
    },
    "component_validity": {
        "join_tables": ["unicode_identity", "component_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join GF0014/GB13000.1 component evidence; contextual decompositions are review aids.",
        "required_source_status_before_points": "row_level_component_inventory",
        "blocker_code": "MISSING_COMPONENT_EVIDENCE",
    },
    "component_name_validity": {
        "join_tables": ["unicode_identity", "component_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Validate component names against GF0014-derived component names before scoring.",
        "required_source_status_before_points": "row_level_component_name_inventory",
        "blocker_code": "MISSING_COMPONENT_NAME_EVIDENCE",
    },
    "radical_validity": {
        "join_tables": ["unicode_identity", "radical_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join GG0011/Kangxi/RSIndex evidence and validate numeric radical-code mapping separately.",
        "required_source_status_before_points": "row_level_radical_evidence",
        "blocker_code": "MISSING_RADICAL_EVIDENCE",
    },
    "independent_character_rule": {
        "join_tables": ["unicode_identity", "component_evidence", "structure_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join GF0013/GF0014 evidence so independent characters are not split incorrectly.",
        "required_source_status_before_points": "row_level_independent_character_evidence",
        "blocker_code": "MISSING_INDEPENDENT_CHARACTER_EVIDENCE",
    },
    "structure_first_decomposition": {
        "join_tables": ["unicode_identity", "component_evidence", "structure_evidence"],
        "join_keys": ["unicode"],
        "source_policy": "Join Agent 13-label localization with standard-backed decomposition evidence.",
        "required_source_status_before_points": "row_level_structure_decomposition_evidence",
        "blocker_code": "MISSING_STRUCTURE_DECOMPOSITION_EVIDENCE",
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


def source_exists(relative_path: str) -> bool:
    return (RESEARCH_ROOT / relative_path).exists() or Path(relative_path).exists()


def source_record(source: dict[str, Any]) -> dict[str, Any]:
    relative_path = source.get("relative_path", "")
    exists_now = source_exists(relative_path)
    return {
        "relative_path": relative_path,
        "exists": bool(source.get("exists", False) or exists_now),
        "grade_status": source.get("grade_status") or source.get("grade") or "unspecified",
        "line_count": source.get("line_count"),
        "sha256": source.get("sha256"),
        "size_bytes": source.get("size_bytes"),
    }


def build_item_designs(source_mapping: dict[str, Any]) -> list[dict[str, Any]]:
    designs: list[dict[str, Any]] = []
    for item in source_mapping["items"]:
        item_id = item["id"]
        rule = ITEM_JOIN_RULES[item_id]
        controlling = [source_record(source) for source in item.get("controlling_sources", [])]
        supporting = [source_record(source) for source in item.get("supporting_sources", [])]
        missing_supporting = [
            source["relative_path"]
            for source in controlling + supporting
            if not source["exists"]
        ]
        designs.append(
            {
                "item": item_id,
                "points": item["points"],
                "current_source_status": item["source_status"],
                "domain": item["domain"],
                "workbook_fields": item.get("workbook_fields", []),
                "join_tables": rule["join_tables"],
                "join_keys": rule["join_keys"],
                "source_policy": rule["source_policy"],
                "required_source_status_before_points": rule["required_source_status_before_points"],
                "blocker_code": rule["blocker_code"],
                "controlling_sources": controlling,
                "supporting_sources": supporting,
                "missing_source_paths": missing_supporting,
                "can_assign_points_now": False,
                "next_action": (
                    "resolve_source_gap_before_scoring"
                    if item["source_status"] == "SOURCE_GAP"
                    else "build_row_level_evidence_join_before_scoring"
                ),
            }
        )
    return designs


def build_checkpoint_contract(mapping_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "batch_id": "full_catalog_agent_mapping_evidence_join_v1",
        "source_plan": str(MAPPING_PLAN),
        "row_count": mapping_plan["summary"]["outside_8105_rows"],
        "resume_key": "unicode",
        "checkpoint_fields": [
            "last_verified_unicode",
            "last_verified_offset",
            "blocker_unicode",
            "blocker_offset",
            "failed_gf0017_item",
            "failed_source_path",
            "next_required_action",
        ],
        "stop_rules": [
            "unicode_identity_gap",
            "source_grade_unresolved",
            "agent_standard_mislabeled_as_national",
            "missing_required_row_level_evidence",
            "attempted_cnbe_row_write",
            "attempted_database_rebuild",
        ],
    }


def build_join_design() -> dict[str, Any]:
    mapping_plan = load_json(MAPPING_PLAN)
    source_mapping = load_json(SOURCE_MAPPING)
    join_schema = load_json(JOIN_SCHEMA)
    item_designs = build_item_designs(source_mapping)
    missing_source_paths = sorted(
        {
            path
            for item in item_designs
            for path in item["missing_source_paths"]
        }
    )
    source_gap_items = [
        item["item"]
        for item in item_designs
        if item["current_source_status"] == "SOURCE_GAP"
    ]
    evidence_required_items = [
        item["item"]
        for item in item_designs
        if item["current_source_status"] == "SOURCE_EVIDENCE_REQUIRED"
    ]
    status = (
        "PASS_EVIDENCE_JOIN_DESIGN_READY"
        if mapping_plan["overall_status"] == "PASS_AGENT_STANDARD_MAPPING_PLAN_READY"
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_agent_mapping_evidence_join_design",
        "overall_status": status,
        "next_workflow_status": "ROW_LEVEL_EVIDENCE_JOIN_IMPLEMENTATION_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "outside_8105_rows": mapping_plan["summary"]["outside_8105_rows"],
            "join_output_tables": len(JOIN_OUTPUT_TABLES),
            "gf0017_items": len(item_designs),
            "source_gap_items": source_gap_items,
            "source_evidence_required_items": evidence_required_items,
            "missing_source_paths": missing_source_paths,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_join_schema_status": join_schema["overall_status"],
        },
        "join_output_tables": JOIN_OUTPUT_TABLES,
        "gf0017_item_join_designs": item_designs,
        "checkpoint_contract": build_checkpoint_contract(mapping_plan),
        "implementation_order": [
            {
                "step": 1,
                "name": "materialize_unicode_identity_view",
                "allowed_now": True,
                "writes_source_assets": False,
            },
            {
                "step": 2,
                "name": "materialize_scope_membership_view",
                "allowed_now": True,
                "writes_source_assets": False,
            },
            {
                "step": 3,
                "name": "materialize_stroke_component_radical_structure_views",
                "allowed_now": True,
                "writes_source_assets": False,
            },
            {
                "step": 4,
                "name": "join_gf0017_item_evidence_status",
                "allowed_now": True,
                "writes_source_assets": False,
            },
            {
                "step": 5,
                "name": "assign_formal_gf0017_scores",
                "allowed_now": False,
                "writes_source_assets": False,
            },
            {
                "step": 6,
                "name": "generate_or_repair_cnbe_rows",
                "allowed_now": False,
                "writes_source_assets": False,
            },
        ],
        "decision": {
            "may_implement_row_level_evidence_join": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "The join design is ready for a read-only implementation pass. "
                "Formal scoring remains blocked until each row receives item-level evidence status."
            ),
        },
        "next_artifacts": [
            "scripts/run_full_catalog_agent_mapping_evidence_join.py",
            "reports/full_catalog_agent_mapping_evidence_join.json",
            "reports/FULL_CATALOG_AGENT_MAPPING_EVIDENCE_JOIN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog Agent Mapping Evidence Join Design",
        "",
        "## Purpose",
        "",
        "This report designs the row-level evidence join needed before the",
        "89,581 outside-8105 rows can be considered for Agent-standard mapping",
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
        f"- Join output tables: `{report['summary']['join_output_tables']}`",
        f"- GF0017 items: `{report['summary']['gf0017_items']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- CNBE row write allowed: `{report['summary']['cnbe_row_write_allowed']}`",
        "",
        "## Join Output Tables",
        "",
    ]
    for table in report["join_output_tables"]:
        lines.append(f"- `{table['name']}`: {table['grain']}")

    lines.extend(["", "## GF0017 Item Join Rules", ""])
    for item in report["gf0017_item_join_designs"]:
        lines.append(
            f"- `{item['item']}` ({item['points']} pts): "
            f"`{item['current_source_status']}` -> `{item['next_action']}`"
        )

    lines.extend(["", "## Implementation Order", ""])
    for step in report["implementation_order"]:
        lines.append(f"- Step {step['step']}: `{step['name']}`; allowed now: `{step['allowed_now']}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed implementation step is a read-only row-level evidence",
            "join runner. Formal scoring, database reconstruction, and CNBE row",
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
    report = build_join_design()
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
