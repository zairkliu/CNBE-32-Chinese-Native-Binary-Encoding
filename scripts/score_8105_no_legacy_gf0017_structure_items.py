#!/usr/bin/env python3
"""Score GF0017 structure-related items for the corrected 8105 pilot packet.

This scorer depends on the no-legacy packet audit. It assigns only items that
are supported by the corrected standardizer packet:

- existing coverage and stroke-order points are preserved from the partial
  scoring packet;
- component validity, radical validity, and structure-first decomposition may
  be added when national-standard candidate evidence is complete;
- stroke shape, component names, and independent-character rules stay blocked.

The script is read-only with respect to CNBE source rows and databases.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_8105_no_legacy_standardizer_packet import build_audit

PACKET_CSV = Path("review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.csv")
PARTIAL_SCORE_CSV = Path("review_packets/300_character_8105_pilot/8105_core_pilot_gf0017_partial_scoring.csv")
JSON_OUTPUT = Path("reports/8105_no_legacy_gf0017_structure_item_scoring.json")
MARKDOWN_OUTPUT = Path("reports/8105_NO_LEGACY_GF0017_STRUCTURE_ITEM_SCORING.md")
SCORED_CSV = Path("review_packets/300_character_8105_pilot/8105_no_legacy_gf0017_structure_item_scoring.csv")

EXPECTED_ROWS = 100
FORMAL_TOTAL = 50
EXISTING_MAX = 6
COMPONENT_VALIDITY_POINTS = 3
RADICAL_VALIDITY_POINTS = 3
STRUCTURE_DECOMPOSITION_POINTS = 20


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
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def can_score_structure_items(row: dict[str, str]) -> bool:
    return (
        row["standard_evidence_status"] == "COMPLETE"
        and bool(row["candidate_structure_label"])
        and bool(row["candidate_decomposition"])
        and bool(row["direct_component_candidates"])
        and bool(row["radical"])
        and row["candidate_structure_status"] == "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
        and row["candidate_decomposition_status"] == "NATIONAL_STANDARD_CANDIDATE_REVIEW_REQUIRED"
    )


def build_scored_rows() -> list[dict[str, Any]]:
    audit_report, _recheck_rows = build_audit()
    if audit_report["overall_status"] != "PASS_8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT":
        raise RuntimeError("no-legacy packet audit must pass before scoring")

    packet_rows = read_csv(PACKET_CSV)
    partial_scores = {
        row["row_id"]: row
        for row in read_csv(PARTIAL_SCORE_CSV)
    }
    if len(packet_rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} packet rows, got {len(packet_rows)}")

    scored_rows: list[dict[str, Any]] = []
    for row in packet_rows:
        row_id = row["row_id"]
        partial = partial_scores[row_id]
        existing_score = int(partial["assigned_score"])
        structure_items_ready = can_score_structure_items(row)
        component_validity_score = COMPONENT_VALIDITY_POINTS if structure_items_ready else 0
        radical_validity_score = RADICAL_VALIDITY_POINTS if structure_items_ready else 0
        structure_decomposition_score = STRUCTURE_DECOMPOSITION_POINTS if structure_items_ready else 0
        newly_assigned_score = (
            component_validity_score
            + radical_validity_score
            + structure_decomposition_score
        )
        assigned_score = existing_score + newly_assigned_score
        remaining_blocked_items = [
            "stroke_shape",
            "component_name_validity",
            "independent_character_rule",
        ]
        if not structure_items_ready:
            remaining_blocked_items.extend([
                "component_validity",
                "radical_validity",
                "structure_first_decomposition",
            ])
        scored_rows.append({
            "row_id": row_id,
            "character": row["character"],
            "unicode_codepoint": row["unicode_codepoint"],
            "scope": row["scope"],
            "candidate_structure_label": row["candidate_structure_label"],
            "candidate_decomposition": row["candidate_decomposition"],
            "direct_component_candidates": row["direct_component_candidates"],
            "radical": row["radical"],
            "standard_evidence_status": row["standard_evidence_status"],
            "existing_score": existing_score,
            "existing_max": EXISTING_MAX,
            "component_validity_score": component_validity_score,
            "component_validity_status": (
                "PASS_NATIONAL_STANDARD_COMPONENT_CANDIDATE"
                if structure_items_ready
                else "NOT_SCORABLE_COMPONENT_EVIDENCE_GAP"
            ),
            "radical_validity_score": radical_validity_score,
            "radical_validity_status": (
                "PASS_NATIONAL_STANDARD_RADICAL_CANDIDATE"
                if structure_items_ready
                else "NOT_SCORABLE_RADICAL_EVIDENCE_GAP"
            ),
            "structure_first_decomposition_score": structure_decomposition_score,
            "structure_first_decomposition_status": (
                "PASS_NATIONAL_STANDARD_STRUCTURE_DECOMPOSITION_CANDIDATE"
                if structure_items_ready
                else "NOT_SCORABLE_STRUCTURE_DECOMPOSITION_EVIDENCE_GAP"
            ),
            "newly_assigned_score": newly_assigned_score,
            "assigned_score": assigned_score,
            "formal_total": FORMAL_TOTAL,
            "row_score_status": (
                "STRUCTURE_ITEMS_SCORED_REMAINING_ITEMS_BLOCKED"
                if structure_items_ready
                else "PARTIAL_SCORE_ONLY_REMAINING_STRUCTURE_ITEMS_BLOCKED"
            ),
            "remaining_blocked_items": ";".join(remaining_blocked_items),
            "cnbe_write_status": "NO_CNBE_WRITE",
            "database_rebuild_status": "NO_DATABASE_REBUILD",
            "review_notice": "GF0017_STRUCTURE_ITEM_SCORING_ONLY_NOT_ENCODING",
        })
    return scored_rows


def build_report(scored_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_with_structure_score = sum(1 for row in scored_rows if row["newly_assigned_score"])
    checks = {
        "row_count_is_100": len(scored_rows) == EXPECTED_ROWS,
        "no_legacy_packet_audit_passed": build_audit()[0]["overall_status"] == "PASS_8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT",
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in scored_rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in scored_rows),
        "component_names_remain_blocked": all("component_name_validity" in row["remaining_blocked_items"] for row in scored_rows),
        "independent_character_rule_remains_blocked": all("independent_character_rule" in row["remaining_blocked_items"] for row in scored_rows),
        "stroke_shape_remains_blocked": all("stroke_shape" in row["remaining_blocked_items"] for row in scored_rows),
    }
    overall_status = "PASS_8105_NO_LEGACY_GF0017_STRUCTURE_ITEM_SCORING" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "no_legacy_8105_gf0017_structure_item_scoring",
        "overall_status": overall_status,
        "next_workflow_status": "READY_FOR_HUMAN_REVIEW_BEFORE_COMPONENT_NAME_AND_INDEPENDENT_RULE_SCORING",
        "summary": {
            "scored_rows": len(scored_rows),
            "rows_with_structure_item_score": rows_with_structure_score,
            "rows_without_structure_item_score": len(scored_rows) - rows_with_structure_score,
            "score_counts": dict(Counter(str(row["assigned_score"]) for row in scored_rows)),
            "row_score_status_counts": dict(Counter(row["row_score_status"] for row in scored_rows)),
            "new_points_per_complete_row": COMPONENT_VALIDITY_POINTS + RADICAL_VALIDITY_POINTS + STRUCTURE_DECOMPOSITION_POINTS,
            "max_assigned_score": max(row["assigned_score"] for row in scored_rows),
            "min_assigned_score": min(row["assigned_score"] for row in scored_rows),
            "cnbe_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MARKDOWN_OUTPUT),
            "scored_csv": str(SCORED_CSV),
        },
        "decision": {
            "may_review_structure_item_scores": overall_status.startswith("PASS"),
            "may_score_component_names": False,
            "may_score_independent_character_rule": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Structure-related GF0017 items are scored only where the "
                "corrected no-legacy packet has complete national-standard "
                "candidate evidence. Component names, independent-character "
                "rules, and stroke-shape scoring remain blocked."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 No-Legacy GF0017 Structure Item Scoring",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
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
    lines.extend([
        "",
        "## Still Blocked",
        "",
        "- stroke shape",
        "- component name validity",
        "- independent-character rule",
        "- CNBE row writes",
        "- SQLite database rebuild",
        "",
        "## Decision",
        "",
        report["decision"]["reason"],
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    scored_rows = build_scored_rows()
    report = build_report(scored_rows)
    write_csv(SCORED_CSV, scored_rows)
    write_json(JSON_OUTPUT, report)
    write_text(MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"scored_rows={report['summary']['scored_rows']}")
    print(f"rows_with_structure_item_score={report['summary']['rows_with_structure_item_score']}")
    print(f"score_counts={report['summary']['score_counts']}")


if __name__ == "__main__":
    main()
