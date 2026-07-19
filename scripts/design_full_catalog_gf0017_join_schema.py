#!/usr/bin/env python3
"""Design the full-catalog GF0017 join schema without scoring rows.

This script creates the contract that a future batch scorer must satisfy when
joining v4_fixed workbook rows with Unicode identity, source evidence, Agent
structure localization, and GF0017 item records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PREFLIGHT_PLAN = Path("reports/full_catalog_gf0017_preflight_plan.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")
UNICODE_IDENTITY = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
AGENT_STANDARD = Path("evidence/agent-standard/cnbe_agent_encoding_standard.json")
LEGACY_LOCALIZATION = Path("evidence/agent-standard/cnbe_legacy_structure_localization.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_join_schema.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_JOIN_SCHEMA.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def workbook_columns(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    columns: list[dict[str, Any]] = []
    for index, header in enumerate(preflight["workbook"]["headers"]):
        info = preflight["field_mapping"][header]
        columns.append(
            {
                "index": index,
                "name": header,
                "agent_role": info["agent_role"],
                "authority": info["authority"],
                "gf0017_use": info["gf0017_use"],
                "required_for_join": header in {"序号", "汉字", "Unicode"},
            }
        )
    return columns


def evidence_tables(source_mapping: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "table_id": "unicode_identity",
            "source": "reports/full_catalog_v4_fixed_unicode_identity.json",
            "join_key": ["char", "unicode"],
            "required_fields": ["row_offset", "worksheet_row", "char", "unicode", "codepoint"],
            "controls": ["Unicode identity gate", "row offset checkpoint"],
            "status_policy": "BLOCKER on mismatch",
        },
        {
            "table_id": "gf0017_source_items",
            "source": "reports/full_catalog_gf0017_source_mapping.json",
            "join_key": ["gf0017_item_id"],
            "required_fields": [
                "id",
                "points",
                "source_status",
                "controlling_sources",
                "workbook_fields",
            ],
            "controls": [item["id"] for item in source_mapping["items"]],
            "status_policy": "SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED must be preserved",
        },
        {
            "table_id": "agent_structure_localization",
            "source": "evidence/agent-standard/cnbe_legacy_structure_localization.json",
            "join_key": ["legacy_structure_label"],
            "required_fields": [
                "legacy_struct_name",
                "legacy_struct_type",
                "agent_structure",
                "agent_struct_type",
                "standard_level",
                "localization_confidence",
            ],
            "controls": ["structure_first_decomposition", "independent_character_rule"],
            "status_policy": "BLOCKER if a legacy label has no Agent localization",
        },
        {
            "table_id": "standard_hanzi_knowledge",
            "source": "future standard-derived evidence extraction",
            "join_key": ["char", "unicode"],
            "required_fields": [
                "stroke_count",
                "stroke_order",
                "stroke_shape_sequence",
                "radical",
                "component_list",
                "component_names",
                "independent_character_status",
                "structure",
                "decomposition_tree",
                "source_references",
                "source_grades",
            ],
            "controls": [
                "stroke_shape",
                "stroke_order",
                "component_validity",
                "component_name_validity",
                "radical_validity",
                "independent_character_rule",
                "structure_first_decomposition",
            ],
            "status_policy": "BLOCKER if required source grade is unresolved",
        },
        {
            "table_id": "cnbe32_carrier_snapshot",
            "source": "v4_fixed workbook columns",
            "join_key": ["char", "unicode"],
            "required_fields": [
                "cnbe_hex",
                "cnbe_dec",
                "cnbe_bin",
                "legacy_radical_code",
                "legacy_stroke_count",
                "legacy_structure_code",
                "legacy_structure_name",
                "legacy_index",
                "legacy_extension_flags",
            ],
            "controls": ["carrier consistency only"],
            "status_policy": "review signal only; cannot prove normative correctness",
        },
    ]


def row_schema(source_mapping: dict[str, Any]) -> dict[str, Any]:
    gf0017_items = [item["id"] for item in source_mapping["items"]]
    return {
        "record_id": "full_catalog_gf0017_join_row_v1",
        "required_top_level_fields": [
            "row_offset",
            "worksheet_row",
            "char",
            "unicode",
            "codepoint",
            "normalization_status",
            "scope_status",
            "workbook_fields",
            "source_evidence",
            "agent_localization",
            "gf0017_items",
            "blockers",
            "checkpoint",
        ],
        "gf0017_item_ids": gf0017_items,
        "gf0017_item_shape": {
            "item_id": "string",
            "points": "integer",
            "source_status": "direct_standard | standard_derived | cross_reference | referenced_not_direct | unresolved | SOURCE_GAP | SOURCE_EVIDENCE_REQUIRED",
            "source_grade": "source-grade label for controlling evidence",
            "score": "null in join-schema phase",
            "status": "null in join-schema phase",
            "evidence_refs": "list of source path/hash/page references",
            "blocker": "null or blocker code",
        },
        "score_policy": {
            "score_values_allowed": False,
            "numeric_score_before_batch_phase": "FORBIDDEN",
            "status_without_source_grade": "FORBIDDEN",
            "source_gap_as_pass": "FORBIDDEN",
        },
    }


def blocker_rules() -> list[dict[str, Any]]:
    return [
        {
            "code": "UNICODE_IDENTITY_MISMATCH",
            "gate": "Unicode identity",
            "action": "stop batch and write checkpoint",
        },
        {
            "code": "SOURCE_GRADE_UNRESOLVED",
            "gate": "Source evidence",
            "action": "stop or isolate affected row/item before scoring",
        },
        {
            "code": "LEGACY_STRUCTURE_NOT_LOCALIZED",
            "gate": "Agent standard localization",
            "action": "stop until legacy label maps to one of the 13 Agent labels",
        },
        {
            "code": "AGENT_STANDARD_MISLABELED_AS_NATIONAL",
            "gate": "Authority boundary",
            "action": "stop and correct standard_level",
        },
        {
            "code": "CNBE32_WRITE_ATTEMPT",
            "gate": "No-write boundary",
            "action": "stop; this phase cannot modify workbook/database/CNBE rows",
        },
        {
            "code": "KNOWLEDGE_ASSET_BLOCKER",
            "gate": "Knowledge inventory",
            "action": "reconcile or explicitly exclude the blocker before batch scoring",
        },
    ]


def build_join_schema() -> dict[str, Any]:
    preflight = load_json(PREFLIGHT_PLAN)
    source_mapping = load_json(SOURCE_MAPPING)
    identity = load_json(UNICODE_IDENTITY)
    agent_standard = load_json(AGENT_STANDARD)
    localization = load_json(LEGACY_LOCALIZATION)

    preconditions_pass = (
        preflight["overall_status"] == "PASS"
        and source_mapping["overall_status"] == "PASS"
        and identity["summary"]["status"] == "PASS"
        and localization["summary"]["all_legacy_labels_mapped"] is True
    )
    schema = {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_join_schema_design",
        "source_workbook": preflight["source_workbook"],
        "source_sheet": preflight["source_sheet"],
        "overall_status": "PASS" if preconditions_pass else "FAIL",
        "next_workflow_status": "JOIN_SCHEMA_READY_BLOCKER_RECONCILIATION_REQUIRED",
        "authority_boundary": {
            "does_not_score_rows": True,
            "does_not_modify_workbook": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
            "cnbe32_is_carrier_not_authority": True,
            "agent_standard_is_not_national_standard": True,
        },
        "preconditions": {
            "preflight_plan_status": preflight["overall_status"],
            "source_mapping_status": source_mapping["overall_status"],
            "unicode_identity_status": identity["summary"]["status"],
            "agent_standard_level": agent_standard["metadata"]["standard_level"],
            "legacy_localization_complete": localization["summary"]["all_legacy_labels_mapped"],
            "knowledge_blockers": source_mapping["summary"]["knowledge_blockers"],
        },
        "workbook_columns": workbook_columns(preflight),
        "evidence_tables": evidence_tables(source_mapping),
        "row_schema": row_schema(source_mapping),
        "blocker_rules": blocker_rules(),
        "checkpoint_contract": {
            "checkpoint_file": "reports/full_catalog_gf0017_join_checkpoint.json",
            "blocker_file": "reports/full_catalog_gf0017_join_blockers.json",
            "last_verified_offset": None,
            "resume_from": None,
            "resume_rule": "restart from last_verified_offset + 1 after blocker evidence is resolved",
        },
        "summary": {
            "workbook_columns": len(preflight["workbook"]["headers"]),
            "data_rows": identity["summary"]["data_rows"],
            "gf0017_items": source_mapping["summary"]["gf0017_items"],
            "gf0017_total_points": source_mapping["summary"]["gf0017_total_points"],
            "evidence_tables": 5,
            "blocker_rules": 6,
            "knowledge_blockers": source_mapping["summary"]["knowledge_blockers"],
        },
        "decision": {
            "may_start_blocker_reconciliation": preconditions_pass,
            "may_start_batch_gf0017_scoring": False,
            "may_rebuild_database": False,
            "may_modify_workbook": False,
            "reason": (
                "The join schema is explicit, but knowledge blockers and source-evidence joins "
                "must be reconciled before row scoring."
            ),
        },
        "next_artifacts": [
            "reports/full_catalog_gf0017_blocker_reconciliation.json",
            "reports/FULL_CATALOG_GF0017_BLOCKER_RECONCILIATION.md",
            "scripts/reconcile_full_catalog_gf0017_blockers.py",
        ],
    }
    return schema


def render_markdown(schema: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Join Schema",
        "",
        "## Purpose",
        "",
        "This report defines the row-level join contract for connecting v4_fixed",
        "workbook rows with Unicode identity, GF0017 source items, Agent structure",
        "localization, standard Hanzi knowledge, and CNBE32 carrier snapshots.",
        "",
        "It is read-only. It does not score rows, modify the workbook, rebuild",
        "databases, change CNBE32 values, create tags, publish releases, or upload",
        "to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{schema['overall_status']}`",
        f"- Next workflow status: `{schema['next_workflow_status']}`",
        f"- Data rows: `{schema['summary']['data_rows']}`",
        f"- Workbook columns: `{schema['summary']['workbook_columns']}`",
        f"- GF0017 items: `{schema['summary']['gf0017_items']}`",
        f"- Evidence tables: `{schema['summary']['evidence_tables']}`",
        f"- Knowledge blockers: `{schema['summary']['knowledge_blockers']}`",
        f"- May start blocker reconciliation: `{schema['decision']['may_start_blocker_reconciliation']}`",
        f"- May start batch GF0017 scoring: `{schema['decision']['may_start_batch_gf0017_scoring']}`",
        "",
        "## Evidence Tables",
        "",
        "| Table | Join key | Status policy |",
        "|---|---|---|",
    ]
    for table in schema["evidence_tables"]:
        key = ", ".join(f"`{value}`" for value in table["join_key"])
        lines.append(f"| `{table['table_id']}` | {key} | {table['status_policy']} |")

    lines.extend(
        [
            "",
            "## Required Row Fields",
            "",
        ]
    )
    for field in schema["row_schema"]["required_top_level_fields"]:
        lines.append(f"- `{field}`")

    lines.extend(
        [
            "",
            "## Blocker Rules",
            "",
            "| Code | Gate | Action |",
            "|---|---|---|",
        ]
    )
    for rule in schema["blocker_rules"]:
        lines.append(f"| `{rule['code']}` | {rule['gate']} | {rule['action']} |")

    lines.extend(
        [
            "",
            "## Score Policy",
            "",
            f"- Score values allowed in this phase: `{schema['row_schema']['score_policy']['score_values_allowed']}`",
            f"- Numeric score before batch phase: `{schema['row_schema']['score_policy']['numeric_score_before_batch_phase']}`",
            f"- Source gap as pass: `{schema['row_schema']['score_policy']['source_gap_as_pass']}`",
            "",
            "## Decision",
            "",
            schema["decision"]["reason"],
            "",
            "The next allowed step is blocker reconciliation and source-evidence join",
            "readiness. Batch GF0017 scoring remains blocked.",
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in schema["next_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    schema = build_join_schema()
    write_json(DEFAULT_JSON_OUTPUT, schema)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(schema))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={schema['overall_status']}")
    print(f"next_workflow_status={schema['next_workflow_status']}")
    if schema["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
