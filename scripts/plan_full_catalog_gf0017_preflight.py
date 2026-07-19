#!/usr/bin/env python3
"""Plan the full-catalog GF0017 preflight without scoring rows.

The v4_fixed workbook has passed schema, sample, and Unicode identity gates.
This script maps its 17 columns to the GF0017 50-point scoring model and the
CNBE Agent gates, then records why batch scoring and database reconstruction
remain blocked until source-evidence assets are reconciled.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_REPORT = Path("reports/full_catalog_excel_schema_comparison.json")
SAMPLE_REPORT = Path("reports/full_catalog_v4_fixed_sample_rows.json")
UNICODE_IDENTITY_REPORT = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
AGENT_RUNTIME_REPORT = Path("reports/cnbe_agent_runtime_logic_verification.json")
GF0017_MODEL = Path("evidence/gf0017/gf0017_cnbe50_scoring_model.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_preflight_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_PREFLIGHT_PLAN.md")

WORKBOOK_PATH = "data/CNBE_编码目录_修复版_v4_fixed.xlsx"
WORKBOOK_SHEET = "CNBE完整编码表v4_fixed"
EXPECTED_HEADERS = [
    "序号",
    "汉字",
    "Unicode",
    "CNBE(Hex)",
    "CNBE(Dec)",
    "CNBE(Bin)",
    "部首区",
    "笔画数",
    "结构区(v4)",
    "结构名称(v4)",
    "字库索引",
    "扩展区",
    "是否现代",
    "Space_Label",
    "Category_Label",
    "Time_Label",
    "备注(v3原结构)",
]

SOURCE_GRADES = [
    "direct_standard",
    "standard_derived",
    "cross_reference",
    "referenced_not_direct",
    "unresolved",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_v4_fixed_schema(schema: dict[str, Any]) -> dict[str, Any]:
    for workbook in schema["workbooks"]:
        if workbook["path"] == WORKBOOK_PATH:
            for sheet in workbook["sheets"]:
                if sheet["name"] == WORKBOOK_SHEET:
                    return {
                        "workbook": workbook,
                        "sheet": sheet,
                        "headers": sheet["header"]["headers"],
                        "row_count": sheet["dimension"]["row_count"],
                        "column_count": sheet["dimension"]["column_count"],
                        "sha256": workbook["sha256"],
                    }
    raise ValueError(f"missing schema for {WORKBOOK_PATH}::{WORKBOOK_SHEET}")


def workbook_field_map() -> dict[str, dict[str, Any]]:
    return {
        "序号": {
            "agent_role": "source_row_sequence",
            "gf0017_use": ["character_set_coverage"],
            "evidence_role": "row ordering and checkpoint offset",
            "authority": "workbook_metadata_not_standard",
        },
        "汉字": {
            "agent_role": "literal_character",
            "gf0017_use": ["character_set_coverage"],
            "evidence_role": "Unicode identity input",
            "authority": "identity_candidate",
        },
        "Unicode": {
            "agent_role": "unicode_codepoint",
            "gf0017_use": ["character_set_coverage"],
            "evidence_role": "Unicode identity input",
            "authority": "identity_candidate",
        },
        "CNBE(Hex)": {
            "agent_role": "cnbe32_carrier_hex",
            "gf0017_use": [],
            "evidence_role": "carrier consistency only",
            "authority": "legacy_cnbe_candidate",
        },
        "CNBE(Dec)": {
            "agent_role": "cnbe32_carrier_decimal",
            "gf0017_use": [],
            "evidence_role": "carrier consistency only",
            "authority": "legacy_cnbe_candidate",
        },
        "CNBE(Bin)": {
            "agent_role": "cnbe32_carrier_binary",
            "gf0017_use": [],
            "evidence_role": "carrier consistency only",
            "authority": "legacy_cnbe_candidate",
        },
        "部首区": {
            "agent_role": "legacy_radical_code",
            "gf0017_use": ["radical_validity"],
            "evidence_role": "candidate radical-code field requiring GG0011/radical map validation",
            "authority": "legacy_cnbe_candidate",
        },
        "笔画数": {
            "agent_role": "legacy_stroke_count",
            "gf0017_use": ["stroke_shape", "stroke_order"],
            "evidence_role": "candidate stroke-count field requiring stroke-order evidence",
            "authority": "legacy_cnbe_candidate",
        },
        "结构区(v4)": {
            "agent_role": "legacy_structure_code",
            "gf0017_use": ["structure_first_decomposition", "independent_character_rule"],
            "evidence_role": "candidate structure-code field requiring Agent localization",
            "authority": "legacy_cnbe_candidate",
        },
        "结构名称(v4)": {
            "agent_role": "legacy_structure_name",
            "gf0017_use": ["structure_first_decomposition", "independent_character_rule"],
            "evidence_role": "candidate structure label requiring 13-label normalization",
            "authority": "legacy_cnbe_candidate",
        },
        "字库索引": {
            "agent_role": "legacy_catalog_index",
            "gf0017_use": ["character_set_coverage"],
            "evidence_role": "catalog ordering only",
            "authority": "workbook_metadata_not_standard",
        },
        "扩展区": {
            "agent_role": "legacy_extension_flags",
            "gf0017_use": [],
            "evidence_role": "CNBE32 extension carrier only",
            "authority": "legacy_cnbe_candidate",
        },
        "是否现代": {
            "agent_role": "legacy_modern_flag",
            "gf0017_use": ["character_set_coverage"],
            "evidence_role": "candidate scope flag requiring standard-set evidence",
            "authority": "legacy_cnbe_candidate",
        },
        "Space_Label": {
            "agent_role": "legacy_space_label",
            "gf0017_use": [],
            "evidence_role": "legacy metadata for CNBE64/CNBE128 archive consideration",
            "authority": "legacy_metadata_not_standard",
        },
        "Category_Label": {
            "agent_role": "legacy_category_label",
            "gf0017_use": [],
            "evidence_role": "legacy metadata for CNBE64/CNBE128 archive consideration",
            "authority": "legacy_metadata_not_standard",
        },
        "Time_Label": {
            "agent_role": "legacy_time_label",
            "gf0017_use": [],
            "evidence_role": "legacy metadata for CNBE64/CNBE128 archive consideration",
            "authority": "legacy_metadata_not_standard",
        },
        "备注(v3原结构)": {
            "agent_role": "legacy_v3_structure_note",
            "gf0017_use": ["structure_first_decomposition"],
            "evidence_role": "legacy structure evidence to preserve, not a standard source",
            "authority": "legacy_metadata_not_standard",
        },
    }


def gf0017_item_map(model: dict[str, Any]) -> list[dict[str, Any]]:
    workbook_fields = workbook_field_map()
    fields_by_item: dict[str, list[str]] = {}
    for field, info in workbook_fields.items():
        for item_id in info["gf0017_use"]:
            fields_by_item.setdefault(item_id, []).append(field)

    source_requirements = {
        "character_set_coverage": [
            "GF0017 clause 5.1.1",
            "confirmed required-set source or project-approved 8105 baseline",
        ],
        "stroke_shape": [
            "GF0017 clause 5.1.2",
            "stroke-shape classification source",
            "GB 13000.1 fold-stroke evidence where applicable",
        ],
        "stroke_order": [
            "GF0017 clause 5.1.3",
            "GF0031/GF3002 stroke-order source",
        ],
        "component_validity": [
            "GF0014/GF3001 component and decomposition evidence",
        ],
        "component_name_validity": [
            "GF0014 component naming evidence",
        ],
        "radical_validity": [
            "GG0011 radical evidence",
            "validated radical-code map",
        ],
        "independent_character_rule": [
            "GF0013 independent-character evidence",
            "GF0014 decomposition compatibility",
        ],
        "structure_first_decomposition": [
            "GF0014 structure/decomposition evidence",
            "Agent 13-label structure normalization",
        ],
    }

    result: list[dict[str, Any]] = []
    for item in model["score_items"]:
        item_id = item["id"]
        fields = fields_by_item.get(item_id, [])
        result.append(
            {
                "id": item_id,
                "points": item["points"],
                "gf0017_clause": item["gf0017_clause"],
                "workbook_fields": fields,
                "workbook_support_level": "identity_or_candidate" if fields else "none",
                "source_requirements": source_requirements[item_id],
                "preflight_status": "SOURCE_EVIDENCE_REQUIRED",
                "blocking_rule": (
                    "Do not calculate final GF0017 score until every required source requirement "
                    "has a source grade and unresolved requirements are isolated."
                ),
            }
        )
    return result


def build_checkpoint_plan(identity_summary: dict[str, Any]) -> dict[str, Any]:
    data_rows = identity_summary["data_rows"]
    return {
        "batch_id": "full-catalog-v4-fixed-gf0017-preflight",
        "mode": "plan_only_no_row_scoring",
        "source_workbook": WORKBOOK_PATH,
        "row_count": data_rows,
        "start_offset": 0,
        "end_offset": data_rows - 1,
        "checkpoint_file": "reports/full_catalog_gf0017_preflight_checkpoint.json",
        "blocker_file": "reports/full_catalog_gf0017_preflight_blockers.json",
        "resume_rule": "restart from last_verified_offset + 1 after blocker evidence is resolved",
        "stop_conditions": [
            "Unicode identity mismatch",
            "source grade unresolved for a required scoring item",
            "legacy structure label without Agent localization",
            "Agent standard mapping mislabeled as national standard",
            "database rewrite attempted before explicit authorization",
        ],
    }


def build_plan() -> dict[str, Any]:
    schema = load_json(SCHEMA_REPORT)
    sample = load_json(SAMPLE_REPORT)
    identity = load_json(UNICODE_IDENTITY_REPORT)
    runtime = load_json(AGENT_RUNTIME_REPORT)
    model = load_json(GF0017_MODEL)
    inventory = load_json(KNOWLEDGE_INVENTORY)

    v4_schema = find_v4_fixed_schema(schema)
    headers_match = v4_schema["headers"] == EXPECTED_HEADERS
    pre_gates_pass = (
        schema["summary"]["status"] == "PASS"
        and sample["summary"]["status"] == "PASS"
        and identity["summary"]["status"] == "PASS"
        and runtime["overall_status"] == "PASS"
    )
    knowledge_no_go = inventory["gates"]["encoding_generation_gate"] == "NO_GO"
    knowledge_review_required = inventory["gates"]["encoding_generation_gate"] == "REVIEW_REQUIRED"
    unresolved_blockers = [
        item for item in inventory.get("action_items", []) if item.get("severity") == "BLOCKER"
    ]

    item_map = gf0017_item_map(model)
    total_points = sum(item["points"] for item in item_map)
    source_grading_contract = {
        "allowed_grades": SOURCE_GRADES,
        "required_behavior": {
            "direct_standard": "may support national-standard evidence when the source is the scoring authority",
            "standard_derived": "may support scoring when derivation is reproducible",
            "cross_reference": "review support only unless promoted by a separate gate",
            "referenced_not_direct": "must be reported as SOURCE_GAP",
            "unresolved": "must stop or isolate the affected row/item before batch scoring",
        },
    }

    batch_scoring_allowed = False
    next_status = "PREFLIGHT_PLAN_READY_BATCH_SCORING_BLOCKED"
    if not pre_gates_pass or not headers_match:
        next_status = "PREFLIGHT_PLAN_BLOCKED_BY_PRE_GATES"
    elif knowledge_no_go:
        next_status = "PREFLIGHT_PLAN_READY_SOURCE_ASSETS_BLOCK_BATCH_SCORING"
    elif knowledge_review_required:
        next_status = "PREFLIGHT_PLAN_READY_SOURCE_ASSETS_REQUIRE_REVIEW"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_preflight_plan",
        "source_workbook": WORKBOOK_PATH,
        "source_sheet": WORKBOOK_SHEET,
        "overall_status": "PASS" if pre_gates_pass and headers_match else "FAIL",
        "next_workflow_status": next_status,
        "pre_gates": {
            "schema_status": schema["summary"]["status"],
            "sample_status": sample["summary"]["status"],
            "unicode_identity_status": identity["summary"]["status"],
            "agent_runtime_status": runtime["overall_status"],
            "headers_match_expected": headers_match,
        },
        "workbook": {
            "sha256": v4_schema["sha256"],
            "worksheet_rows": v4_schema["row_count"],
            "data_rows": identity["summary"]["data_rows"],
            "column_count": v4_schema["column_count"],
            "headers": v4_schema["headers"],
        },
        "field_mapping": workbook_field_map(),
        "gf0017_item_mapping": item_map,
        "gf0017_total_points": total_points,
        "source_grading_contract": source_grading_contract,
        "checkpoint_plan": build_checkpoint_plan(identity["summary"]),
        "known_blockers": unresolved_blockers,
        "decision": {
            "may_start_source_evidence_mapping": pre_gates_pass and headers_match,
            "may_start_batch_gf0017_scoring": batch_scoring_allowed,
            "may_rebuild_database": False,
            "may_modify_workbook": False,
            "may_publish_release": False,
            "reason": (
                "The workbook can enter source-evidence mapping, but final GF0017 scoring is blocked "
                "until required source grades and review-required asset notes are resolved or accepted."
            ),
        },
        "next_artifacts": [
            "reports/full_catalog_gf0017_source_mapping.json",
            "reports/FULL_CATALOG_GF0017_SOURCE_MAPPING.md",
            "scripts/map_full_catalog_gf0017_sources.py",
        ],
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Preflight Plan",
        "",
        "## Purpose",
        "",
        "This plan maps the v4_fixed full-catalog workbook into the CNBE Agent",
        "GF0017 preflight workflow. It is a planning and gate artifact only.",
        "",
        "It does not score rows, rewrite the workbook, rebuild the SQLite",
        "database, change CNBE32 values, create tags, publish releases, or upload",
        "to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{plan['overall_status']}`",
        f"- Next workflow status: `{plan['next_workflow_status']}`",
        f"- Source workbook: `{plan['source_workbook']}`",
        f"- Data rows: `{plan['workbook']['data_rows']}`",
        f"- Columns: `{plan['workbook']['column_count']}`",
        f"- GF0017 total points: `{plan['gf0017_total_points']}`",
        f"- May start source evidence mapping: `{plan['decision']['may_start_source_evidence_mapping']}`",
        f"- May start batch GF0017 scoring: `{plan['decision']['may_start_batch_gf0017_scoring']}`",
        f"- May rebuild database: `{plan['decision']['may_rebuild_database']}`",
        "",
        "## Pre-Gates",
        "",
        "| Gate | Status |",
        "|---|:---:|",
    ]
    for key, value in plan["pre_gates"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Workbook Field Mapping",
            "",
            "| Column | Agent role | GF0017 use | Authority boundary |",
            "|---|---|---|---|",
        ]
    )
    for field, info in plan["field_mapping"].items():
        gf_use = ", ".join(info["gf0017_use"]) if info["gf0017_use"] else "not a scoring field"
        lines.append(f"| `{field}` | {info['agent_role']} | {gf_use} | {info['authority']} |")

    lines.extend(
        [
            "",
            "## GF0017 Item Mapping",
            "",
            "| Item | Points | Workbook fields | Preflight status |",
            "|---|---:|---|---|",
        ]
    )
    for item in plan["gf0017_item_mapping"]:
        fields = ", ".join(f"`{field}`" for field in item["workbook_fields"]) or "none"
        lines.append(f"| `{item['id']}` | {item['points']} | {fields} | {item['preflight_status']} |")

    lines.extend(
        [
            "",
            "## Known Blockers",
            "",
        ]
    )
    if plan["known_blockers"]:
        for item in plan["known_blockers"]:
            lines.append(f"- `{item['asset']}`: {item['issue']} -> {item['next_step']}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Stop And Resume",
            "",
            f"- Batch id: `{plan['checkpoint_plan']['batch_id']}`",
            f"- Start offset: `{plan['checkpoint_plan']['start_offset']}`",
            f"- End offset: `{plan['checkpoint_plan']['end_offset']}`",
            f"- Checkpoint file: `{plan['checkpoint_plan']['checkpoint_file']}`",
            f"- Resume rule: {plan['checkpoint_plan']['resume_rule']}",
            "",
            "Stop conditions:",
            "",
        ]
    )
    for condition in plan["checkpoint_plan"]["stop_conditions"]:
        lines.append(f"- {condition}")

    lines.extend(
        [
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in plan["next_artifacts"]:
        lines.append(f"- `{artifact}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            plan["decision"]["reason"],
            "",
            "The next allowed implementation step is source-evidence mapping.",
            "Batch GF0017 scoring remains blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    plan = build_plan()
    write_json(DEFAULT_JSON_OUTPUT, plan)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(plan))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={plan['overall_status']}")
    print(f"next_workflow_status={plan['next_workflow_status']}")
    if plan["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
