#!/usr/bin/env python3
"""Apply ZDIC lookup references to the Agent-reviewed editable packet copy."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ZDIC_MANIFEST = Path("reports/zdic_reference_snapshot_manifest.json")
AGENT_REVIEWED_PACKET = Path(
    "review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_EDITABLE.csv"
)
ZDIC_ENHANCED_PACKET = Path(
    "review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_ZDIC_EDITABLE.csv"
)
DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_agent_review_zdic_enhancement.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_AGENT_REVIEW_ZDIC_ENHANCEMENT.md")


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


def build_enhancement() -> dict[str, Any]:
    manifest = load_json(ZDIC_MANIFEST)
    fieldnames, rows = read_csv(AGENT_REVIEWED_PACKET)
    zdic_by_unicode = {row["unicode"]: row for row in manifest["lookup_rows"]}
    snapshot_by_unicode = {row["unicode"]: row for row in manifest["snapshot_records"]}
    enhanced_rows: list[dict[str, str]] = []
    for row in rows:
        enhanced = dict(row)
        zdic = zdic_by_unicode[row["unicode"]]
        snapshot = snapshot_by_unicode.get(row["unicode"])
        snapshot_note = ""
        if snapshot and snapshot["snapshot_available"]:
            snapshot_note = f";zdic_snapshot:{snapshot['dom_snapshot_path']}"
        enhanced["human_source_reference"] = (
            f"{enhanced['human_source_reference']};zdic:{zdic['zdic_url']}{snapshot_note}"
        )
        enhanced["human_review_notes"] = (
            f"{enhanced['human_review_notes']} ZDIC reference added as online cross-reference only."
        )
        enhanced["editable_copy_notice"] = "AGENT_REVIEWED_ZDIC_EDITABLE_COPY_NOT_SOURCE_EVIDENCE"
        enhanced_rows.append(enhanced)

    checks = {
        "zdic_manifest_passed": manifest["overall_status"] == "PASS_ZDIC_REFERENCE_SNAPSHOT_MANIFEST_READY",
        "row_count_matches_manifest": len(enhanced_rows) == manifest["summary"]["packet_rows"],
        "all_rows_have_zdic_url": all(";zdic:https://www.zdic.net/hans/" in row["human_source_reference"] for row in enhanced_rows),
        "does_not_modify_source_report": True,
        "does_not_modify_original_agent_reviewed_copy": True,
        "does_not_assign_points": True,
        "does_not_emit_final_labels": True,
        "does_not_create_database": True,
    }
    status = "PASS_AGENT_REVIEW_ZDIC_REFERENCES_APPLIED" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_agent_review_zdic_reference_enhancement",
        "overall_status": status,
        "next_workflow_status": "ZDIC_ENHANCED_REVIEW_COPY_READY_NOT_SOURCE_EVIDENCE",
        "authority_boundary": {
            "zdic_cross_reference_only": True,
            "does_not_promote_zdic_to_national_standard": True,
            "does_not_modify_source_report": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "summary": {
            "enhanced_rows": len(enhanced_rows),
            "snapshot_references_available": manifest["summary"]["captured_snapshot_rows"],
            "packet_snapshot_references_available": manifest["summary"]["captured_packet_snapshot_rows"],
            "gf0017_points_assigned": 0,
            "final_structure_labels_emitted": 0,
            "database_generation_allowed": False,
        },
        "checks": checks,
        "outputs": {
            "enhancement_json": str(DEFAULT_JSON_OUTPUT),
            "enhancement_markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "zdic_enhanced_editable_csv": str(ZDIC_ENHANCED_PACKET),
        },
        "decision": {
            "may_use_zdic_enhanced_copy_for_review": status.startswith("PASS"),
            "may_promote_zdic_to_national_standard": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "ZDIC references were added to a separate reviewed editable copy. "
                "They are online cross-reference context only."
            ),
        },
        "enhanced_rows": enhanced_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Agent Review ZDIC Enhancement",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Enhanced rows: {report['summary']['enhanced_rows']}",
        f"- Snapshot references available: {report['summary']['snapshot_references_available']}",
        f"- Packet snapshot references available: {report['summary']['packet_snapshot_references_available']}",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        f"- Output: `{report['outputs']['zdic_enhanced_editable_csv']}`",
        "",
        "ZDIC references are online cross-reference context only. They are not",
        "national-standard evidence, GF0017 points, final labels, CNBE rows, or",
        "database records.",
        "",
        "## Decision",
        "",
        report["decision"]["reason"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    report = build_enhancement()
    enhanced_rows = report.pop("enhanced_rows")
    fieldnames, _rows = read_csv(AGENT_REVIEWED_PACKET)
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(ZDIC_ENHANCED_PACKET, fieldnames, enhanced_rows)
    print(report["overall_status"])
    print(f"enhanced_rows={report['summary']['enhanced_rows']}")
    print(f"output={ZDIC_ENHANCED_PACKET}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
