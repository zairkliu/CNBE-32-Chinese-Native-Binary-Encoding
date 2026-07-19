#!/usr/bin/env python3
"""Audit the corrected 8105 standardizer packet for no-legacy structure use."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

PACKET_CSV = Path("review_packets/300_character_8105_pilot/8105_core_bounded_standardizer_review_packet.csv")
ENCODING_COMPARISON = Path("evidence/8105/cnbe8105_encoding_comparison.json")
JSON_OUTPUT = Path("reports/8105_no_legacy_standardizer_packet_audit.json")
MARKDOWN_OUTPUT = Path("reports/8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT.md")
HUMAN_RECHECK_CSV = Path("review_packets/300_character_8105_pilot/8105_no_legacy_human_recheck_packet.csv")

EXPECTED_ROWS = 100
REGRESSION_CHARS = {
    "侵": ("左右", "⿰亻⿳彐冖又"),
    "偶": ("左右", "⿰亻禺"),
    "冁": ("左右", "⿰单展"),
}
FORBIDDEN_PACKET_FIELDS = {"legacy_cnbe32", "legacy_structure_label"}
FORBIDDEN_POLLUTION_VALUES = {"右下包"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
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


def candidate_matches_standard(row: dict[str, str], standard: dict[str, Any]) -> bool:
    expected_structure = standard.get("structure") or ""
    expected_decomposition = standard.get("decomposition") or ""
    if expected_structure and row["candidate_structure_label"] != expected_structure:
        return False
    if expected_decomposition and row["candidate_decomposition"] != expected_decomposition:
        return False
    return True


def build_human_recheck_rows(rows: list[dict[str, str]], mismatch_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[str, dict[str, str]] = {}
    for row in mismatch_rows:
        selected[row["row_id"]] = row
    for char in REGRESSION_CHARS:
        for row in rows:
            if row["character"] == char:
                selected[row["row_id"]] = row
    for row in rows:
        if row["candidate_status"] == "STANDARDIZER_EVIDENCE_GAP":
            selected[row["row_id"]] = row
    seen_structure: set[str] = set()
    for row in rows:
        label = row["candidate_structure_label"] or "UNRESOLVED"
        if label not in seen_structure:
            selected[row["row_id"]] = row
            seen_structure.add(label)
    return sorted(selected.values(), key=lambda row: row["row_id"])


def build_audit() -> tuple[dict[str, Any], list[dict[str, str]]]:
    fieldnames, rows = read_csv(PACKET_CSV)
    comparison = load_json(ENCODING_COMPARISON)["characters"]
    forbidden_fields = sorted(set(fieldnames) & FORBIDDEN_PACKET_FIELDS)
    pollution_hits: list[dict[str, str]] = []
    mismatch_rows: list[dict[str, str]] = []
    regression_failures: list[dict[str, str]] = []

    for row in rows:
        char = row["character"]
        standard = comparison.get(char, {}).get("standard", {})
        if not candidate_matches_standard(row, standard):
            mismatch_rows.append({
                "row_id": row["row_id"],
                "character": char,
                "candidate_structure_label": row["candidate_structure_label"],
                "standard_structure": standard.get("structure", ""),
                "candidate_decomposition": row["candidate_decomposition"],
                "standard_decomposition": standard.get("decomposition", ""),
            })
        for field, value in row.items():
            if value in FORBIDDEN_POLLUTION_VALUES:
                pollution_hits.append({
                    "row_id": row["row_id"],
                    "character": char,
                    "field": field,
                    "value": value,
                })
        if char in REGRESSION_CHARS:
            expected_structure, expected_decomposition = REGRESSION_CHARS[char]
            if (
                row["candidate_structure_label"] != expected_structure
                or row["candidate_decomposition"] != expected_decomposition
            ):
                regression_failures.append({
                    "row_id": row["row_id"],
                    "character": char,
                    "candidate_structure_label": row["candidate_structure_label"],
                    "candidate_decomposition": row["candidate_decomposition"],
                })

    recheck_rows = build_human_recheck_rows(rows, mismatch_rows)
    checks = {
        "row_count_is_100": len(rows) == EXPECTED_ROWS,
        "no_forbidden_legacy_fields": not forbidden_fields,
        "no_forbidden_pollution_values": not pollution_hits,
        "all_candidates_match_standard_evidence": not mismatch_rows,
        "regression_chars_match_corrected_structures": not regression_failures,
        "no_cnbe_rows_written": all(row["cnbe_write_status"] == "NO_CNBE_WRITE" for row in rows),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in rows),
        "no_new_gf0017_points": all(row["gf0017_new_points_assigned"] == "0" for row in rows),
    }
    overall_status = "PASS_8105_NO_LEGACY_STANDARDIZER_PACKET_AUDIT" if all(checks.values()) else "BLOCKED"
    report = {
        "report_schema_version": "1.0",
        "mode": "no_legacy_8105_standardizer_packet_audit",
        "overall_status": overall_status,
        "next_workflow_status": "READY_FOR_HUMAN_RECHECK_PACKET_REVIEW" if overall_status.startswith("PASS") else "BLOCKED_FIX_PACKET",
        "summary": {
            "packet_rows": len(rows),
            "human_recheck_rows": len(recheck_rows),
            "structure_counts": dict(Counter(row["candidate_structure_label"] or "UNRESOLVED" for row in rows)),
            "candidate_status_counts": dict(Counter(row["candidate_status"] for row in rows)),
            "forbidden_field_count": len(forbidden_fields),
            "pollution_hit_count": len(pollution_hits),
            "candidate_standard_mismatch_count": len(mismatch_rows),
            "regression_failure_count": len(regression_failures),
        },
        "checks": checks,
        "forbidden_fields": forbidden_fields,
        "pollution_hits": pollution_hits,
        "candidate_standard_mismatches": mismatch_rows,
        "regression_failures": regression_failures,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MARKDOWN_OUTPUT),
            "human_recheck_csv": str(HUMAN_RECHECK_CSV),
        },
        "decision": {
            "may_start_human_recheck": overall_status.startswith("PASS"),
            "may_assign_gf0017_structure_points": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The packet is clean enough for human recheck only. GF0017 "
                "structure scoring and CNBE writes remain blocked until human "
                "review confirms the corrected structure candidates."
            ),
        },
    }
    return report, recheck_rows


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 8105 No-Legacy Standardizer Packet Audit",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Packet rows: {report['summary']['packet_rows']}",
        f"- Human recheck rows: {report['summary']['human_recheck_rows']}",
        f"- Forbidden legacy fields: {report['summary']['forbidden_field_count']}",
        f"- Forbidden pollution hits: {report['summary']['pollution_hit_count']}",
        f"- Candidate/standard mismatches: {report['summary']['candidate_standard_mismatch_count']}",
        f"- Regression failures: {report['summary']['regression_failure_count']}",
        "",
        "## Structure Counts",
        "",
        "| Structure | Count |",
        "|---|---:|",
    ]
    for label, count in sorted(report["summary"]["structure_counts"].items()):
        lines.append(f"| `{label}` | {count} |")
    lines.extend([
        "",
        "## Decision",
        "",
        report["decision"]["reason"],
        "",
        "## Outputs",
        "",
        f"- Human recheck CSV: `{report['outputs']['human_recheck_csv']}`",
        f"- JSON report: `{report['outputs']['json_report']}`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    report, recheck_rows = build_audit()
    write_json(JSON_OUTPUT, report)
    write_text(MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(HUMAN_RECHECK_CSV, recheck_rows)
    print(report["overall_status"])
    print(f"packet_rows={report['summary']['packet_rows']}")
    print(f"human_recheck_rows={report['summary']['human_recheck_rows']}")
    print(f"mismatches={report['summary']['candidate_standard_mismatch_count']}")


if __name__ == "__main__":
    main()
