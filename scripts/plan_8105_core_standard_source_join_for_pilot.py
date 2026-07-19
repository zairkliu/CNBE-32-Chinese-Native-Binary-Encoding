#!/usr/bin/env python3
"""Plan the standard-source join for the 100-row 8105 pilot control set.

This read-only gate joins the 300-character pilot evidence packet back to the
structured 8105 baseline. It locks Unicode, 8105 level/rank, stroke count, and
stroke order for the 100 core rows, while keeping structure and decomposition
as pending source-extraction work.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

PILOT_JOIN_CSV = Path("review_packets/300_character_8105_pilot/300_character_pilot_evidence_join.csv")
BASE_8105 = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/base_character_data.json")
CNBE_8105_KNOWLEDGE = Path(
    "/Users/liuzhaoqi/Documents/cnbe-research/knowledge/structured/cnbe_character_knowledge.json"
)

DEFAULT_JSON_OUTPUT = Path("reports/8105_core_standard_source_join_pilot_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN.md")
DEFAULT_CSV_OUTPUT = Path("review_packets/300_character_8105_pilot/8105_core_standard_source_join_pilot_plan.csv")

EXPECTED_CORE_ROWS = 100
EXPECTED_BASE_ROWS = 8105

ROW_FIELDNAMES = [
    "pilot_id",
    "char",
    "unicode",
    "stratum",
    "base_8105_found",
    "base_unicode_match",
    "standard_level",
    "standard_rank",
    "stroke_count",
    "stroke_order_str",
    "stroke_join_status",
    "dictionary_context_status",
    "structure_join_status",
    "decomposition_join_status",
    "gf0017_points_assigned",
    "final_structure_label",
    "cnbe_write_status",
    "next_required_action",
]

STRUCTURE_FIELDS = {
    "structure",
    "structure_type",
    "agent_structure",
    "结构",
    "字形结构",
    "hanzi_structure",
}

DECOMPOSITION_FIELDS = {
    "decomposition",
    "components",
    "component_sequence",
    "拆分",
    "部件",
    "hanzi_decomposition",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in ROW_FIELDNAMES} for row in rows])


def index_knowledge_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["char"]: row for row in rows if isinstance(row, dict) and row.get("char")}


def has_any_field(row: dict[str, Any], field_names: set[str]) -> bool:
    return any(row.get(field) not in (None, "", [], {}) for field in field_names)


def dictionary_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_CNBE_8105_KNOWLEDGE_ROW"
    if row.get("has_dictionary_entry"):
        return "CROSS_REFERENCE_CONTEXT_AVAILABLE"
    return "NO_DICTIONARY_CONTEXT"


def build_plan() -> dict[str, Any]:
    pilot_rows = read_csv(PILOT_JOIN_CSV)
    base_8105: dict[str, dict[str, Any]] = load_json(BASE_8105)
    knowledge_index = index_knowledge_rows(load_json(CNBE_8105_KNOWLEDGE))
    core_rows = [row for row in pilot_rows if row["stratum"] == "8105_core_control"]

    output_rows: list[dict[str, Any]] = []
    for pilot in core_rows:
        char = pilot["char"]
        unicode_value = pilot["unicode"]
        base_row = base_8105.get(char)
        knowledge_row = knowledge_index.get(char)
        base_found = base_row is not None
        unicode_match = bool(base_row and base_row.get("unicode") == unicode_value)
        stroke_available = bool(base_row and base_row.get("stroke_count") and base_row.get("stroke_order_str"))
        structure_candidate = has_any_field(knowledge_row or {}, STRUCTURE_FIELDS)
        decomposition_candidate = has_any_field(knowledge_row or {}, DECOMPOSITION_FIELDS)
        output_rows.append(
            {
                "pilot_id": pilot["pilot_id"],
                "char": char,
                "unicode": unicode_value,
                "stratum": pilot["stratum"],
                "base_8105_found": base_found,
                "base_unicode_match": unicode_match,
                "standard_level": base_row.get("level", "") if base_row else "",
                "standard_rank": base_row.get("standard_rank", "") if base_row else "",
                "stroke_count": base_row.get("stroke_count", "") if base_row else "",
                "stroke_order_str": base_row.get("stroke_order_str", "") if base_row else "",
                "stroke_join_status": "STANDARD_DERIVED_STROKE_JOIN_READY"
                if stroke_available and unicode_match
                else "STANDARD_DERIVED_STROKE_JOIN_BLOCKED",
                "dictionary_context_status": dictionary_status(knowledge_row),
                "structure_join_status": "STRUCTURE_CANDIDATE_FIELD_PRESENT_REQUIRES_SOURCE_AUDIT"
                if structure_candidate
                else "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED",
                "decomposition_join_status": "DECOMPOSITION_CANDIDATE_FIELD_PRESENT_REQUIRES_SOURCE_AUDIT"
                if decomposition_candidate
                else "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED",
                "gf0017_points_assigned": 0,
                "final_structure_label": "",
                "cnbe_write_status": "NO_CNBE_WRITE",
                "next_required_action": "extract_structure_decomposition_from_standard_sources_before_scoring",
            }
        )

    summary = {
        "core_pilot_rows": len(output_rows),
        "base_8105_total_rows": len(base_8105),
        "base_8105_found_rows": sum(1 for row in output_rows if row["base_8105_found"]),
        "base_unicode_match_rows": sum(1 for row in output_rows if row["base_unicode_match"]),
        "stroke_join_ready_rows": sum(
            1 for row in output_rows if row["stroke_join_status"] == "STANDARD_DERIVED_STROKE_JOIN_READY"
        ),
        "structure_standard_source_required_rows": sum(
            1 for row in output_rows if row["structure_join_status"] == "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        ),
        "decomposition_standard_source_required_rows": sum(
            1
            for row in output_rows
            if row["decomposition_join_status"] == "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        ),
        "dictionary_context_rows": sum(
            1 for row in output_rows if row["dictionary_context_status"] == "CROSS_REFERENCE_CONTEXT_AVAILABLE"
        ),
        "gf0017_points_assigned": sum(int(row["gf0017_points_assigned"]) for row in output_rows),
        "final_structure_labels_emitted": sum(1 for row in output_rows if row["final_structure_label"]),
        "cnbe_rows_written": sum(1 for row in output_rows if row["cnbe_write_status"] != "NO_CNBE_WRITE"),
    }
    checks = {
        "core_row_count_matches": summary["core_pilot_rows"] == EXPECTED_CORE_ROWS,
        "base_8105_count_matches": summary["base_8105_total_rows"] == EXPECTED_BASE_ROWS,
        "all_core_rows_found_in_base": summary["base_8105_found_rows"] == EXPECTED_CORE_ROWS,
        "all_core_unicode_values_match": summary["base_unicode_match_rows"] == EXPECTED_CORE_ROWS,
        "all_core_stroke_fields_joined": summary["stroke_join_ready_rows"] == EXPECTED_CORE_ROWS,
        "structure_decomposition_kept_pending": summary["structure_standard_source_required_rows"] == EXPECTED_CORE_ROWS
        and summary["decomposition_standard_source_required_rows"] == EXPECTED_CORE_ROWS,
        "no_gf0017_points_assigned": summary["gf0017_points_assigned"] == 0,
        "no_final_structure_labels": summary["final_structure_labels_emitted"] == 0,
        "no_cnbe_rows_written": summary["cnbe_rows_written"] == 0,
        "no_database_rebuild": True,
        "no_xlsx_generated": True,
        "no_source_asset_write": True,
    }
    status = "PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_8105_core_standard_source_join_pilot_plan",
        "overall_status": status,
        "next_workflow_status": "READY_FOR_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_NO_SCORING",
        "inputs": {
            "pilot_join_csv": str(PILOT_JOIN_CSV),
            "base_8105": str(BASE_8105),
            "cnbe_8105_knowledge": str(CNBE_8105_KNOWLEDGE),
        },
        "authority_boundary": {
            "base_8105_is_standard_derived_core": True,
            "cnbe_8105_knowledge_dictionary_text_is_cross_reference": True,
            "structure_decomposition_not_filled_from_dictionary_or_visual_memory": True,
            "formal_gf0017_scoring_remains_blocked": True,
        },
        "summary": summary,
        "checks": checks,
        "decision": {
            "may_start_structure_decomposition_source_extraction_plan": status
            == "PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY",
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "may_generate_full_catalog_copy": False,
        },
        "rows": output_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    checks = report["checks"]
    lines = [
        "# 8105 Core Standard Source Join Pilot Plan",
        "",
        f"Overall status: `{report['overall_status']}`",
        f"Next workflow status: `{report['next_workflow_status']}`",
        "",
        "## Scope",
        "",
        "This report covers only the 100-row `8105_core_control` stratum from the existing 300-character pilot.",
        "It does not regenerate the 97,686-row catalog, assign GF0017 points, emit final structure labels, write CNBE rows, rebuild a database, or generate an XLSX workbook.",
        "",
        "## Summary",
        "",
        f"- Core pilot rows: {summary['core_pilot_rows']}",
        f"- Base 8105 rows: {summary['base_8105_total_rows']}",
        f"- Base Unicode matches: {summary['base_unicode_match_rows']}",
        f"- Stroke count/order joined: {summary['stroke_join_ready_rows']}",
        f"- Structure standard-source extraction required: {summary['structure_standard_source_required_rows']}",
        f"- Decomposition standard-source extraction required: {summary['decomposition_standard_source_required_rows']}",
        f"- Dictionary context rows: {summary['dictionary_context_rows']}",
        f"- GF0017 points assigned: {summary['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {summary['final_structure_labels_emitted']}",
        f"- CNBE rows written: {summary['cnbe_rows_written']}",
        "",
        "## Gate Checks",
        "",
    ]
    for name, passed in checks.items():
        lines.append(f"- {name}: `{passed}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "`base_character_data.json` supplies standard-derived Unicode identity, 8105 level/rank, stroke count, and stroke order for this pilot control set.",
            "`cnbe_character_knowledge.json` supplies dictionary context but no source-audited structure or decomposition fields for these rows.",
            "The next allowed step is a separate standard-source extraction plan for structure and decomposition.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, report["rows"])
    print(report["overall_status"])


if __name__ == "__main__":
    main()
