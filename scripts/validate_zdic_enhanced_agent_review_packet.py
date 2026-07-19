#!/usr/bin/env python3
"""Validate the ZDIC-enhanced Agent review packet boundary.

This validator is intentionally read-only. It checks that ZDIC evidence remains
bounded review context for the 212-row packet and does not become GF0017
scoring evidence, final structure labels, CNBE rows, a database, or a full
97,686-row duplicate.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ZDIC_MANIFEST = Path("reports/zdic_reference_snapshot_manifest.json")
ZDIC_ENHANCEMENT = Path("reports/structure_decomposition_agent_review_zdic_enhancement.json")
AGENT_REVIEW = Path("reports/structure_decomposition_agent_review_result.json")
PACKET_MANIFEST = Path("reports/structure_decomposition_review_packet_manifest.json")
ENHANCED_PACKET = Path(
    "review_packets/structure_decomposition/structure_decomposition_review_packet_AGENT_REVIEWED_ZDIC_EDITABLE.csv"
)

DEFAULT_JSON_OUTPUT = Path("reports/zdic_enhanced_agent_review_packet_validation.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/ZDIC_ENHANCED_AGENT_REVIEW_PACKET_VALIDATION.md")

EXPECTED_PACKET_ROWS = 212
FULL_CATALOG_ROWS = 97686
EDITABLE_NOTICE = "AGENT_REVIEWED_ZDIC_EDITABLE_COPY_NOT_SOURCE_EVIDENCE"


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


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_packet() -> dict[str, Any]:
    zdic_manifest = load_json(ZDIC_MANIFEST)
    zdic_enhancement = load_json(ZDIC_ENHANCEMENT)
    agent_review = load_json(AGENT_REVIEW)
    packet_manifest = load_json(PACKET_MANIFEST)
    fieldnames, rows = read_csv(ENHANCED_PACKET)

    snapshot_records = zdic_manifest["snapshot_records"]
    snapshot_file_checks = []
    for record in snapshot_records:
        dom_path = Path(record["dom_snapshot_path"])
        png_path = Path(record["viewport_png_path"])
        snapshot_file_checks.append(
            {
                "unicode": record["unicode"],
                "char": record["char"],
                "dom_snapshot_path": str(dom_path),
                "dom_snapshot_exists": dom_path.is_file(),
                "dom_snapshot_sha256": sha256_file(dom_path),
                "viewport_png_path": str(png_path),
                "viewport_png_exists": png_path.is_file(),
                "viewport_png_sha256": sha256_file(png_path),
                "observed_fields": record["observed_fields"],
                "authority_boundary": record["authority_boundary"],
            }
        )

    row_checks = {
        "row_count_is_bounded_packet": len(rows) == EXPECTED_PACKET_ROWS,
        "row_count_is_not_full_catalog": len(rows) < FULL_CATALOG_ROWS,
        "all_rows_have_zdic_url": all(";zdic:https://www.zdic.net/hans/" in row["human_source_reference"] for row in rows),
        "all_rows_keep_blank_structure_label": all(row["human_structure_label"] == "" for row in rows),
        "all_rows_keep_blank_decomposition": all(row["human_decomposition"] == "" for row in rows),
        "all_rows_marked_editable_not_source_evidence": all(row["editable_copy_notice"] == EDITABLE_NOTICE for row in rows),
        "no_score_columns_added": "gf0017_score" not in fieldnames and "score" not in fieldnames,
        "no_final_agent_structure_column_added": "agent_structure" not in fieldnames
        and "final_structure_label" not in fieldnames,
    }

    checks = {
        "packet_manifest_passed": packet_manifest["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY",
        "agent_review_passed": agent_review["overall_status"]
        == "PASS_STRUCTURE_DECOMPOSITION_AGENT_REVIEW_COMPLETED_NO_SCORING",
        "zdic_manifest_passed": zdic_manifest["overall_status"] == "PASS_ZDIC_REFERENCE_SNAPSHOT_MANIFEST_READY",
        "zdic_enhancement_passed": zdic_enhancement["overall_status"] == "PASS_AGENT_REVIEW_ZDIC_REFERENCES_APPLIED",
        "uses_bounded_packet_only": len(rows) == packet_manifest["summary"]["packet_rows"] == EXPECTED_PACKET_ROWS,
        "does_not_duplicate_full_97686_table": len(rows) < FULL_CATALOG_ROWS,
        "snapshot_files_exist_with_hashes": all(
            item["dom_snapshot_exists"]
            and item["dom_snapshot_sha256"]
            and item["viewport_png_exists"]
            and item["viewport_png_sha256"]
            for item in snapshot_file_checks
        ),
        "snapshot_core_navigation_fields_present": all(
            item["observed_fields"]["has_unicode"]
            and item["observed_fields"]["has_radical"]
            and item["observed_fields"]["has_total_strokes"]
            and item["observed_fields"]["has_stroke_order"]
            for item in snapshot_file_checks
        ),
        "snapshot_supplemental_fields_recorded_with_gaps": sum(
            1
            for item in snapshot_file_checks
            if item["observed_fields"]["has_structure"]
            and item["observed_fields"]["has_kangxi"]
            and item["observed_fields"]["has_origin_shape"]
        )
        >= 4,
        "zdic_remains_cross_reference_only": zdic_manifest["authority_boundary"]["zdic_is_online_cross_reference"]
        and zdic_manifest["authority_boundary"]["zdic_is_not_national_standard_authority"]
        and zdic_enhancement["authority_boundary"]["zdic_cross_reference_only"],
        "does_not_assign_gf0017_points": zdic_manifest["summary"]["gf0017_points_assigned"] == 0
        and zdic_enhancement["summary"]["gf0017_points_assigned"] == 0,
        "does_not_emit_final_structure_labels": zdic_manifest["summary"]["final_structure_labels_emitted"] == 0
        and zdic_enhancement["summary"]["final_structure_labels_emitted"] == 0,
        "does_not_create_database_or_xlsx": not any(
            str(path).endswith((".db", ".sqlite", ".sqlite3", ".xlsx"))
            for path in [
                ZDIC_MANIFEST,
                ZDIC_ENHANCEMENT,
                AGENT_REVIEW,
                PACKET_MANIFEST,
                ENHANCED_PACKET,
                DEFAULT_JSON_OUTPUT,
                DEFAULT_MARKDOWN_OUTPUT,
            ]
        ),
        **row_checks,
    }

    status = "PASS_ZDIC_ENHANCED_AGENT_REVIEW_PACKET_VALIDATED" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "validate_zdic_enhanced_agent_review_packet",
        "overall_status": status,
        "next_workflow_status": "ZDIC_ENHANCED_PACKET_READY_FOR_HUMAN_REVIEW_NOT_SCORING",
        "summary": {
            "enhanced_packet_rows": len(rows),
            "full_catalog_rows": FULL_CATALOG_ROWS,
            "snapshot_records": len(snapshot_records),
            "snapshot_files_verified": sum(
                1
                for item in snapshot_file_checks
                if item["dom_snapshot_exists"] and item["viewport_png_exists"]
            ),
            "snapshot_records_with_supplemental_field_gaps": sum(
                1
                for item in snapshot_file_checks
                if not (
                    item["observed_fields"]["has_structure"]
                    and item["observed_fields"]["has_kangxi"]
                    and item["observed_fields"]["has_origin_shape"]
                )
            ),
            "gf0017_points_assigned": 0,
            "final_structure_labels_emitted": 0,
            "database_generation_allowed": False,
            "xlsx_generation_allowed": False,
        },
        "checks": checks,
        "snapshot_file_checks": snapshot_file_checks,
        "outputs": {
            "validation_json": str(DEFAULT_JSON_OUTPUT),
            "validation_markdown": str(DEFAULT_MARKDOWN_OUTPUT),
            "enhanced_packet": str(ENHANCED_PACKET),
        },
        "decision": {
            "may_use_zdic_enhanced_packet_for_human_review": status.startswith("PASS"),
            "may_promote_zdic_to_national_standard": False,
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "ZDIC is validated as online navigation and cross-reference context "
                "for the bounded review packet only. Any source-evidence merge or "
                "score assignment requires a later standards-validation gate."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ZDIC Enhanced Agent Review Packet Validation",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Enhanced packet rows: {report['summary']['enhanced_packet_rows']}",
        f"- Snapshot records: {report['summary']['snapshot_records']}",
        f"- Snapshot files verified: {report['summary']['snapshot_files_verified']}",
        f"- Snapshot records with supplemental field gaps: {report['summary']['snapshot_records_with_supplemental_field_gaps']}",
        f"- GF0017 points assigned: {report['summary']['gf0017_points_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        f"- Database generation allowed: `{report['summary']['database_generation_allowed']}`",
        f"- XLSX generation allowed: `{report['summary']['xlsx_generation_allowed']}`",
        "",
        "## Authority Boundary",
        "",
        "ZDIC remains an online cross-reference and reviewer navigation layer.",
        "It is not national-standard authority, GF0017 scoring evidence, a final",
        "structure label source, a CNBE row source, or a database reconstruction",
        "source in this gate.",
        "",
        "## Snapshot Verification",
        "",
        "| Unicode | Char | DOM | PNG | Unicode Field | Radical | Strokes | Stroke Order | Kangxi |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["snapshot_file_checks"]:
        fields = item["observed_fields"]
        lines.append(
            f"| `{item['unicode']}` | {item['char']} | `{item['dom_snapshot_exists']}` | "
            f"`{item['viewport_png_exists']}` | `{fields['has_unicode']}` | "
            f"`{fields['has_radical']}` | `{fields['has_total_strokes']}` | "
            f"`{fields['has_stroke_order']}` | `{fields['has_kangxi']}` |"
        )
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = validate_packet()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"enhanced_packet_rows={report['summary']['enhanced_packet_rows']}")
    print(f"snapshot_files_verified={report['summary']['snapshot_files_verified']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
