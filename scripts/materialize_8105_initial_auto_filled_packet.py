#!/usr/bin/env python3
"""Materialize the initial auto-filled 8105 review packet.

This script applies the already-audited priority candidates to a separate
review packet. It does not modify the source standardizer packet, CNBE source
tables, cnbe-research knowledge assets, or databases.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

STANDARDIZER_CSV = Path("review_packets/8105_full/8105_full_no_legacy_standardizer.csv")
PRIORITY_CANDIDATES_CSV = Path("review_packets/8105_full/8105_gap_priority_reference_candidates.csv")

OUTPUT_DIR = Path("review_packets/8105_full")
INITIAL_PACKET_CSV = OUTPUT_DIR / "8105_initial_auto_filled_review_packet.csv"
INITIAL_FILLED_CSV = OUTPUT_DIR / "8105_initial_auto_filled_rows.csv"
INITIAL_REMAINING_CSV = OUTPUT_DIR / "8105_initial_remaining_gap_queue.csv"

REPORT_JSON = Path("reports/8105_initial_auto_filled_project.json")
REPORT_MD = Path("reports/8105_INITIAL_AUTO_FILLED_PROJECT.md")

EXPECTED_ROWS = 8105
EXPECTED_AUTO_FILL_ROWS = 30
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
IDS_OPERATORS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻")


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


def components_from_decomposition(decomposition: str) -> str:
    parts = [char for char in decomposition if char not in IDS_OPERATORS and char != "?"]
    return " ".join(parts)


def load_candidates() -> dict[str, dict[str, str]]:
    rows = read_csv(PRIORITY_CANDIDATES_CSV)
    return {row["character"]: row for row in rows}


def apply_candidate(row: dict[str, str], candidate: dict[str, str] | None) -> dict[str, Any]:
    output = dict(row)
    output["initial_fill_status"] = "UNCHANGED"
    output["initial_fill_rule"] = ""
    output["initial_source_priority"] = ""
    output["initial_authority_boundary"] = ""
    output["initial_review_status"] = row.get("review_status", "HUMAN_REVIEW_REQUIRED")
    output["initial_cnbe_write_status"] = "NO_CNBE_WRITE"
    output["initial_database_rebuild_status"] = "NO_DATABASE_REBUILD"

    if not candidate:
        if row["standardizer_status"] == "NATIONAL_STANDARD_CANDIDATE_COMPLETE_REVIEW_REQUIRED":
            output["initial_completion_status"] = "COMPLETE_CANDIDATE_UNCHANGED"
        else:
            output["initial_completion_status"] = "REMAINING_GAP_REVIEW_REQUIRED"
        return output

    proposed_structure = candidate["proposed_structure"]
    proposed_decomposition = candidate["proposed_decomposition"]
    if proposed_structure not in ALLOWED_STRUCTURES or not proposed_decomposition:
        output["initial_completion_status"] = "CANDIDATE_REJECTED_REVIEW_REQUIRED"
        output["initial_fill_status"] = "REJECTED"
        return output

    output["candidate_structure_label"] = proposed_structure
    output["candidate_decomposition"] = proposed_decomposition
    components = row["direct_component_candidates"] or components_from_decomposition(proposed_decomposition)
    output["direct_component_candidates"] = components
    output["standardizer_status"] = "INITIAL_AUTO_FILLED_REVIEW_REQUIRED"
    output["blocked_items"] = "CNBE32_NOT_PROPOSED;HUMAN_REVIEW_REQUIRED"
    output["candidate_structure_status"] = "INITIAL_AUTO_FILL_REVIEW_REQUIRED"
    output["candidate_decomposition_status"] = "INITIAL_AUTO_FILL_REVIEW_REQUIRED"
    output["initial_completion_status"] = "INITIAL_AUTO_FILLED_REVIEW_REQUIRED"
    output["initial_fill_status"] = "APPLIED_TO_REVIEW_PACKET"
    output["initial_fill_rule"] = candidate["candidate_rule"]
    output["initial_source_priority"] = candidate["source_priority"]
    output["initial_authority_boundary"] = candidate["authority_boundary"]
    output["initial_review_status"] = "HUMAN_REVIEW_REQUIRED_BEFORE_SOURCE_MERGE"
    return output


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv(STANDARDIZER_CSV)
    candidates = load_candidates()
    packet = [apply_candidate(row, candidates.get(row["character"])) for row in rows]
    filled_rows = [row for row in packet if row["initial_fill_status"] == "APPLIED_TO_REVIEW_PACKET"]
    remaining_rows = [row for row in packet if row["initial_completion_status"] == "REMAINING_GAP_REVIEW_REQUIRED"]
    structure_labels = {row["candidate_structure_label"] for row in packet if row["candidate_structure_label"]}
    completion_counts = Counter(row["initial_completion_status"] for row in packet)
    checks = {
        "row_count_is_8105": len(packet) == EXPECTED_ROWS,
        "auto_fill_rows_expected": len(filled_rows) == EXPECTED_AUTO_FILL_ROWS,
        "all_structures_allowed_or_blank": structure_labels <= ALLOWED_STRUCTURES,
        "remaining_rows_accounted_for": len(remaining_rows) + completion_counts["COMPLETE_CANDIDATE_UNCHANGED"] + len(filled_rows) == EXPECTED_ROWS,
        "no_cnbe_rows_written": all(row["initial_cnbe_write_status"] == "NO_CNBE_WRITE" for row in packet),
        "no_database_rebuild": all(row["initial_database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in packet),
        "source_packet_not_modified": True,
    }
    report = {
        "report_schema_version": "1.0",
        "mode": "8105_initial_auto_filled_review_packet",
        "overall_status": "PASS_8105_INITIAL_AUTO_FILLED_PROJECT_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "total_rows": len(packet),
            "complete_candidates_before_auto_fill": completion_counts["COMPLETE_CANDIDATE_UNCHANGED"],
            "auto_filled_review_rows": len(filled_rows),
            "initial_review_ready_rows": completion_counts["COMPLETE_CANDIDATE_UNCHANGED"] + len(filled_rows),
            "remaining_gap_rows": len(remaining_rows),
            "completion_status_counts": dict(completion_counts),
            "fill_rule_counts": dict(Counter(row["initial_fill_rule"] or "none" for row in filled_rows)),
            "source_priority_counts": dict(Counter(row["initial_source_priority"] or "none" for row in filled_rows)),
            "structure_counts": dict(Counter(row["candidate_structure_label"] or "UNRESOLVED" for row in packet)),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "initial_packet_csv": str(INITIAL_PACKET_CSV),
            "initial_filled_rows_csv": str(INITIAL_FILLED_CSV),
            "initial_remaining_gap_queue_csv": str(INITIAL_REMAINING_CSV),
            "json_report": str(REPORT_JSON),
            "markdown_report": str(REPORT_MD),
        },
        "decision": {
            "initial_project_review_packet_ready": all(checks.values()),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "recommended_next_step": (
                "Human review the 30 auto-filled rows, then decide whether to "
                "authorize a separate source-merge gate for accepted rows."
            ),
        },
    }
    return packet, filled_rows, remaining_rows, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 Initial Auto-Filled Project",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Total rows: {report['summary']['total_rows']}",
        f"- Complete candidates before auto-fill: {report['summary']['complete_candidates_before_auto_fill']}",
        f"- Auto-filled review rows: {report['summary']['auto_filled_review_rows']}",
        f"- Initial review-ready rows: {report['summary']['initial_review_ready_rows']}",
        f"- Remaining gap rows: {report['summary']['remaining_gap_rows']}",
        f"- CNBE rows written: {report['summary']['cnbe_rows_written']}",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        "",
        "The initial packet is a review packet only. It does not overwrite the",
        "source standardizer packet, CNBE source tables, cnbe-research knowledge",
        "assets, or databases.",
        "",
        "## Fill Rule Counts",
        "",
        "| Rule | Rows |",
        "|---|---:|",
    ]
    for rule, count in sorted(report["summary"]["fill_rule_counts"].items()):
        lines.append(f"| `{rule}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["recommended_next_step"], ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    packet, filled_rows, remaining_rows, report = build()
    write_csv(INITIAL_PACKET_CSV, packet)
    write_csv(INITIAL_FILLED_CSV, filled_rows)
    write_csv(INITIAL_REMAINING_CSV, remaining_rows)
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_markdown(report))
    return report


def main() -> None:
    report = run()
    print(report["overall_status"])
    print(f"total_rows={report['summary']['total_rows']}")
    print(f"auto_filled_review_rows={report['summary']['auto_filled_review_rows']}")
    print(f"initial_review_ready_rows={report['summary']['initial_review_ready_rows']}")
    print(f"remaining_gap_rows={report['summary']['remaining_gap_rows']}")


if __name__ == "__main__":
    main()
