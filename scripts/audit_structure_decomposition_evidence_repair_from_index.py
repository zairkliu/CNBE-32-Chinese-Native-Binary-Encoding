#!/usr/bin/env python3
"""Audit structure/decomposition evidence repair before review-packet export."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPAIR_REPORT = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")
DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_evidence_repair_agent_audit.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_AGENT_AUDIT.md")

EXPECTED_ROWS = 97_686
EXPECTED_8105_ROWS = 8_105
REQUIRED_STATUSES = {
    "CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED",
    "STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY",
    "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED",
    "STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY",
    "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT",
    "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_index(schema: list[str]) -> dict[str, int]:
    return {field: index for index, field in enumerate(schema)}


def audit_repair_report() -> dict[str, Any]:
    report = load_json(REPAIR_REPORT)
    positions = schema_index(report["row_schema"])
    row_records = report["row_records"]

    status_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    malformed_rows: list[str] = []
    forbidden_score_rows: list[str] = []

    for unicode_label, row in row_records.items():
        if not isinstance(row, list) or len(row) != len(report["row_schema"]):
            malformed_rows.append(unicode_label)
            continue
        status_counts[row[positions["structure_evidence_status"]]] += 1
        scope_counts[row[positions["catalog_scope"]]] += 1
        if "score" in row or "final_structure_label" in row:
            forbidden_score_rows.append(unicode_label)

    checks = {
        "repair_report_passed": report["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED",
        "row_count_match": len(row_records) == EXPECTED_ROWS,
        "scope_8105_count_match": scope_counts["8105_core"] == EXPECTED_8105_ROWS,
        "required_statuses_present": REQUIRED_STATUSES <= set(status_counts),
        "malformed_rows_zero": not malformed_rows,
        "forbidden_score_rows_zero": not forbidden_score_rows,
        "report_blocks_scoring": report["summary"]["formal_scoring_allowed"] is False,
        "report_blocks_cnbe_writes": report["summary"]["cnbe_row_write_allowed"] is False,
        "report_blocks_database_rebuild": report["summary"]["database_rebuild_allowed"] is False,
        "score_values_assigned_zero": report["summary"]["score_values_assigned"] == 0,
        "final_structure_labels_emitted_zero": report["summary"]["final_structure_labels_emitted"] == 0,
    }
    status = "PASS_STRUCTURE_DECOMPOSITION_AGENT_AUDIT_READY_FOR_REVIEW_PACKET" if all(checks.values()) else "BLOCKED"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_structure_decomposition_evidence_repair_agent_audit",
        "overall_status": status,
        "next_workflow_status": "STRUCTURE_DECOMPOSITION_REVIEW_PACKET_ALLOWED_NO_FULL_TABLE_DUPLICATION",
        "source_report": {
            "path": str(REPAIR_REPORT),
            "sha256": sha256_file(REPAIR_REPORT),
            "row_count": len(row_records),
        },
        "summary": {
            "total_rows": len(row_records),
            "scope_counts": dict(scope_counts),
            "status_counts": dict(status_counts),
            "malformed_row_sample_count": len(malformed_rows),
            "forbidden_score_row_sample_count": len(forbidden_score_rows),
            "may_generate_review_packet": status.startswith("PASS"),
            "may_duplicate_full_97686_table": False,
            "may_generate_database": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
        },
        "checks": checks,
        "issue_samples": {
            "malformed_rows": malformed_rows[:20],
            "forbidden_score_rows": forbidden_score_rows[:20],
        },
        "decision": {
            "may_generate_bounded_review_packet": status.startswith("PASS"),
            "may_generate_full_table_or_database": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "reason": (
                "Agent audit passed. The next packet must reference the existing "
                "97,686-row evidence report instead of duplicating it."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Evidence Repair Agent Audit",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Source report: `{report['source_report']['path']}`",
        f"- Source SHA-256: `{report['source_report']['sha256']}`",
        f"- Total rows audited: {report['summary']['total_rows']}",
        f"- May generate review packet: `{report['summary']['may_generate_review_packet']}`",
        f"- May duplicate full 97,686 table: `{report['summary']['may_duplicate_full_97686_table']}`",
        f"- May generate database: `{report['summary']['may_generate_database']}`",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---:|",
    ]
    for check, value in sorted(report["checks"].items()):
        lines.append(f"| `{check}` | `{value}` |")
    lines.extend(["", "## Status Counts", "", "| Status | Count |", "|---|---:|"])
    for status, count in sorted(report["summary"]["status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    report = audit_repair_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"rows={report['summary']['total_rows']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
