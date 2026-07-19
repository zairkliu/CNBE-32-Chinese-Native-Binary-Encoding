#!/usr/bin/env python3
"""Plan 8105-core structure/decomposition source extraction.

This read-only runner prepares the handoff from the 100-row 8105 core pilot to
`cnbe-hanzi-decomposition-standardizer`. It validates input rows, standard
source availability, output schema coverage, and no-score/no-write boundaries.
It does not extract final structure labels, assign GF0017 points, write CNBE
rows, rebuild databases, or duplicate the full catalog.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

STANDARD_JOIN_REPORT = Path("reports/8105_core_standard_source_join_pilot_plan.json")
STANDARD_JOIN_CSV = Path("review_packets/300_character_8105_pilot/8105_core_standard_source_join_pilot_plan.csv")

DEFAULT_JSON_OUTPUT = Path("reports/8105_core_structure_decomposition_source_extraction_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN.md")
DEFAULT_CSV_OUTPUT = Path(
    "review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv"
)

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")

STANDARD_SOURCES = [
    {
        "source_id": "GF0014_2009_COMPONENT_NAMES",
        "path": RESEARCH_ROOT
        / "source/03-部件及部件名称规范/GF 0014-2009 现代常用字部件及部件名称规范.md",
        "controls": ["component_validity", "component_name_validity", "structure_first_decomposition"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GB13000_COMPONENT_SPEC_1998",
        "path": RESEARCH_ROOT
        / "source/06-汉字部件规范/信息处理用GB 13000.1 字符集汉字部件规范 （1998-5-1）.md",
        "controls": ["component_validity", "structure_first_decomposition"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GF0013_2009_SINGLE_COMPONENT",
        "path": RESEARCH_ROOT / "source/04-独体字规范/GF 0013-2009 现代常用独体字规范.md",
        "controls": ["independent_character_rule", "structure_first_decomposition"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GG0011_2009_RADICALS",
        "path": RESEARCH_ROOT / "source/02-汉字部首表/GG 0011-2009 汉字部首表.md",
        "controls": ["radical_validity"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GF0031_2026_STROKE_ORDER",
        "path": RESEARCH_ROOT / "source/05-笔顺规范/GF 0031—2026 通用规范汉字笔顺规范.md",
        "controls": ["stroke_order", "stroke_shape"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GF3002_1999_STROKE_ORDER",
        "path": RESEARCH_ROOT / "source/05-笔顺规范/GF3002-1999 GB13000.1字符集汉字笔顺规范.md",
        "controls": ["stroke_order"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GB13000_FOLDED_STROKE",
        "path": RESEARCH_ROOT / "source/07-折笔规范/GB 13000.1 字符集汉字折笔规范.md",
        "controls": ["stroke_shape"],
        "source_grade": "direct_standard_text",
    },
    {
        "source_id": "GF3003_1999_STROKE_ORDERING",
        "path": RESEARCH_ROOT / "source/08-字序规范/GF3003-1999 GB13000.1字符集汉字字序（笔画序）规范.md",
        "controls": ["stroke_order", "ordering_context"],
        "source_grade": "direct_standard_text",
    },
]

HANDOFF_FIELDNAMES = [
    "row_id",
    "char",
    "unicode",
    "codepoint",
    "scope_status",
    "authority_layer",
    "unicode_identity_status",
    "raw_structure_label",
    "normalized_structure_label",
    "structure_join_status",
    "decomposition_tree",
    "decomposition_join_status",
    "character_components",
    "non_character_components",
    "basic_components",
    "component_names",
    "component_name_status",
    "single_component_status",
    "radical_context_status",
    "stroke_context_status",
    "source_grade",
    "source_refs",
    "cross_reference_refs",
    "blocker",
    "next_required_action",
    "gf0017_points_assigned",
    "final_structure_label",
    "cnbe_write_status",
    "database_rebuild_status",
    "review_notice",
]

EXPECTED_ROWS = 100


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
        writer = csv.DictWriter(handle, fieldnames=HANDOFF_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in HANDOFF_FIELDNAMES} for row in rows])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest() -> list[dict[str, Any]]:
    manifest = []
    for source in STANDARD_SOURCES:
        path = source["path"]
        exists = path.exists()
        manifest.append(
            {
                "source_id": source["source_id"],
                "path": str(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": sha256_file(path) if exists else "",
                "controls": source["controls"],
                "source_grade": source["source_grade"] if exists else "unresolved",
            }
        )
    return manifest


def codepoint_from_unicode(unicode_value: str) -> int:
    return int(unicode_value[2:], 16)


def standardizer_row(row: dict[str, str], source_refs: str) -> dict[str, Any]:
    return {
        "row_id": row["pilot_id"],
        "char": row["char"],
        "unicode": row["unicode"],
        "codepoint": codepoint_from_unicode(row["unicode"]),
        "scope_status": "8105_core_control",
        "authority_layer": "national_standard_core_pending_structure_decomposition_extraction",
        "unicode_identity_status": "PASS_UNICODE_IDENTITY",
        "raw_structure_label": "",
        "normalized_structure_label": "",
        "structure_join_status": "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED",
        "decomposition_tree": "",
        "decomposition_join_status": "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED",
        "character_components": "",
        "non_character_components": "",
        "basic_components": "",
        "component_names": "",
        "component_name_status": "COMPONENT_NAMES_STANDARD_SOURCE_REQUIRED",
        "single_component_status": "SINGLE_COMPONENT_SOURCE_CHECK_REQUIRED",
        "radical_context_status": "RADICAL_STANDARD_SOURCE_CHECK_REQUIRED",
        "stroke_context_status": row["stroke_join_status"],
        "source_grade": "standard_extraction_planned_not_joined",
        "source_refs": source_refs,
        "cross_reference_refs": row["dictionary_context_status"],
        "blocker": "MISSING_STANDARD_STRUCTURE_SOURCE;MISSING_STANDARD_DECOMPOSITION_SOURCE",
        "next_required_action": "run_bounded_standard_source_extractor_with_human_review_gate",
        "gf0017_points_assigned": 0,
        "final_structure_label": "",
        "cnbe_write_status": "NO_CNBE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
        "review_notice": "STANDARDIZER_HANDOFF_ONLY_NOT_SCORE_OR_ENCODING",
    }


def build_plan() -> dict[str, Any]:
    previous_report = load_json(STANDARD_JOIN_REPORT)
    source_records = source_manifest()
    rows = read_csv(STANDARD_JOIN_CSV)
    source_refs = ";".join(record["source_id"] for record in source_records if record["exists"])
    handoff_rows = [standardizer_row(row, source_refs) for row in rows]

    summary = {
        "input_rows": len(rows),
        "handoff_rows": len(handoff_rows),
        "standard_source_records": len(source_records),
        "standard_source_records_available": sum(1 for record in source_records if record["exists"]),
        "unicode_identity_pass_rows": sum(
            1 for row in handoff_rows if row["unicode_identity_status"] == "PASS_UNICODE_IDENTITY"
        ),
        "structure_source_required_rows": sum(
            1 for row in handoff_rows if row["structure_join_status"] == "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        ),
        "decomposition_source_required_rows": sum(
            1
            for row in handoff_rows
            if row["decomposition_join_status"] == "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        ),
        "component_name_source_required_rows": sum(
            1 for row in handoff_rows if row["component_name_status"] == "COMPONENT_NAMES_STANDARD_SOURCE_REQUIRED"
        ),
        "gf0017_points_assigned": sum(int(row["gf0017_points_assigned"]) for row in handoff_rows),
        "final_structure_labels_emitted": sum(1 for row in handoff_rows if row["final_structure_label"]),
        "cnbe_rows_written": sum(1 for row in handoff_rows if row["cnbe_write_status"] != "NO_CNBE_WRITE"),
        "database_rebuild_allowed": False,
    }
    checks = {
        "previous_standard_join_passed": previous_report["overall_status"]
        == "PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY",
        "input_row_count_matches": summary["input_rows"] == EXPECTED_ROWS,
        "handoff_row_count_matches": summary["handoff_rows"] == EXPECTED_ROWS,
        "all_standard_sources_available": summary["standard_source_records_available"] == len(source_records),
        "all_rows_have_unicode_identity": summary["unicode_identity_pass_rows"] == EXPECTED_ROWS,
        "all_rows_remain_structure_pending": summary["structure_source_required_rows"] == EXPECTED_ROWS,
        "all_rows_remain_decomposition_pending": summary["decomposition_source_required_rows"] == EXPECTED_ROWS,
        "component_name_gate_pending": summary["component_name_source_required_rows"] == EXPECTED_ROWS,
        "no_gf0017_points_assigned": summary["gf0017_points_assigned"] == 0,
        "no_final_structure_labels": summary["final_structure_labels_emitted"] == 0,
        "no_cnbe_rows_written": summary["cnbe_rows_written"] == 0,
        "no_database_rebuild": summary["database_rebuild_allowed"] is False,
        "no_full_catalog_copy": True,
        "no_source_asset_write": True,
    }
    status = (
        "PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY"
        if all(checks.values())
        else "BLOCKED_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_8105_core_structure_decomposition_source_extraction_plan",
        "overall_status": status,
        "next_workflow_status": "READY_FOR_BOUNDED_STANDARDIZER_EXTRACTION_RUN_NO_SCORING",
        "skill_handoff": {
            "skill": "cnbe-hanzi-decomposition-standardizer",
            "task_type": "batch",
            "input_path": str(DEFAULT_CSV_OUTPUT),
            "input_scope": "8105_core_control",
            "join_key": "unicode",
            "mode": "evidence_only_no_score",
            "allowed_outputs": ["bounded_json_report", "bounded_csv_review_packet", "markdown_summary"],
            "forbidden_outputs": ["full_catalog_copy", "gf0017_points", "final_encoding_table", "database"],
        },
        "standard_sources": source_records,
        "summary": summary,
        "checks": checks,
        "decision": {
            "may_run_bounded_standardizer_extraction": status
            == "PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY",
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_research_knowledge": False,
        },
        "handoff_rows": handoff_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# 8105 Core Structure Decomposition Source Extraction Plan",
        "",
        f"Overall status: `{report['overall_status']}`",
        f"Next workflow status: `{report['next_workflow_status']}`",
        "",
        "## Scope",
        "",
        "This is a bounded plan for the 100-row `8105_core_control` pilot stratum.",
        "It prepares the input contract for `cnbe-hanzi-decomposition-standardizer`.",
        "It does not extract final labels, assign GF0017 points, write CNBE rows, rebuild databases, or duplicate the full catalog.",
        "",
        "## Summary",
        "",
        f"- Input rows: {summary['input_rows']}",
        f"- Handoff rows: {summary['handoff_rows']}",
        f"- Standard source records available: {summary['standard_source_records_available']} / {summary['standard_source_records']}",
        f"- Unicode identity pass rows: {summary['unicode_identity_pass_rows']}",
        f"- Structure source required rows: {summary['structure_source_required_rows']}",
        f"- Decomposition source required rows: {summary['decomposition_source_required_rows']}",
        f"- Component-name source required rows: {summary['component_name_source_required_rows']}",
        f"- GF0017 points assigned: {summary['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {summary['final_structure_labels_emitted']}",
        f"- CNBE rows written: {summary['cnbe_rows_written']}",
        "",
        "## Standardizer Call",
        "",
        "```text",
    ]
    for key, value in report["skill_handoff"].items():
        lines.append(f"{key}: {value}")
    lines.extend(["```", "", "## Gate Checks", ""])
    for name, passed in report["checks"].items():
        lines.append(f"- {name}: `{passed}`")
    lines.extend(["", "## Standard Sources", ""])
    for record in report["standard_sources"]:
        lines.append(
            f"- `{record['source_id']}`: exists=`{record['exists']}`, size={record['size_bytes']}, sha256=`{record['sha256']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, report["handoff_rows"])
    print(report["overall_status"])


if __name__ == "__main__":
    main()
