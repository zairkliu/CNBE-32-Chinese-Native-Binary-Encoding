#!/usr/bin/env python3
"""Build a zdic reference manifest for the bounded review packet.

The manifest records lookup URLs for the 212-row packet and browser-captured
snapshot files for representative rows. It does not scrape the full 97,686-row
table, build a database, assign GF0017 points, or promote zdic content to
national-standard authority.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

PACKET_MANIFEST = Path("reports/structure_decomposition_review_packet_manifest.json")
AGENT_REVIEW_RESULT = Path("reports/structure_decomposition_agent_review_result.json")
AGENT_REVIEWED_PACKET = Path(
    "review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_EDITABLE.csv"
)
SNAPSHOT_DIR = Path("reports/zdic_snapshots")

DEFAULT_JSON_OUTPUT = Path("reports/zdic_reference_snapshot_manifest.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/ZDIC_REFERENCE_SNAPSHOT_MANIFEST.md")

SNAPSHOT_SAMPLE_CHARS = {
    "U+946B": "鑫",
    "U+7131": "焱",
    "U+3400": "㐀",
    "U+3447": "㑇",
    "U+323AF": "𲎯",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_unicode_label(unicode_label: str) -> str:
    return unicode_label.replace("+", "_")


def zdic_url(char: str) -> str:
    return f"https://www.zdic.net/hans/{quote(char)}"


def snapshot_record(unicode_label: str, char: str, packet_row: dict[str, str] | None) -> dict[str, Any]:
    safe = safe_unicode_label(unicode_label)
    dom_path = SNAPSHOT_DIR / f"{safe}_dom_snapshot.txt"
    png_path = SNAPSHOT_DIR / f"{safe}_viewport.png"
    dom_text = dom_path.read_text(encoding="utf-8") if dom_path.is_file() else ""
    return {
        "unicode": unicode_label,
        "char": char,
        "packet_id": (packet_row or {}).get("packet_id"),
        "in_current_packet": packet_row is not None,
        "zdic_url": zdic_url(char),
        "dom_snapshot_path": str(dom_path),
        "dom_snapshot_sha256": sha256_file(dom_path),
        "viewport_png_path": str(png_path),
        "viewport_png_sha256": sha256_file(png_path),
        "snapshot_available": dom_path.is_file() and png_path.is_file(),
        "observed_fields": {
            "has_radical": "部首" in dom_text,
            "has_total_strokes": "总笔画" in dom_text,
            "has_unicode": "统一码" in dom_text,
            "has_stroke_order": "笔顺" in dom_text,
            "has_structure": "字形结构" in dom_text,
            "has_kangxi": "康熙字典" in dom_text,
            "has_origin_shape": "字源字形" in dom_text,
        },
        "authority_boundary": "online_cross_reference_not_national_standard",
    }


def build_manifest() -> dict[str, Any]:
    packet_manifest = load_json(PACKET_MANIFEST)
    agent_review = load_json(AGENT_REVIEW_RESULT)
    rows = read_csv(AGENT_REVIEWED_PACKET)
    lookup_rows = [
        {
            "packet_id": row["packet_id"],
            "unicode": row["unicode"],
            "char": row["char"],
            "catalog_scope": row["catalog_scope"],
            "structure_evidence_status": row["structure_evidence_status"],
            "agent_review_status": row["human_review_status"],
            "zdic_url": zdic_url(row["char"]),
            "snapshot_status": "SNAPSHOT_CAPTURED"
            if row["unicode"] in SNAPSHOT_SAMPLE_CHARS
            else "URL_ONLY_NOT_CAPTURED",
            "authority_boundary": "zdic_cross_reference_only",
        }
        for row in rows
    ]
    rows_by_unicode = {row["unicode"]: row for row in rows}
    snapshot_records = [
        snapshot_record(unicode_label, char, rows_by_unicode.get(unicode_label))
        for unicode_label, char in SNAPSHOT_SAMPLE_CHARS.items()
    ]
    captured = [record for record in snapshot_records if record["snapshot_available"]]
    captured_in_packet = [
        record
        for record in captured
        if record["in_current_packet"]
    ]
    checks = {
        "packet_manifest_passed": packet_manifest["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY",
        "agent_review_passed": agent_review["overall_status"]
        == "PASS_STRUCTURE_DECOMPOSITION_AGENT_REVIEW_COMPLETED_NO_SCORING",
        "uses_bounded_packet_only": len(rows) == packet_manifest["summary"]["packet_rows"],
        "does_not_query_full_97686_table": True,
        "lookup_rows_match_packet": len(lookup_rows) == 212,
        "sample_snapshots_present": len(captured) == len(snapshot_records) and len(captured) >= 4,
        "packet_sample_snapshots_present": len(captured_in_packet) >= 2,
        "does_not_assign_scores": True,
        "does_not_emit_final_labels": True,
        "does_not_create_database": True,
    }
    status = "PASS_ZDIC_REFERENCE_SNAPSHOT_MANIFEST_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_zdic_reference_snapshot_manifest",
        "overall_status": status,
        "next_workflow_status": "ZDIC_REFERENCE_AVAILABLE_FOR_REVIEW_NOT_SCORING",
        "authority_boundary": {
            "zdic_is_online_cross_reference": True,
            "zdic_is_not_national_standard_authority": True,
            "does_not_query_full_97686_table": True,
            "does_not_generate_database": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
        },
        "summary": {
            "packet_rows": len(rows),
            "lookup_rows": len(lookup_rows),
            "snapshot_sample_rows": len(snapshot_records),
            "captured_snapshot_rows": len(captured),
            "captured_packet_snapshot_rows": len(captured_in_packet),
            "full_table_query_allowed": False,
            "database_generation_allowed": False,
            "gf0017_points_assigned": 0,
            "final_structure_labels_emitted": 0,
        },
        "checks": checks,
        "lookup_rows": lookup_rows,
        "snapshot_records": snapshot_records,
        "decision": {
            "may_use_zdic_for_review_context": status.startswith("PASS"),
            "may_promote_zdic_to_national_standard": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "zdic URLs and representative browser snapshots are available for "
                "review context. They must remain cross-reference evidence until "
                "validated against standards and audited."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZDIC Reference Snapshot Manifest",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Packet lookup rows: {report['summary']['lookup_rows']}",
        f"- Snapshot sample rows: {report['summary']['snapshot_sample_rows']}",
        f"- Captured snapshot rows: {report['summary']['captured_snapshot_rows']}",
        f"- Full table query allowed: `{report['summary']['full_table_query_allowed']}`",
        f"- Database generation allowed: `{report['summary']['database_generation_allowed']}`",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        "",
        "ZDIC is used as online cross-reference context only. It is not promoted",
        "to national-standard authority and does not produce scores or final",
        "structure labels.",
        "",
        "## Snapshot Samples",
        "",
        "| Unicode | Char | Snapshot | Structure field | Kangxi | 字源字形 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for record in report["snapshot_records"]:
        fields = record["observed_fields"]
        lines.append(
            f"| `{record['unicode']}` | {record['char']} | `{record['snapshot_available']}` | "
            f"`{fields['has_structure']}` | `{fields['has_kangxi']}` | `{fields['has_origin_shape']}` |"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_manifest()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"lookup_rows={report['summary']['lookup_rows']}")
    print(f"captured_snapshot_rows={report['summary']['captured_snapshot_rows']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
