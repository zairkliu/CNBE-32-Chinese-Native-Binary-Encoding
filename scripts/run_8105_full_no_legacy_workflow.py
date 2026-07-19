#!/usr/bin/env python3
"""Run the full 8105 no-legacy standardizer and structure-item scoring workflow.

This workflow covers all 8,105 rows. It reads the standard side of
`evidence/8105/cnbe8105_encoding_comparison.json`, never uses legacy CNBE
structure fields as candidate evidence, and does not write source catalogs or
rebuild databases.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

ENCODING_COMPARISON = Path("evidence/8105/cnbe8105_encoding_comparison.json")

OUTPUT_DIR = Path("review_packets/8105_full")
STANDARDIZER_CSV = OUTPUT_DIR / "8105_full_no_legacy_standardizer.csv"
SCORING_CSV = OUTPUT_DIR / "8105_full_no_legacy_gf0017_structure_scoring.csv"
ZDIC_QUEUE_CSV = OUTPUT_DIR / "8105_full_zdic_gap_queue.csv"

STANDARDIZER_JSON = Path("reports/8105_full_no_legacy_standardizer.json")
STANDARDIZER_MD = Path("reports/8105_FULL_NO_LEGACY_STANDARDIZER.md")
SCORING_JSON = Path("reports/8105_full_no_legacy_gf0017_structure_scoring.json")
SCORING_MD = Path("reports/8105_FULL_NO_LEGACY_GF0017_STRUCTURE_SCORING.md")

EXPECTED_ROWS = 8105
BASE_ASSIGNED_SCORE = 6
COMPONENT_VALIDITY_POINTS = 3
RADICAL_VALIDITY_POINTS = 3
STRUCTURE_DECOMPOSITION_POINTS = 20
FORMAL_TOTAL = 50
ALLOWED_STRUCTURES = {
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
}
REGRESSION_CHARS = {
    "侵": ("左右", "⿰亻⿳彐冖又"),
    "偶": ("左右", "⿰亻禺"),
    "冁": ("左右", "⿰单展"),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def zdic_url(char: str) -> str:
    return f"https://www.zdic.net/hans/{quote(char)}"


def sort_key(item: tuple[str, dict[str, Any]]) -> tuple[int, int, str]:
    char, record = item
    rank = record.get("standard_rank")
    codepoint = record.get("standard", {}).get("codepoint") or ord(char)
    return (int(rank) if rank else 999999, int(codepoint), char)


def standard_complete(standard: dict[str, Any]) -> bool:
    return (
        standard.get("evidence_status") == "COMPLETE"
        and bool(standard.get("structure"))
        and bool(standard.get("decomposition"))
        and bool(standard.get("components"))
        and bool(standard.get("radical"))
        and "?" not in str(standard.get("decomposition") or "")
    )


def standardizer_status(standard: dict[str, Any]) -> str:
    if standard_complete(standard):
        return "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"
    if standard.get("structure") or standard.get("decomposition") or standard.get("components"):
        return "NATIONAL_STANDARD_CANDIDATE_PARTIAL_REVIEW_REQUIRED"
    return "STANDARDIZER_EVIDENCE_GAP_ZDIC_OR_SOURCE_REVIEW_REQUIRED"


def blocker_items(standard: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not standard.get("structure"):
        blockers.append("MISSING_STANDARD_STRUCTURE")
    if not standard.get("decomposition"):
        blockers.append("MISSING_STANDARD_DECOMPOSITION")
    if "?" in str(standard.get("decomposition") or ""):
        blockers.append("AMBIGUOUS_DECOMPOSITION")
    if not standard.get("components"):
        blockers.append("MISSING_STANDARD_COMPONENTS")
    if not standard.get("radical"):
        blockers.append("MISSING_STANDARD_RADICAL")
    blockers.extend(["CNBE32_NOT_PROPOSED", "HUMAN_REVIEW_REQUIRED"])
    return blockers


def build_standardizer_rows() -> list[dict[str, Any]]:
    comparison = load_json(ENCODING_COMPARISON)["characters"]
    rows: list[dict[str, Any]] = []
    for index, (char, record) in enumerate(sorted(comparison.items(), key=sort_key), start=1):
        standard = record.get("standard", {})
        structure = standard.get("structure") or ""
        decomposition = standard.get("decomposition") or ""
        components = standard.get("components") or []
        row = {
            "row_id": f"8105_full_{index:04d}",
            "character": char,
            "unicode_codepoint": record.get("unicode") or standard.get("unicode") or f"U+{ord(char):04X}",
            "decimal_codepoint": standard.get("codepoint") or ord(char),
            "scope": "8105_national_standard_core",
            "standard_level": standard.get("level", ""),
            "standard_rank": record.get("standard_rank") or standard.get("standard_rank") or "",
            "source_level": "national_standard_then_core_reference_then_network_cross_reference",
            "candidate_structure_label": structure,
            "candidate_structure_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if structure
                else "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED"
            ),
            "candidate_decomposition": decomposition,
            "candidate_decomposition_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if decomposition and "?" not in decomposition
                else "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED"
            ),
            "direct_component_candidates": " ".join(components),
            "radical": standard.get("radical") or "",
            "radical_status": (
                "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
                if standard.get("radical")
                else "RADICAL_STANDARD_SOURCE_CHECK_REQUIRED"
            ),
            "stroke_count": standard.get("stroke_count") or "",
            "stroke_order": standard.get("stroke_order_str") or "",
            "standard_evidence_status": standard.get("evidence_status") or "",
            "standardizer_status": standardizer_status(standard),
            "blocked_items": ";".join(blocker_items(standard)),
            "zdic_url": zdic_url(char),
            "proposed_cnbe32": "",
            "proposed_cnbe32_status": "NO_PROPOSED_CNBE32_BEFORE_REVIEW",
            "review_status": "HUMAN_REVIEW_REQUIRED",
            "cnbe_write_status": "NO_CNBE_WRITE",
            "database_rebuild_status": "NO_DATABASE_REBUILD",
        }
        rows.append(row)
    return rows


def build_zdic_gap_queue(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row["row_id"],
            "character": row["character"],
            "unicode_codepoint": row["unicode_codepoint"],
            "standard_rank": row["standard_rank"],
            "standardizer_status": row["standardizer_status"],
            "blocked_items": row["blocked_items"],
            "zdic_url": row["zdic_url"],
            "source_level": "network_cross_reference_queue",
        }
        for row in rows
        if row["standardizer_status"] != "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"
    ]


def build_standardizer_report(rows: list[dict[str, Any]], zdic_queue: list[dict[str, Any]]) -> dict[str, Any]:
    structure_labels = {row["candidate_structure_label"] for row in rows if row["candidate_structure_label"]}
    regression_failures = []
    by_char = {row["character"]: row for row in rows}
    for char, expected in REGRESSION_CHARS.items():
        row = by_char.get(char, {})
        if (row.get("candidate_structure_label"), row.get("candidate_decomposition")) != expected:
            regression_failures.append(char)
    checks = {
        "row_count_is_8105": len(rows) == EXPECTED_ROWS,
        "no_legacy_fields_present": all(
            "legacy" not in key.lower()
            for row in rows
            for key in row
        ),
        "all_structure_labels_allowed_or_blank": structure_labels <= ALLOWED_STRUCTURES,
        "regression_chars_correct": not regression_failures,
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows),
    }
    status_counts = Counter(row["standardizer_status"] for row in rows)
    return {
        "report_schema_version": "1.0",
        "mode": "full_8105_no_legacy_standardizer",
        "overall_status": "PASS_8105_FULL_NO_LEGACY_STANDARDIZER_READY" if all(checks.values()) else "BLOCKED",
        "next_workflow_status": "READY_FOR_FULL_8105_STRUCTURE_ITEM_SCORING_AND_GAP_REVIEW",
        "summary": {
            "review_rows": len(rows),
            "complete_candidate_rows": status_counts["NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"],
            "partial_candidate_rows": status_counts["NATIONAL_STANDARD_CANDIDATE_PARTIAL_REVIEW_REQUIRED"],
            "evidence_gap_rows": status_counts["STANDARDIZER_EVIDENCE_GAP_ZDIC_OR_SOURCE_REVIEW_REQUIRED"],
            "zdic_gap_queue_rows": len(zdic_queue),
            "structure_counts": dict(Counter(row["candidate_structure_label"] or "UNRESOLVED" for row in rows)),
            "standardizer_status_counts": dict(status_counts),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "regression_failures": regression_failures,
        "outputs": {
            "standardizer_csv": str(STANDARDIZER_CSV),
            "zdic_gap_queue_csv": str(ZDIC_QUEUE_CSV),
            "json_report": str(STANDARDIZER_JSON),
            "markdown_report": str(STANDARDIZER_MD),
        },
        "decision": {
            "may_score_structure_items": all(checks.values()),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "All 8105 rows were materialized without legacy structure input. "
                "Complete standard-side candidates may enter structure-item scoring; "
                "gaps route to ZDIC/source review queues."
            ),
        },
    }


def can_score_structure_items(row: dict[str, Any]) -> bool:
    return row["standardizer_status"] == "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"


def build_scoring_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored_rows: list[dict[str, Any]] = []
    for row in rows:
        ready = can_score_structure_items(row)
        new_score = (
            COMPONENT_VALIDITY_POINTS
            + RADICAL_VALIDITY_POINTS
            + STRUCTURE_DECOMPOSITION_POINTS
            if ready
            else 0
        )
        blocked = ["stroke_shape", "component_name_validity", "independent_character_rule"]
        if not ready:
            blocked.extend(["component_validity", "radical_validity", "structure_first_decomposition"])
        scored_rows.append({
            "row_id": row["row_id"],
            "character": row["character"],
            "unicode_codepoint": row["unicode_codepoint"],
            "standard_rank": row["standard_rank"],
            "candidate_structure_label": row["candidate_structure_label"],
            "candidate_decomposition": row["candidate_decomposition"],
            "direct_component_candidates": row["direct_component_candidates"],
            "radical": row["radical"],
            "standard_evidence_status": row["standard_evidence_status"],
            "base_assigned_score": BASE_ASSIGNED_SCORE,
            "component_validity_score": COMPONENT_VALIDITY_POINTS if ready else 0,
            "radical_validity_score": RADICAL_VALIDITY_POINTS if ready else 0,
            "structure_first_decomposition_score": STRUCTURE_DECOMPOSITION_POINTS if ready else 0,
            "newly_assigned_score": new_score,
            "assigned_score": BASE_ASSIGNED_SCORE + new_score,
            "formal_total": FORMAL_TOTAL,
            "row_score_status": (
                "STRUCTURE_ITEMS_SCORED_REMAINING_ITEMS_BLOCKED"
                if ready
                else "BASE_SCORE_ONLY_STRUCTURE_ITEMS_BLOCKED"
            ),
            "remaining_blocked_items": ";".join(blocked),
            "cnbe_write_status": "NO_CNBE_WRITE",
            "database_rebuild_status": "NO_DATABASE_REBUILD",
        })
    return scored_rows


def build_scoring_report(rows: list[dict[str, Any]], standardizer_report: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "row_count_is_8105": len(rows) == EXPECTED_ROWS,
        "standardizer_passed": standardizer_report["overall_status"] == "PASS_8105_FULL_NO_LEGACY_STANDARDIZER_READY",
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows),
        "component_names_remain_blocked": all("component_name_validity" in row["remaining_blocked_items"] for row in rows),
        "independent_character_rule_remains_blocked": all("independent_character_rule" in row["remaining_blocked_items"] for row in rows),
        "stroke_shape_remains_blocked": all("stroke_shape" in row["remaining_blocked_items"] for row in rows),
    }
    score_counts = Counter(str(row["assigned_score"]) for row in rows)
    status_counts = Counter(row["row_score_status"] for row in rows)
    scored_count = status_counts["STRUCTURE_ITEMS_SCORED_REMAINING_ITEMS_BLOCKED"]
    return {
        "report_schema_version": "1.0",
        "mode": "full_8105_no_legacy_gf0017_structure_item_scoring",
        "overall_status": "PASS_8105_FULL_NO_LEGACY_GF0017_STRUCTURE_SCORING" if all(checks.values()) else "BLOCKED",
        "next_workflow_status": "READY_FOR_FULL_8105_GAP_REPAIR_AND_HUMAN_REVIEW",
        "summary": {
            "scored_rows": len(rows),
            "rows_with_structure_item_score": scored_count,
            "rows_without_structure_item_score": len(rows) - scored_count,
            "score_counts": dict(score_counts),
            "row_score_status_counts": dict(status_counts),
            "new_points_per_complete_row": COMPONENT_VALIDITY_POINTS + RADICAL_VALIDITY_POINTS + STRUCTURE_DECOMPOSITION_POINTS,
            "min_assigned_score": min(row["assigned_score"] for row in rows),
            "max_assigned_score": max(row["assigned_score"] for row in rows),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "scoring_csv": str(SCORING_CSV),
            "json_report": str(SCORING_JSON),
            "markdown_report": str(SCORING_MD),
        },
        "decision": {
            "may_review_full_8105_structure_scores": all(checks.values()),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Full 8105 structure-related scores are assigned only where "
                "standard-side structure, decomposition, component, and radical "
                "evidence is complete. Remaining rows are routed to gap repair."
            ),
        },
    }


def render_standardizer_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Full No-Legacy Standardizer",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Review rows: {report['summary']['review_rows']}",
        f"- Complete candidate rows: {report['summary']['complete_candidate_rows']}",
        f"- Partial candidate rows: {report['summary']['partial_candidate_rows']}",
        f"- Evidence gap rows: {report['summary']['evidence_gap_rows']}",
        f"- ZDIC/source gap queue rows: {report['summary']['zdic_gap_queue_rows']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "Legacy CNBE structure fields are not read or emitted. Gaps are routed to",
        "the ZDIC/source review queue rather than filled by model memory.",
        "",
        "## Structure Counts",
        "",
        "| Structure | Count |",
        "|---|---:|",
    ]
    for label, count in sorted(report["summary"]["structure_counts"].items()):
        lines.append(f"| `{label}` | {count} |")
    lines.extend(["", "## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def render_scoring_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Full No-Legacy GF0017 Structure Scoring",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Scored rows: {report['summary']['scored_rows']}",
        f"- Rows with structure-item score: {report['summary']['rows_with_structure_item_score']}",
        f"- Rows without structure-item score: {report['summary']['rows_without_structure_item_score']}",
        f"- New points per complete row: {report['summary']['new_points_per_complete_row']}",
        f"- Min assigned score: {report['summary']['min_assigned_score']}",
        f"- Max assigned score: {report['summary']['max_assigned_score']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "## Score Counts",
        "",
        "| Score | Rows |",
        "|---:|---:|",
    ]
    for score, count in sorted(report["summary"]["score_counts"].items(), key=lambda item: int(item[0])):
        lines.append(f"| {score} | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def run_workflow() -> tuple[dict[str, Any], dict[str, Any]]:
    standardizer_rows = build_standardizer_rows()
    zdic_queue = build_zdic_gap_queue(standardizer_rows)
    standardizer_report = build_standardizer_report(standardizer_rows, zdic_queue)
    scoring_rows = build_scoring_rows(standardizer_rows)
    scoring_report = build_scoring_report(scoring_rows, standardizer_report)

    write_csv(STANDARDIZER_CSV, standardizer_rows)
    write_csv(ZDIC_QUEUE_CSV, zdic_queue)
    write_csv(SCORING_CSV, scoring_rows)
    write_json(STANDARDIZER_JSON, standardizer_report)
    write_text(STANDARDIZER_MD, render_standardizer_markdown(standardizer_report))
    write_json(SCORING_JSON, scoring_report)
    write_text(SCORING_MD, render_scoring_markdown(scoring_report))
    return standardizer_report, scoring_report


def main() -> None:
    standardizer_report, scoring_report = run_workflow()
    print(standardizer_report["overall_status"])
    print(scoring_report["overall_status"])
    print(f"review_rows={standardizer_report['summary']['review_rows']}")
    print(f"complete_candidate_rows={standardizer_report['summary']['complete_candidate_rows']}")
    print(f"gap_queue_rows={standardizer_report['summary']['zdic_gap_queue_rows']}")
    print(f"rows_with_structure_item_score={scoring_report['summary']['rows_with_structure_item_score']}")


if __name__ == "__main__":
    main()
