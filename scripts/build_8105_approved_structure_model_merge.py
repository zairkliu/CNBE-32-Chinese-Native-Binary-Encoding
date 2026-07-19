#!/usr/bin/env python3
"""Merge the human-approved 8105 structure packet into repo model evidence.

The output is a repository-model merge candidate. It compares the approved
8105 Agent structure baseline against the legacy/runtime `data/cnbe32.json`
model, but it does not rewrite that model, encode CNBE32 values, or rebuild any
database.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_cnbe_agent_encoding_standard import (
    AGENT_ALLOWED_STRUCTURES,
    LEGACY_STRUCTURE_LOCALIZATION,
)

APPROVED_PACKET = Path("review_packets/8105_full/8105_hanzi_decomp_v03_human_approved_structure_packet.csv")
CNBE32_MODEL = Path("data/cnbe32.json")
JSON_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_structure_model_merge.json")
CSV_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_structure_model_merge.csv")
MD_OUTPUT = Path("evidence/agent-standard/CNBE8105_APPROVED_STRUCTURE_MODEL_MERGE.md")

EXPECTED_8105_ROWS = 8105
KNOWN_REGRESSION_CHARS = ("家", "侵", "偶", "冁", "孓", "㑇")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def codepoint_to_unicode(codepoint: Any) -> str:
    if isinstance(codepoint, int):
        return f"U+{codepoint:04X}"
    if isinstance(codepoint, str) and codepoint.startswith("U+"):
        return codepoint
    return ""


def legacy_agent_structure(row: dict[str, Any] | None) -> tuple[str, str, str]:
    if row is None:
        return "", "", ""
    raw_name = str(row.get("struct_name", ""))
    mapping = LEGACY_STRUCTURE_LOCALIZATION.get(raw_name)
    if not mapping:
        return raw_name, str(row.get("struct_type", "")), "LEGACY_STRUCTURE_UNMAPPED"
    return mapping["agent_structure"], str(mapping["agent_struct_type"]), "LEGACY_STRUCTURE_LOCALIZED"


def merge_record(approved: dict[str, str], current: dict[str, Any] | None) -> dict[str, Any]:
    current_structure, current_agent_type, current_status = legacy_agent_structure(current)
    approved_structure = approved["candidate_structure_label"]
    approved_type = approved["agent_struct_type"]
    exists = current is not None
    if not exists:
        merge_status = "MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE"
    elif current_structure == approved_structure and current_agent_type == approved_type:
        merge_status = "CURRENT_MODEL_STRUCTURE_CONFIRMED"
    else:
        merge_status = "CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE"

    current_unicode = codepoint_to_unicode(current.get("unicode")) if current else ""
    unicode_status = (
        "CURRENT_MODEL_MISSING"
        if not current
        else "UNICODE_MATCH"
        if current_unicode == approved["unicode_codepoint"]
        else "UNICODE_MISMATCH_BLOCKER"
    )
    return {
        "row_id": approved["row_id"],
        "character": approved["character"],
        "unicode_codepoint": approved["unicode_codepoint"],
        "decimal_codepoint": approved["decimal_codepoint"],
        "standard_rank": approved["standard_rank"],
        "scope": approved["scope"],
        "approved_agent_structure": approved_structure,
        "approved_agent_struct_type": approved_type,
        "approved_decomposition": approved["candidate_decomposition"],
        "approved_components": approved["direct_component_candidates"],
        "approved_basis": approved.get("human_review_basis", ""),
        "current_model_exists": exists,
        "current_unicode_codepoint": current_unicode,
        "unicode_status": unicode_status,
        "current_cnbe": current.get("cnbe", "") if current else "",
        "current_radix": current.get("radix", "") if current else "",
        "current_radix_name": current.get("radix_name", "") if current else "",
        "current_strokes": current.get("strokes", "") if current else "",
        "current_struct_name": current.get("struct_name", "") if current else "",
        "current_struct_type": current.get("struct_type", "") if current else "",
        "current_agent_structure_localized": current_structure,
        "current_agent_struct_type_localized": current_agent_type,
        "current_structure_localization_status": current_status,
        "merge_status": merge_status,
        "merge_authority": "HUMAN_APPROVED_AGENT_STRUCTURE_CANDIDATE_NOT_NATIONAL_STANDARD",
        "source_table_write_status": "NO_SOURCE_TABLE_WRITE",
        "cnbe32_write_status": "NO_CNBE32_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
    }


def build() -> dict[str, Any]:
    approved_rows = read_csv(APPROVED_PACKET)
    current_rows = read_json(CNBE32_MODEL)["characters"]
    current_by_char = {row["char"]: row for row in current_rows}
    records = [merge_record(row, current_by_char.get(row["character"])) for row in approved_rows]
    status_counts = Counter(row["merge_status"] for row in records)
    structure_counts = Counter(row["approved_agent_structure"] for row in records)
    basis_counts = Counter(row["approved_basis"] for row in records)
    unicode_status_counts = Counter(row["unicode_status"] for row in records)
    repair_rows = [row for row in records if row["merge_status"] == "CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE"]
    missing_rows = [row for row in records if row["merge_status"] == "MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE"]
    confirmed_rows = [row for row in records if row["merge_status"] == "CURRENT_MODEL_STRUCTURE_CONFIRMED"]
    bad_structures = sorted({row["approved_agent_structure"] for row in records} - set(AGENT_ALLOWED_STRUCTURES))
    known = {char: next(row for row in records if row["character"] == char) for char in KNOWN_REGRESSION_CHARS}
    checks = {
        "row_count_is_8105": len(records) == EXPECTED_8105_ROWS,
        "all_approved_structures_allowed": not bad_structures,
        "all_approved_structures_have_codes": all(row["approved_agent_struct_type"] != "" for row in records),
        "unique_character_count_is_8105": len({row["character"] for row in records}) == EXPECTED_8105_ROWS,
        "unique_unicode_count_is_8105": len({row["unicode_codepoint"] for row in records}) == EXPECTED_8105_ROWS,
        "no_unicode_mismatch": "UNICODE_MISMATCH_BLOCKER" not in unicode_status_counts,
        "known_regressions_are_repair_or_insert_candidates": all(
            known[char]["merge_status"]
            in {"CURRENT_MODEL_STRUCTURE_REPAIR_CANDIDATE", "MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE"}
            for char in KNOWN_REGRESSION_CHARS
        ),
        "no_source_table_writes": all(row["source_table_write_status"] == "NO_SOURCE_TABLE_WRITE" for row in records),
        "no_cnbe32_writes": all(row["cnbe32_write_status"] == "NO_CNBE32_WRITE" for row in records),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in records),
    }
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "approved_8105_structure_packet_to_repository_structure_model_merge",
            "approved_packet": str(APPROVED_PACKET),
            "repository_structure_model": str(CNBE32_MODEL),
            "write_gate": "NO_SOURCE_TABLE_WRITE_NO_CNBE32_WRITE_NO_DATABASE_REBUILD",
        },
        "overall_status": "PASS_8105_APPROVED_STRUCTURE_MODEL_MERGE_READY"
        if all(checks.values())
        else "BLOCKED",
        "summary": {
            "total_rows": len(records),
            "current_model_rows": len(current_rows),
            "current_model_intersection_rows": len(records) - len(missing_rows),
            "missing_from_current_model_rows": len(missing_rows),
            "current_model_confirmed_rows": len(confirmed_rows),
            "current_model_structure_repair_candidate_rows": len(repair_rows),
            "merge_status_counts": dict(status_counts),
            "unicode_status_counts": dict(unicode_status_counts),
            "approved_structure_counts": dict(structure_counts),
            "approved_basis_counts": dict(basis_counts),
            "source_table_rows_written": 0,
            "cnbe32_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "known_regression_samples": known,
        "samples": {
            "first_repair_candidates": repair_rows[:30],
            "first_missing_candidates": missing_rows[:30],
            "first_confirmed": confirmed_rows[:30],
        },
        "records": records,
        "outputs": {
            "json": str(JSON_OUTPUT),
            "csv": str(CSV_OUTPUT),
            "markdown": str(MD_OUTPUT),
        },
        "decision": {
            "may_use_as_repository_structure_model_merge_candidate": all(checks.values()),
            "may_write_data_cnbe32_json": False,
            "may_rebuild_database": False,
            "recommended_next_step": (
                "Review repair and missing-row counts, then design a separate "
                "CNBE32 dry-run encoding patch for rows whose radical, stroke, "
                "structure, and index fields can be resolved without ambiguity."
            ),
        },
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(model: dict[str, Any]) -> str:
    summary = model["summary"]
    known_rows = []
    for char in KNOWN_REGRESSION_CHARS:
        row = model["known_regression_samples"][char]
        known_rows.append(
            [
                char,
                row["unicode_codepoint"],
                row["approved_agent_structure"],
                row["approved_agent_struct_type"],
                row["current_struct_name"],
                row["current_struct_type"],
                row["current_agent_structure_localized"],
                row["merge_status"],
            ]
        )
    lines = [
        "# CNBE 8105 Approved Structure Model Merge",
        "",
        f"- Overall status: `{model['overall_status']}`",
        f"- Total 8105 rows: {summary['total_rows']}",
        f"- Current model intersection rows: {summary['current_model_intersection_rows']}",
        f"- Missing from current model rows: {summary['missing_from_current_model_rows']}",
        f"- Current model confirmed rows: {summary['current_model_confirmed_rows']}",
        f"- Structure repair candidate rows: {summary['current_model_structure_repair_candidate_rows']}",
        f"- CNBE32 rows written: {summary['cnbe32_rows_written']}",
        f"- Database rebuild allowed: `{summary['database_rebuild_allowed']}`",
        "",
        "This merge is evidence-only. It does not modify `data/cnbe32.json`,",
        "does not encode CNBE32 values, and does not rebuild SQLite databases.",
        "",
        "## Merge Status Counts",
        "",
        markdown_table(["Status", "Rows"], [[key, value] for key, value in sorted(summary["merge_status_counts"].items())]),
        "",
        "## Known Regression Samples",
        "",
        markdown_table(
            [
                "Char",
                "Unicode",
                "Approved structure",
                "Approved type",
                "Current struct name",
                "Current type",
                "Current localized",
                "Merge status",
            ],
            known_rows,
        ),
        "",
        "## Decision",
        "",
        model["decision"]["recommended_next_step"],
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    model = build()
    write_json(JSON_OUTPUT, model)
    write_csv(CSV_OUTPUT, model["records"])
    write_text(MD_OUTPUT, render_markdown(model))
    return model


def main() -> None:
    model = run()
    print(model["overall_status"])
    print(f"total_rows={model['summary']['total_rows']}")
    print(f"current_model_intersection_rows={model['summary']['current_model_intersection_rows']}")
    print(f"missing_from_current_model_rows={model['summary']['missing_from_current_model_rows']}")
    print(f"current_model_structure_repair_candidate_rows={model['summary']['current_model_structure_repair_candidate_rows']}")
    print(f"cnbe32_rows_written={model['summary']['cnbe32_rows_written']}")
    print(f"database_rebuild_allowed={model['summary']['database_rebuild_allowed']}")


if __name__ == "__main__":
    main()
