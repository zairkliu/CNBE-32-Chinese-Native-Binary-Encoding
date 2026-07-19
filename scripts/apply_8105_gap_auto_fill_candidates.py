#!/usr/bin/env python3
"""Create no-write auto-fill candidates for the full 8105 gap queue.

The script uses only deterministic rules and already materialized reference
records. It never promotes legacy CNBE structure fields, ZDIC, or dictionary
context to national-standard authority. All outputs are review packets.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

STANDARDIZER_CSV = Path("review_packets/8105_full/8105_full_no_legacy_standardizer.csv")

OUTPUT_DIR = Path("review_packets/8105_full")
AUTO_FILL_CSV = OUTPUT_DIR / "8105_full_gap_auto_fill_candidates.csv"
REMAINING_GAP_CSV = OUTPUT_DIR / "8105_full_gap_remaining_review_queue.csv"
REPORT_JSON = Path("reports/8105_full_gap_auto_fill_candidates.json")
REPORT_MD = Path("reports/8105_FULL_GAP_AUTO_FILL_CANDIDATES.md")

EXPECTED_ROWS = 8105
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

IDS_TO_STRUCTURE = {
    "⿰": "左右",
    "⿱": "上下",
    "⿲": "左中右",
    "⿳": "上中下",
    "⿴": "全包围",
    "⿵": "上三包",
    "⿶": "下三包",
    "⿷": "左三包",
    "⿸": "左上包",
    "⿹": "右上包",
    "⿺": "左下包",
    "⿻": "镶嵌",
}

FORBIDDEN_LEGACY_STRUCTURES = {"右下包", "品字形", "三叠结构", "会意结构"}
REVIEW_ONLY_AUTHORITY = "AGENT_REVIEW_CANDIDATE_NOT_NATIONAL_STANDARD"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def split_components(value: str) -> list[str]:
    return [item for item in value.split(" ") if item]


def infer_structure_from_decomposition(decomposition: str) -> str:
    if not decomposition or "?" in decomposition:
        return ""
    return IDS_TO_STRUCTURE.get(decomposition[0], "")


def candidate_for_row(row: dict[str, str]) -> dict[str, Any]:
    char = row["character"]
    structure = row["candidate_structure_label"]
    decomposition = row["candidate_decomposition"]
    components = split_components(row["direct_component_candidates"])
    proposed_structure = structure
    proposed_decomposition = decomposition
    proposed_components = row["direct_component_candidates"]
    fill_rule = ""
    evidence_layer = ""
    confidence = ""
    blocker = ""

    if structure == "独体字" and decomposition == "?" and components == [char]:
        proposed_decomposition = char
        fill_rule = "single_component_identity_decomposition"
        evidence_layer = "standard_derived_agent_rule"
        confidence = "HIGH_REVIEW_REQUIRED"
    elif not structure and infer_structure_from_decomposition(decomposition):
        proposed_structure = infer_structure_from_decomposition(decomposition)
        fill_rule = "ids_operator_structure_mapping"
        evidence_layer = "standard_derived_from_existing_decomposition"
        confidence = "HIGH_REVIEW_REQUIRED"
    if not fill_rule:
        blocker = "SOURCE_EVIDENCE_REQUIRED"
    elif not proposed_decomposition:
        blocker = "DECOMPOSITION_STILL_MISSING_REVIEW_REQUIRED"
    elif proposed_structure not in ALLOWED_STRUCTURES:
        blocker = "PROPOSED_STRUCTURE_OUTSIDE_ALLOWED_SET"
    elif proposed_structure in FORBIDDEN_LEGACY_STRUCTURES:
        blocker = "FORBIDDEN_LEGACY_STRUCTURE"
    elif "?" in str(proposed_decomposition):
        blocker = "DECOMPOSITION_STILL_AMBIGUOUS_REVIEW_REQUIRED"
    else:
        blocker = "REVIEW_REQUIRED_BEFORE_MERGE"

    return {
        "row_id": row["row_id"],
        "character": char,
        "unicode_codepoint": row["unicode_codepoint"],
        "standard_rank": row["standard_rank"],
        "original_structure": structure,
        "original_decomposition": decomposition,
        "original_components": row["direct_component_candidates"],
        "proposed_structure": proposed_structure,
        "proposed_decomposition": proposed_decomposition,
        "proposed_components": proposed_components,
        "radical": row["radical"],
        "fill_rule": fill_rule or "no_safe_auto_fill",
        "evidence_layer": evidence_layer or "unresolved",
        "authority_boundary": REVIEW_ONLY_AUTHORITY,
        "confidence": confidence or "NONE",
        "blocker": blocker,
        "review_status": "HUMAN_REVIEW_REQUIRED",
        "cnbe_write_status": "NO_CNBE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
        "zdic_url": row["zdic_url"],
    }


def build_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv(STANDARDIZER_CSV)
    gaps = [
        row
        for row in rows
        if row["standardizer_status"] != "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED"
    ]
    candidate_rows = [candidate_for_row(row) for row in gaps]
    auto_rows = [row for row in candidate_rows if row["fill_rule"] != "no_safe_auto_fill"]
    remaining_rows = [row for row in candidate_rows if row["fill_rule"] == "no_safe_auto_fill"]
    proposed_structures = {row["proposed_structure"] for row in auto_rows if row["proposed_structure"]}
    checks = {
        "standardizer_row_count_is_8105": len(rows) == EXPECTED_ROWS,
        "gap_rows_accounted_for": len(auto_rows) + len(remaining_rows) == len(gaps),
        "proposed_structures_allowed": proposed_structures <= ALLOWED_STRUCTURES,
        "forbidden_legacy_structures_absent": not (proposed_structures & FORBIDDEN_LEGACY_STRUCTURES),
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in candidate_rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in candidate_rows),
        "network_references_not_national_standard": all(
            row["authority_boundary"] == REVIEW_ONLY_AUTHORITY for row in candidate_rows
        ),
    }
    fill_counts = Counter(row["fill_rule"] for row in candidate_rows)
    structure_counts = Counter(row["proposed_structure"] or "UNRESOLVED" for row in auto_rows)
    report = {
        "report_schema_version": "1.0",
        "mode": "full_8105_gap_auto_fill_candidates_no_write",
        "overall_status": "PASS_8105_GAP_AUTO_FILL_CANDIDATES_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "standardizer_rows": len(rows),
            "gap_rows": len(gaps),
            "auto_fill_candidate_rows": len(auto_rows),
            "remaining_review_rows": len(remaining_rows),
            "fill_rule_counts": dict(fill_counts),
            "auto_fill_structure_counts": dict(structure_counts),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "auto_fill_candidates_csv": str(AUTO_FILL_CSV),
            "remaining_gap_review_queue_csv": str(REMAINING_GAP_CSV),
            "json_report": str(REPORT_JSON),
            "markdown_report": str(REPORT_MD),
        },
        "decision": {
            "may_human_review_auto_fill_candidates": all(checks.values()),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Only deterministic single-component and IDS-operator rules are "
                "used. Network references remain review context and all candidates "
                "require human/source review before any merge."
            ),
        },
    }
    return auto_rows, remaining_rows, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Full Gap Auto-Fill Candidates",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Gap rows: {report['summary']['gap_rows']}",
        f"- Auto-fill candidate rows: {report['summary']['auto_fill_candidate_rows']}",
        f"- Remaining review rows: {report['summary']['remaining_review_rows']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "## Fill Rule Counts",
        "",
        "| Rule | Rows |",
        "|---|---:|",
    ]
    for rule, count in sorted(report["summary"]["fill_rule_counts"].items()):
        lines.append(f"| `{rule}` | {count} |")
    lines.extend(["", "## Auto-Fill Structure Counts", "", "| Structure | Rows |", "|---|---:|"])
    for structure, count in sorted(report["summary"]["auto_fill_structure_counts"].items()):
        lines.append(f"| `{structure}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    auto_rows, remaining_rows, report = build_candidates()
    write_csv(AUTO_FILL_CSV, auto_rows)
    write_csv(REMAINING_GAP_CSV, remaining_rows)
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_markdown(report))
    return report


def main() -> None:
    report = run()
    print(report["overall_status"])
    print(f"gap_rows={report['summary']['gap_rows']}")
    print(f"auto_fill_candidate_rows={report['summary']['auto_fill_candidate_rows']}")
    print(f"remaining_review_rows={report['summary']['remaining_review_rows']}")


if __name__ == "__main__":
    main()
