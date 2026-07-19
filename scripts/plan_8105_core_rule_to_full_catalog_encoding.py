#!/usr/bin/env python3
"""Plan the 8105-core rule path for full-catalog CNBE encoding.

This is a read-only planning gate. It makes the 8,105-row 通用规范汉字表 core
the national-standard baseline, defines how outside-8105 rows may be filled as
Agent-standard candidates, and blocks CNBE row writes, database rebuilds, and
full-catalog scoring until evidence gates pass.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

UNIFIED_AUDIT = Path("reports/unified_hanzi_evidence_index_audit.json")
GF0017_SCORING = Path("reports/unified_hanzi_gf0017_scoring_from_index.json")
SOURCE_REPAIR_PLAN = Path("reports/gf0017_source_evidence_repair_plan_from_index.json")
STRUCTURE_REPAIR = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")
ZDIC_VALIDATION = Path("reports/zdic_enhanced_agent_review_packet_validation.json")

DEFAULT_JSON_OUTPUT = Path("reports/8105_core_rule_to_full_catalog_encoding_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN.md")

TOTAL_ROWS = 97_686
CORE_8105_ROWS = 8_105
OUTSIDE_8105_ROWS = 89_581

GF0017_ITEMS = [
    {"item": "character_set_coverage", "points": 3, "required_evidence": "8105 scope decision"},
    {"item": "stroke_shape", "points": 3, "required_evidence": "GF/GB stroke-shape evidence"},
    {"item": "stroke_order", "points": 3, "required_evidence": "通用规范汉字笔顺规范 evidence"},
    {"item": "component_validity", "points": 3, "required_evidence": "现代常用字部件规范 evidence"},
    {"item": "component_name_validity", "points": 8, "required_evidence": "部件及部件名称规范 evidence"},
    {"item": "radical_validity", "points": 3, "required_evidence": "汉字部首表 evidence"},
    {"item": "independent_character_rule", "points": 7, "required_evidence": "现代常用独体字规范 evidence"},
    {"item": "structure_first_decomposition", "points": 20, "required_evidence": "结构类型 and decomposition evidence"},
]

ALLOWED_STRUCTURE_LABELS = [
    "独体字",
    "上下",
    "上中下",
    "左右",
    "左中右",
    "左上包",
    "右上包",
    "左三包",
    "左下包",
    "上三包",
    "下三包",
    "全包围",
    "镶嵌",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_plan() -> dict[str, Any]:
    unified_audit = load_json(UNIFIED_AUDIT)
    gf0017_scoring = load_json(GF0017_SCORING)
    source_repair_plan = load_json(SOURCE_REPAIR_PLAN)
    structure_repair = load_json(STRUCTURE_REPAIR)
    zdic_validation = load_json(ZDIC_VALIDATION)

    catalog_counts = unified_audit["summary"]["catalog_scope_counts"]
    structure_summary = structure_repair["summary"]
    checks = {
        "unified_index_audited": unified_audit["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_AUDITED",
        "catalog_total_matches": unified_audit["summary"]["total_entries"] == TOTAL_ROWS,
        "core_8105_count_matches": catalog_counts["8105_core"] == CORE_8105_ROWS,
        "outside_8105_count_matches": catalog_counts["outside_8105_agent_candidate"] == OUTSIDE_8105_ROWS,
        "formal_scoring_still_blocked": gf0017_scoring["summary"]["rows_fully_scored"] == 0,
        "source_repair_plan_ready": source_repair_plan["overall_status"] == "PASS_GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_READY",
        "structure_repair_materialized_no_scoring": structure_repair["overall_status"]
        == "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED"
        and structure_summary["score_values_assigned"] == 0
        and structure_summary["final_structure_labels_emitted"] == 0,
        "zdic_validated_as_cross_reference_only": zdic_validation["overall_status"]
        == "PASS_ZDIC_ENHANCED_AGENT_REVIEW_PACKET_VALIDATED"
        and zdic_validation["decision"]["may_promote_zdic_to_national_standard"] is False,
        "cnbe_writes_blocked": unified_audit["summary"]["cnbe_row_write_allowed"] is False
        and structure_summary["cnbe_row_write_allowed"] is False,
        "database_rebuild_blocked": unified_audit["summary"]["database_rebuild_allowed"] is False
        and structure_summary["database_rebuild_allowed"] is False,
    }
    status = "PASS_8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN_READY" if all(checks.values()) else "BLOCKED"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_8105_core_rule_to_full_catalog_encoding_plan",
        "overall_status": status,
        "next_workflow_status": "READY_FOR_300_CHARACTER_PILOT_PLAN_NO_ENCODING_WRITES",
        "purpose": (
            "Freeze 8105 as the national-standard core and define how the full "
            "97,686-row catalog can be filled through standard-aligned and "
            "Agent-standard evidence gates without repeating AI hallucination."
        ),
        "core_position": {
            "core_resource": "通用规范汉字表 8105",
            "core_rows": CORE_8105_ROWS,
            "status": "national_standard_core",
            "rule": (
                "8105 is the controlling baseline for national-standard claims. "
                "Outside-8105 rows may align to 8105-derived project rules only "
                "as Agent-standard candidates."
            ),
        },
        "catalog_scope": {
            "total_rows": TOTAL_ROWS,
            "core_8105_rows": CORE_8105_ROWS,
            "outside_8105_rows": OUTSIDE_8105_ROWS,
            "outside_8105_status": "agent_standard_candidate_not_national_standard",
        },
        "evidence_layers": {
            "national_standard": {
                "priority": 1,
                "allowed_sources": [
                    "通用规范汉字表",
                    "GF/GG/GB 国家语言文字规范",
                    "structured 8105 knowledge derived from local standard assets",
                ],
                "allowed_use": "direct or standard-derived evidence after row-level validation",
                "forbidden_use": "none; this is the only layer for national-standard claims",
            },
            "standard_aligned": {
                "priority": 2,
                "allowed_sources": [
                    "8105-learned rule patterns",
                    "辞海",
                    "康熙字典",
                    "中华大字典",
                    "汉字源流大典",
                    "licensed dictionary context index",
                ],
                "allowed_use": "project-level evidence support and human review after standard alignment",
                "forbidden_use": "direct national-standard authority or automatic GF0017 scoring",
            },
            "cross_reference_only": {
                "priority": 3,
                "allowed_sources": ["ZDIC", "offline Chinese Wikipedia", "Unihan cross-reference data"],
                "allowed_use": "review navigation, source discovery, semantic disambiguation",
                "forbidden_use": "final labels, GF0017 points, CNBE row writes, database reconstruction",
            },
        },
        "frozen_rule_core_fields": [
            "unicode_identity",
            "target_scope_membership",
            "stroke_shape",
            "stroke_order",
            "stroke_count",
            "component_validity",
            "component_name_validity",
            "radical_validity",
            "side_component_or偏旁",
            "independent_character_rule",
            "allowed_structure_label",
            "structure_first_decomposition",
            "source_grade",
            "gf0017_item_status",
        ],
        "allowed_structure_labels": ALLOWED_STRUCTURE_LABELS,
        "gf0017_model": {
            "total_points": 50,
            "items": GF0017_ITEMS,
            "current_policy": (
                "Do not assign formal full-row scores until every item has "
                "validated source evidence. Existing partial character-set "
                "coverage points do not authorize final labels or CNBE writes."
            ),
        },
        "outside_8105_fill_strategy": [
            {
                "stage": "unicode_identity",
                "action": "confirm literal character, Unicode scalar, normalization, and scope",
                "stop_condition": "ambiguous identity or row drift",
            },
            {
                "stage": "8105_rule_alignment",
                "action": "compare structure, radical, stroke, and component patterns against frozen 8105 rules",
                "stop_condition": "no 8105 support examples or conflicting rule family",
            },
            {
                "stage": "dictionary_origin_support",
                "action": "attach Cihai, Kangxi, Zhonghua Dazidian, and Yuanliu context when available",
                "stop_condition": "dictionary conflict or no usable source context",
            },
            {
                "stage": "online_cross_reference_navigation",
                "action": "use ZDIC/Wiki only for reviewer navigation and gap discovery",
                "stop_condition": "attempted promotion to national-standard evidence",
            },
            {
                "stage": "agent_standard_candidate",
                "action": "emit review candidate metadata only after all no-write gates pass",
                "stop_condition": "attempted final label, score, CNBE row, database, or release claim",
            },
        ],
        "pilot_design": {
            "recommended_size": 300,
            "strata": [
                {
                    "name": "8105_core_control",
                    "rows": 100,
                    "purpose": "prove national-standard core evidence and GF0017 item joins",
                    "expected_output": "evidence status and review packet, not rewritten CNBE rows",
                },
                {
                    "name": "outside_8105_strong_dictionary_context",
                    "rows": 100,
                    "purpose": "test 8105-aligned rule transfer with strong dictionary/origin support",
                    "expected_output": "Agent-standard candidates requiring human review",
                },
                {
                    "name": "outside_8105_extension_or_gap",
                    "rows": 100,
                    "purpose": "stress-test gaps, extension characters, ZDIC navigation, and stop gates",
                    "expected_output": "review queues and blockers, not filled values",
                },
            ],
            "sampling_rule": "deterministic by Unicode, catalog scope, evidence status, and blocker class",
            "write_policy": "read_only_reports_only",
        },
        "implementation_sequence": [
            "create 8105 frozen rule-core manifest",
            "audit 8105 item-level evidence joins for the 8 GF0017 items",
            "design deterministic 300-character pilot sample",
            "run pilot evidence join without scores or CNBE writes",
            "produce human review packet with blank final fields",
            "merge reviewed evidence only after explicit authorization and audit",
            "then consider formal scoring and CNBE32/64/128 candidate mapping",
        ],
        "cnbe_layer_policy": {
            "cnbe32": "compact carrier only after evidence gates pass; never overrides Hanzi evidence",
            "cnbe64": "extended archive for stroke sequence, component tree, and source anchors",
            "cnbe128": "research archive for multiple evidence witnesses, confidence, and review history",
        },
        "stop_gates": [
            "do not generate final structure labels from visual intuition",
            "do not assign GF0017 scores from cross-reference-only evidence",
            "do not write CNBE rows before source-evidence merge and audit",
            "do not rebuild SQLite databases in this planning phase",
            "do not duplicate the 97,686-row catalog into another XLSX/database",
            "do not label outside-8105 rows as national-standard outputs",
        ],
        "current_blockers": {
            "formal_full_catalog_gf0017_scoring": "blocked until item-level source evidence is complete",
            "structure_first_decomposition": "highest-priority repair item",
            "8105_structure_join": f"{structure_summary['core_8105_standard_join_required_rows']} core rows require standard-derived structure/decomposition join",
            "outside_8105_agent_queue": f"{structure_summary['source_grade_counts']['agent_standard_candidate_not_national_standard']} rows currently agent-standard queue only",
            "source_gap_rows": structure_summary["source_gap_rows"],
        },
        "checks": checks,
        "decision": {
            "may_create_300_character_pilot_plan": status.startswith("PASS"),
            "may_start_full_catalog_encoding": False,
            "may_start_formal_gf0017_scoring": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The project is ready to plan a bounded 300-character pilot "
                "around the frozen 8105 core. It is not ready for full-catalog "
                "encoding writes or database reconstruction."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Core Rule To Full Catalog Encoding Plan",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total catalog rows: {report['catalog_scope']['total_rows']}",
        f"- 8105 national-standard core rows: {report['catalog_scope']['core_8105_rows']}",
        f"- Outside-8105 Agent-standard candidates: {report['catalog_scope']['outside_8105_rows']}",
        f"- May create 300-character pilot plan: `{report['decision']['may_create_300_character_pilot_plan']}`",
        f"- May start full-catalog encoding: `{report['decision']['may_start_full_catalog_encoding']}`",
        f"- May write CNBE rows: `{report['decision']['may_write_cnbe_rows']}`",
        f"- May rebuild database: `{report['decision']['may_rebuild_database']}`",
        "",
        "## Core Rule",
        "",
        report["core_position"]["rule"],
        "",
        "## Evidence Layers",
        "",
        "| Layer | Priority | Allowed Use | Forbidden Use |",
        "|---|---:|---|---|",
    ]
    for name, layer in report["evidence_layers"].items():
        lines.append(
            f"| `{name}` | {layer['priority']} | {layer['allowed_use']} | {layer['forbidden_use']} |"
        )

    lines.extend(
        [
            "",
            "## GF0017 Model",
            "",
            "| Item | Points | Required Evidence |",
            "|---|---:|---|",
        ]
    )
    for item in report["gf0017_model"]["items"]:
        lines.append(f"| `{item['item']}` | {item['points']} | {item['required_evidence']} |")

    lines.extend(
        [
            "",
            "## Pilot Design",
            "",
            "| Stratum | Rows | Purpose | Expected Output |",
            "|---|---:|---|---|",
        ]
    )
    for stratum in report["pilot_design"]["strata"]:
        lines.append(
            f"| `{stratum['name']}` | {stratum['rows']} | {stratum['purpose']} | {stratum['expected_output']} |"
        )

    lines.extend(
        [
            "",
            "## Stop Gates",
            "",
        ]
    )
    for gate in report["stop_gates"]:
        lines.append(f"- {gate}")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"core_8105_rows={report['catalog_scope']['core_8105_rows']}")
    print(f"outside_8105_rows={report['catalog_scope']['outside_8105_rows']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
