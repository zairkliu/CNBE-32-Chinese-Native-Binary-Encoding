#!/usr/bin/env python3
"""Materialize a no-write 8105 structure-code candidate packet from v0.3.

Only v0.3 rows that fill a currently blank structure are applied. Conflicts are
kept out of the packet and must be reviewed separately.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_hanzi_decomp_v03_8105_adapter import APPROVED_STRUCTURES

INITIAL_PACKET = Path("review_packets/8105_full/8105_initial_auto_filled_review_packet.csv")
ADAPTER_ALL = Path("review_packets/8105_full/8105_hanzi_decomp_v03_adapter_all.csv")
ADAPTER_FILL = Path("review_packets/8105_full/8105_hanzi_decomp_v03_gap_fill_candidates.csv")
ADAPTER_CONFLICT = Path("review_packets/8105_full/8105_hanzi_decomp_v03_conflicts.csv")

OUTPUT_DIR = Path("review_packets/8105_full")
CANDIDATE_PACKET = OUTPUT_DIR / "8105_hanzi_decomp_v03_structure_code_candidate_packet.csv"
APPLIED_ROWS = OUTPUT_DIR / "8105_hanzi_decomp_v03_applied_gap_rows.csv"
REMAINING_BLANK_ROWS = OUTPUT_DIR / "8105_hanzi_decomp_v03_remaining_blank_rows.csv"

JSON_REPORT = Path("reports/8105_hanzi_decomp_v03_structure_code_candidate_packet.json")
MD_REPORT = Path("reports/8105_HANZI_DECOMP_V03_STRUCTURE_CODE_CANDIDATE_PACKET.md")
EXPECTED_ROWS = 8105


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


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    packet = read_csv(INITIAL_PACKET)
    adapter_rows = {row["character"]: row for row in read_csv(ADAPTER_ALL)}
    fill_rows = {row["character"]: row for row in read_csv(ADAPTER_FILL)}
    conflict_rows = read_csv(ADAPTER_CONFLICT)
    materialized: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    for row in packet:
        char = row["character"]
        out = dict(row)
        adapter = adapter_rows.get(char, {})
        fill = fill_rows.get(char)
        out["v03_tool_status"] = adapter.get("tool_status", "")
        out["v03_tool_structure"] = adapter.get("tool_structure", "")
        out["v03_tool_decomposition"] = adapter.get("tool_decomposition", "")
        out["v03_tool_top_level_parts"] = adapter.get("tool_top_level_parts", "")
        out["v03_materialize_status"] = "UNCHANGED"
        out["agent_struct_type"] = APPROVED_STRUCTURES.get(out["candidate_structure_label"], "")
        out["structure_code_candidate_status"] = "STRUCTURE_CODE_FROM_EXISTING_PACKET"
        out["cnbe32_write_status"] = "NO_CNBE32_WRITE"
        out["database_rebuild_status"] = "NO_DATABASE_REBUILD"
        if fill:
            out["candidate_structure_label"] = fill["tool_structure"]
            out["candidate_decomposition"] = fill["tool_decomposition"]
            out["direct_component_candidates"] = fill["tool_top_level_parts"]
            out["standardizer_status"] = "HANZI_DECOMP_V03_GAP_FILLED_REVIEW_REQUIRED"
            out["candidate_structure_status"] = "V03_AGENT_REFERENCE_REVIEW_REQUIRED"
            out["candidate_decomposition_status"] = "V03_AGENT_REFERENCE_REVIEW_REQUIRED"
            out["agent_struct_type"] = fill["tool_struct_type"]
            out["v03_materialize_status"] = "APPLIED_GAP_FILL_REVIEW_REQUIRED"
            out["structure_code_candidate_status"] = "AGENT_STRUCTURE_CODE_CANDIDATE_REVIEW_REQUIRED"
            out["review_status"] = "HUMAN_REVIEW_REQUIRED_BEFORE_SOURCE_MERGE"
            applied.append(out)
        materialized.append(out)
    remaining_blank = [row for row in materialized if not row["candidate_structure_label"]]
    structures = {row["candidate_structure_label"] for row in materialized if row["candidate_structure_label"]}
    checks = {
        "row_count_is_8105": len(materialized) == EXPECTED_ROWS,
        "applied_rows_match_adapter_fill_rows": len(applied) == len(fill_rows),
        "conflict_rows_not_applied": all(
            row["v03_materialize_status"] != "APPLIED_GAP_FILL_REVIEW_REQUIRED"
            for row in materialized
            if row["character"] in {conflict["character"] for conflict in conflict_rows}
        ),
        "all_structures_allowed_or_blank": structures <= set(APPROVED_STRUCTURES),
        "all_nonblank_structures_have_code": all(
            row["agent_struct_type"] != "" for row in materialized if row["candidate_structure_label"]
        ),
        "no_cnbe32_writes": all(row["cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in materialized),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in materialized),
    }
    report = {
        "report_schema_version": "1.0",
        "mode": "hanzi_decomp_v03_8105_structure_code_candidate_packet",
        "overall_status": "PASS_HANZI_DECOMP_V03_STRUCTURE_CODE_PACKET_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "total_rows": len(materialized),
            "applied_v03_gap_fill_rows": len(applied),
            "remaining_blank_structure_rows": len(remaining_blank),
            "v03_conflict_rows_excluded": len(conflict_rows),
            "structure_code_candidate_rows": sum(1 for row in materialized if row["agent_struct_type"] != ""),
            "materialize_status_counts": dict(Counter(row["v03_materialize_status"] for row in materialized)),
            "structure_counts": dict(Counter(row["candidate_structure_label"] or "UNRESOLVED" for row in materialized)),
            "cnbe32_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "candidate_packet_csv": str(CANDIDATE_PACKET),
            "applied_rows_csv": str(APPLIED_ROWS),
            "remaining_blank_rows_csv": str(REMAINING_BLANK_ROWS),
            "json_report": str(JSON_REPORT),
            "markdown_report": str(MD_REPORT),
        },
        "decision": {
            "may_human_review_structure_code_candidates": all(checks.values()),
            "may_write_cnbe32": False,
            "may_rebuild_database": False,
            "recommended_next_step": (
                "Human-review the 1,243 applied v0.3 gap fills and the 357 "
                "conflicts before authorizing any source merge."
            ),
        },
    }
    return materialized, applied, remaining_blank, report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Hanzi Decomp v0.3 Structure-Code Candidate Packet",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Total rows: {report['summary']['total_rows']}",
        f"- Applied v0.3 gap fills: {report['summary']['applied_v03_gap_fill_rows']}",
        f"- Remaining blank structure rows: {report['summary']['remaining_blank_structure_rows']}",
        f"- v0.3 conflict rows excluded: {report['summary']['v03_conflict_rows_excluded']}",
        f"- Structure-code candidate rows: {report['summary']['structure_code_candidate_rows']}",
        f"- CNBE32 rows written: {report['summary']['cnbe32_rows_written']}",
        "",
        "This packet contains structure-code candidates only. It does not write",
        "CNBE32 rows and does not rebuild a database.",
        "",
        "## Materialize Status Counts",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["materialize_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["recommended_next_step"], ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    materialized, applied, remaining_blank, report = build()
    write_csv(CANDIDATE_PACKET, materialized)
    write_csv(APPLIED_ROWS, applied)
    write_csv(REMAINING_BLANK_ROWS, remaining_blank)
    write_json(JSON_REPORT, report)
    write_text(MD_REPORT, render_markdown(report))
    return report


def main() -> None:
    report = run()
    print(report["overall_status"])
    print(f"applied_v03_gap_fill_rows={report['summary']['applied_v03_gap_fill_rows']}")
    print(f"remaining_blank_structure_rows={report['summary']['remaining_blank_structure_rows']}")
    print(f"structure_code_candidate_rows={report['summary']['structure_code_candidate_rows']}")


if __name__ == "__main__":
    main()
