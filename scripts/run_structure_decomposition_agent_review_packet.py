#!/usr/bin/env python3
"""Run Agent review on the bounded structure/decomposition review packet.

The review writes a new AGENT_REVIEWED_EDITABLE copy. It does not edit the
canonical packet, the original EDITABLE copy, or the 97,686-row source report.
It also does not assign scores or final structure/decomposition labels.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

PACKET_MANIFEST = Path("reports/structure_decomposition_review_packet_manifest.json")
CANONICAL_PACKET = Path("reports/structure_decomposition_review_packet.csv")
ORIGINAL_EDITABLE = Path("review_packets/structure_decomposition/structure_decomposition_review_packet_EDITABLE.csv")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_agent_review_result.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_AGENT_REVIEW_RESULT.md")
AGENT_REVIEWED_EDITABLE = Path(
    "review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_EDITABLE.csv"
)

AGENT_REVIEWER = "CNBE Agent Review v1"


REVIEW_RULES = {
    "CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED": {
        "agent_review_status": "STANDARD_JOIN_REQUIRED",
        "human_review_status": "需要查标准原文",
        "review_class": "8105_core_standard_join",
        "note": (
            "8105 core row needs standard-derived structure/decomposition join before "
            "any GF0017 structure score or final structure label."
        ),
        "blocks_scoring": True,
    },
    "STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY": {
        "agent_review_status": "READY_FOR_HUMAN_ADJUDICATION",
        "human_review_status": "证据可采纳",
        "review_class": "context_ready_for_adjudication",
        "note": (
            "Review context is available. Treat it as adjudication input only; "
            "do not promote it to a final label without merge-and-audit."
        ),
        "blocks_scoring": True,
    },
    "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED": {
        "agent_review_status": "PARTIAL_REPAIR_REQUIRED",
        "human_review_status": "需要查标准原文",
        "review_class": "partial_context_needs_repair",
        "note": "Partial structure/decomposition context needs source repair before scoring.",
        "blocks_scoring": True,
    },
    "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT": {
        "agent_review_status": "DICTIONARY_CONTEXT_CHECK_REQUIRED",
        "human_review_status": "需要查字典/字源",
        "review_class": "dictionary_context_only",
        "note": "Dictionary context may guide review but is not direct GF0017 structure authority.",
        "blocks_scoring": True,
    },
    "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT": {
        "agent_review_status": "REVIEW_CONTEXT_SOURCE_CHECK_REQUIRED",
        "human_review_status": "需要查字典/字源",
        "review_class": "cross_reference_context_only",
        "note": "Cross-reference context exists; verify against standards before any final label.",
        "blocks_scoring": True,
    },
    "STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY": {
        "agent_review_status": "AGENT_STANDARD_QUEUE_REVIEW_REQUIRED",
        "human_review_status": "暂缓",
        "review_class": "agent_standard_queue_only",
        "note": (
            "No direct structure evidence in packet. Keep as Agent-standard queue "
            "candidate, not national-standard output."
        ),
        "blocks_scoring": True,
    },
}


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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def review_row(row: dict[str, str], source_sha: str) -> dict[str, str]:
    reviewed = dict(row)
    rule = REVIEW_RULES[row["structure_evidence_status"]]
    reviewed["human_review_status"] = rule["human_review_status"]
    reviewed["human_structure_label"] = ""
    reviewed["human_decomposition"] = ""
    reviewed["human_component_note"] = rule["review_class"]
    reviewed["human_source_reference"] = f"source_sha256:{source_sha};next_action:{row['next_action']}"
    reviewed["human_reviewer"] = AGENT_REVIEWER
    reviewed["human_review_notes"] = (
        f"{rule['agent_review_status']}: {rule['note']} "
        "No GF0017 points or final structure label assigned."
    )
    reviewed["editable_copy_notice"] = "AGENT_REVIEWED_EDITABLE_COPY_NOT_SOURCE_EVIDENCE"
    return reviewed


def run_agent_review() -> dict[str, Any]:
    manifest = load_json(PACKET_MANIFEST)
    fieldnames, rows = read_csv(CANONICAL_PACKET)
    _editable_fieldnames, editable_rows = read_csv(ORIGINAL_EDITABLE)
    source_sha = manifest["source_report_ref"]["sha256"]

    reviewed_rows = [review_row(row, source_sha) for row in rows]
    status_counts = Counter(row["human_review_status"] for row in reviewed_rows)
    review_class_counts = Counter(row["human_component_note"] for row in reviewed_rows)
    source_status_counts = Counter(row["structure_evidence_status"] for row in reviewed_rows)
    forbidden_label_rows = [
        row["packet_id"]
        for row in reviewed_rows
        if row["human_structure_label"] or row["human_decomposition"]
    ]
    checks = {
        "packet_manifest_passed": manifest["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY",
        "uses_bounded_packet_only": len(rows) == manifest["summary"]["packet_rows"],
        "does_not_read_or_duplicate_full_97686_table": True,
        "original_editable_row_count_unchanged": len(editable_rows) == len(rows),
        "agent_reviewed_copy_is_separate": AGENT_REVIEWED_EDITABLE != ORIGINAL_EDITABLE,
        "no_final_structure_labels_written": not forbidden_label_rows,
        "no_gf0017_points_assigned": True,
        "no_database_generated": True,
        "no_xlsx_generated": True,
    }
    status = "PASS_STRUCTURE_DECOMPOSITION_AGENT_REVIEW_COMPLETED_NO_SCORING" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_structure_decomposition_agent_review",
        "overall_status": status,
        "next_workflow_status": "AGENT_REVIEW_READY_FOR_HUMAN_DECISION_OR_MERGE_PLAN",
        "authority_boundary": {
            "uses_bounded_packet_only": True,
            "does_not_duplicate_full_97686_table": True,
            "does_not_modify_source_report": True,
            "does_not_modify_original_editable_copy": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "summary": {
            "reviewed_rows": len(reviewed_rows),
            "source_total_rows": manifest["summary"]["source_total_rows"],
            "human_review_status_counts": dict(status_counts),
            "agent_review_class_counts": dict(review_class_counts),
            "source_structure_status_counts": dict(source_status_counts),
            "final_structure_labels_written": 0,
            "gf0017_points_assigned": 0,
            "full_table_duplicate_allowed": False,
            "database_generation_allowed": False,
            "xlsx_generation_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "agent_review_json": str(DEFAULT_JSON_OUTPUT),
            "agent_review_markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "agent_reviewed_editable_csv": str(AGENT_REVIEWED_EDITABLE),
        },
        "review_rules": REVIEW_RULES,
        "decision": {
            "may_start_human_decision_or_merge_plan": status.startswith("PASS"),
            "may_modify_agent_reviewed_editable_copy": status.startswith("PASS"),
            "may_modify_source_report": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Agent review completed on the bounded packet. The reviewed copy "
                "contains triage notes only and must not be treated as source "
                "evidence until a later merge-and-audit gate."
            ),
        },
        "reviewed_rows": reviewed_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Agent Review Result",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Reviewed rows: {report['summary']['reviewed_rows']}",
        f"- Source total rows referenced: {report['summary']['source_total_rows']}",
        f"- Agent reviewed editable copy: `{report['outputs']['agent_reviewed_editable_csv']}`",
        f"- Full table duplicate allowed: `{report['summary']['full_table_duplicate_allowed']}`",
        f"- Database generation allowed: `{report['summary']['database_generation_allowed']}`",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels written: {report['summary']['final_structure_labels_written']}",
        "",
        "The Agent reviewed the bounded packet only. It did not duplicate the",
        "97,686-row source report, generate XLSX, build a database, assign scores,",
        "or write final structure labels.",
        "",
        "## Review Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["human_review_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Agent Review Classes", "", "| Class | Count |", "|---|---:|"])
    for review_class, count in sorted(report["summary"]["agent_review_class_counts"].items()):
        lines.append(f"| `{review_class}` | {count} |")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = run_agent_review()
    reviewed_rows = report.pop("reviewed_rows")
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    fieldnames, _rows = read_csv(CANONICAL_PACKET)
    write_csv(AGENT_REVIEWED_EDITABLE, fieldnames, reviewed_rows)
    print(report["overall_status"])
    print(f"reviewed_rows={report['summary']['reviewed_rows']}")
    print(f"agent_reviewed_copy={AGENT_REVIEWED_EDITABLE}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
