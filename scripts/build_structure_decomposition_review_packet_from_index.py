#!/usr/bin/env python3
"""Build a bounded structure/decomposition review packet.

The packet references the existing 97,686-row repair report and exports only a
small deterministic review sample. It does not duplicate the full table, create
XLSX files, build databases, assign points, or emit final structure labels.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

AGENT_AUDIT = Path("reports/structure_decomposition_evidence_repair_agent_audit.json")
REPAIR_REPORT = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_review_packet_manifest.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_REVIEW_PACKET.md")
DEFAULT_CSV_OUTPUT = Path("reports/structure_decomposition_review_packet.csv")
EDITABLE_COPY_OUTPUT = Path("review_packets/structure_decomposition/structure_decomposition_review_packet_EDITABLE.csv")

MAX_ROWS_PER_QUEUE = 40
ALLOWED_STRUCTURE_LABELS = [
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
]
REVIEW_STATUS_VALUES = [
    "未审核",
    "证据可采纳",
    "证据不足",
    "需要查标准原文",
    "需要查字典/字源",
    "暂缓",
    "排除本轮",
]
CSV_COLUMNS = [
    "packet_id",
    "unicode",
    "char",
    "catalog_scope",
    "structure_evidence_status",
    "source_grade",
    "next_action",
    "phase1_status",
    "dictionary_review_status",
    "wiki_review_status",
    "feature_review_queue",
    "dictionary_source_count",
    "has_origin_context",
    "wiki_hit_count",
    "human_review_status",
    "human_structure_label",
    "human_decomposition",
    "human_component_note",
    "human_source_reference",
    "human_reviewer",
    "human_review_notes",
    "editable_copy_notice",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def schema_index(schema: list[str]) -> dict[str, int]:
    return {field: index for index, field in enumerate(schema)}


def packet_row(packet_id: str, unicode_label: str, row: list[Any], positions: dict[str, int]) -> dict[str, Any]:
    return {
        "packet_id": packet_id,
        "unicode": unicode_label,
        "char": row[positions["char"]],
        "catalog_scope": row[positions["catalog_scope"]],
        "structure_evidence_status": row[positions["structure_evidence_status"]],
        "source_grade": row[positions["source_grade"]],
        "next_action": row[positions["next_action"]],
        "phase1_status": row[positions["phase1_status"]],
        "dictionary_review_status": row[positions["dictionary_review_status"]],
        "wiki_review_status": row[positions["wiki_review_status"]],
        "feature_review_queue": row[positions["feature_review_queue"]],
        "dictionary_source_count": row[positions["dictionary_source_count"]],
        "has_origin_context": row[positions["has_origin_context"]],
        "wiki_hit_count": row[positions["wiki_hit_count"]],
        "human_review_status": "未审核",
        "human_structure_label": "",
        "human_decomposition": "",
        "human_component_note": "",
        "human_source_reference": "",
        "human_reviewer": "",
        "human_review_notes": "",
        "editable_copy_notice": "EDITABLE_COPY_ONLY_DO_NOT_TREAT_AS_SOURCE_EVIDENCE",
    }


def deterministic_packet_rows(repair: dict[str, Any]) -> list[dict[str, Any]]:
    positions = schema_index(repair["row_schema"])
    buckets: dict[str, list[tuple[str, list[Any]]]] = defaultdict(list)
    for unicode_label, row in repair["row_records"].items():
        status = row[positions["structure_evidence_status"]]
        buckets[status].append((unicode_label, row))

    packet_rows: list[dict[str, Any]] = []
    for status in sorted(buckets):
        rows = sorted(buckets[status], key=lambda item: int(item[0][2:], 16))
        for index, (unicode_label, row) in enumerate(rows[:MAX_ROWS_PER_QUEUE], start=1):
            packet_rows.append(packet_row(f"{status}_{index:03d}", unicode_label, row, positions))
    return packet_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_review_packet() -> dict[str, Any]:
    audit = load_json(AGENT_AUDIT)
    repair = load_json(REPAIR_REPORT)
    rows = deterministic_packet_rows(repair)
    status_counts = Counter(row["structure_evidence_status"] for row in rows)
    scope_counts = Counter(row["catalog_scope"] for row in rows)
    human_prefill_rows = [
        row["packet_id"]
        for row in rows
        if row["human_structure_label"] or row["human_decomposition"]
    ]
    checks = {
        "agent_audit_passed": audit["overall_status"]
        == "PASS_STRUCTURE_DECOMPOSITION_AGENT_AUDIT_READY_FOR_REVIEW_PACKET",
        "source_repair_report_passed": repair["overall_status"]
        == "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED",
        "packet_is_bounded_sample_not_full_table": len(rows) < repair["summary"]["total_rows"],
        "does_not_duplicate_97686_rows": len(rows) != 97_686,
        "does_not_generate_xlsx": True,
        "does_not_generate_database": True,
        "human_labels_blank_before_review": not human_prefill_rows,
        "score_values_assigned_zero": True,
        "final_structure_labels_emitted_zero": True,
    }
    status = "PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_structure_decomposition_review_packet",
        "overall_status": status,
        "next_workflow_status": "HUMAN_OR_AGENT_REVIEW_ALLOWED_NO_SCORING",
        "source_report_ref": audit["source_report"],
        "authority_boundary": {
            "references_existing_97686_report": True,
            "does_not_duplicate_full_97686_table": True,
            "does_not_create_xlsx": True,
            "does_not_create_database": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_rows": True,
        },
        "review_instructions": {
            "editable_copy_path": str(EDITABLE_COPY_OUTPUT),
            "editable_copy_rule": (
                "Only the EDITABLE copy may be modified during review. The source "
                "repair report remains read-only evidence."
            ),
            "allowed_structure_labels": ALLOWED_STRUCTURE_LABELS,
            "review_status_values": REVIEW_STATUS_VALUES,
            "unicode_first_rule": "Confirm char and Unicode before any structure/decomposition note.",
            "scoring_boundary": "Reviewer notes are evidence intake only and are not GF0017 scores.",
        },
        "summary": {
            "source_total_rows": repair["summary"]["total_rows"],
            "packet_rows": len(rows),
            "max_rows_per_queue": MAX_ROWS_PER_QUEUE,
            "packet_status_counts": dict(status_counts),
            "packet_scope_counts": dict(scope_counts),
            "human_label_prefill_count": len(human_prefill_rows),
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "full_table_duplicate_allowed": False,
            "database_generation_allowed": False,
            "xlsx_generation_allowed": False,
        },
        "checks": checks,
        "columns": CSV_COLUMNS,
        "packet_rows": rows,
        "outputs": {
            "manifest_json": str(DEFAULT_JSON_OUTPUT),
            "markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "canonical_csv": str(DEFAULT_CSV_OUTPUT),
            "editable_copy_csv": str(EDITABLE_COPY_OUTPUT),
        },
        "decision": {
            "may_start_human_or_agent_review": status.startswith("PASS"),
            "may_modify_editable_copy_only": status.startswith("PASS"),
            "may_modify_source_report": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "A bounded review packet is ready. It references the existing "
                "97,686-row source report and provides an explicitly marked "
                "editable copy for review notes only."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Review Packet",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Source report: `{report['source_report_ref']['path']}`",
        f"- Source SHA-256: `{report['source_report_ref']['sha256']}`",
        f"- Source total rows: {report['summary']['source_total_rows']}",
        f"- Packet rows: {report['summary']['packet_rows']}",
        f"- Editable copy: `{report['outputs']['editable_copy_csv']}`",
        f"- Full table duplicate allowed: `{report['summary']['full_table_duplicate_allowed']}`",
        f"- Database generation allowed: `{report['summary']['database_generation_allowed']}`",
        f"- XLSX generation allowed: `{report['summary']['xlsx_generation_allowed']}`",
        "",
        "The packet is a bounded review surface. It does not duplicate the full",
        "97,686-row table, create a database, assign GF0017 points, or emit final",
        "structure labels.",
        "",
        "## Packet Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["packet_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Editing Rule", "", report["review_instructions"]["editable_copy_rule"], ""])
    lines.extend(["## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_review_packet()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, report["packet_rows"])
    EDITABLE_COPY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEFAULT_CSV_OUTPUT, EDITABLE_COPY_OUTPUT)
    print(report["overall_status"])
    print(f"packet_rows={report['summary']['packet_rows']}")
    print(f"editable_copy={EDITABLE_COPY_OUTPUT}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
