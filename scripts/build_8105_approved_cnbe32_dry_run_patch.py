#!/usr/bin/env python3
"""Build a CNBE32 dry-run patch from the approved 8105 structure merge model.

This dry-run uses the human-approved 8105 Agent structure baseline and current
repository model indices. It writes review artifacts only. It does not modify
`data/cnbe32.json`, does not build SQLite, and does not publish release data.
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

from scripts.build_cnbe8105_dry_run_patch import (
    EXT_MASK,
    decode_cnbe_fields,
    encode_cnbe_fields,
)
from scripts.build_cnbe8105_radical_code_map import (
    KNOWLEDGE_BASE,
    load_radical_code_source,
    resolve_radical,
)

APPROVED_PACKET = Path("review_packets/8105_full/8105_hanzi_decomp_v03_human_approved_structure_packet.csv")
MERGE_MODEL = Path("evidence/agent-standard/cnbe8105_approved_structure_model_merge.json")
JSON_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_patch.json")
CSV_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_patch.csv")
MD_OUTPUT = Path("evidence/agent-standard/CNBE8105_APPROVED_CNBE32_DRY_RUN_PATCH.md")

EXPECTED_8105_ROWS = 8105
MAX_STROKES = 31
MAX_STRUCT_TYPE = 15
MAX_INDEX = 2047


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


def approved_rows_by_char() -> dict[str, dict[str, str]]:
    return {row["character"]: row for row in read_csv(APPROVED_PACKET)}


def parse_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def block_record(merge: dict[str, Any], reason: str, detail: str = "") -> dict[str, Any]:
    return {
        "character": merge["character"],
        "unicode_codepoint": merge["unicode_codepoint"],
        "standard_rank": merge["standard_rank"],
        "status": "DRY_RUN_BLOCKED",
        "block_reason": reason,
        "block_detail": detail,
        "approved_agent_structure": merge["approved_agent_structure"],
        "approved_agent_struct_type": merge["approved_agent_struct_type"],
        "approved_radical": "",
        "approved_strokes": "",
        "current_cnbe": merge.get("current_cnbe", ""),
        "current_index": "",
        "write_gate": "NO_WRITE_DRY_RUN_ONLY",
    }


def dry_run_record(
    merge: dict[str, Any],
    approved: dict[str, str],
    radical_resolution: dict[str, Any],
) -> dict[str, Any]:
    current_code = int(merge["current_cnbe"])
    current_index = int(merge["current_index"]) if "current_index" in merge else None
    if current_index is None:
        current_index = None
    current_index = int(merge.get("current_index", approved.get("current_index", 0)) or 0)
    strokes = int(approved["stroke_count"])
    struct_type = int(merge["approved_agent_struct_type"])
    radix = int(radical_resolution["code"])
    ext = current_code & EXT_MASK
    proposed_code = encode_cnbe_fields(radix, strokes, struct_type, current_index, ext)
    decoded = decode_cnbe_fields(proposed_code)
    return {
        "character": merge["character"],
        "unicode_codepoint": merge["unicode_codepoint"],
        "standard_rank": merge["standard_rank"],
        "status": "DRY_RUN_READY",
        "merge_status": merge["merge_status"],
        "approved_basis": merge["approved_basis"],
        "approved_radical": approved["radical"],
        "approved_canonical_radical": radical_resolution["canonical_radical"],
        "approved_radical_resolution": radical_resolution["status"],
        "approved_radix": radix,
        "approved_strokes": strokes,
        "approved_agent_structure": merge["approved_agent_structure"],
        "approved_agent_struct_type": struct_type,
        "approved_decomposition": merge["approved_decomposition"],
        "current_cnbe": current_code,
        "current_cnbe_hex": f"0x{current_code:08X}",
        "current_radix": merge["current_radix"],
        "current_radix_name": merge["current_radix_name"],
        "current_strokes": merge["current_strokes"],
        "current_struct_name": merge["current_struct_name"],
        "current_struct_type": merge["current_struct_type"],
        "current_index": current_index,
        "current_ext": ext,
        "proposed_cnbe": proposed_code,
        "proposed_cnbe_hex": f"0x{proposed_code:08X}",
        "proposed_radix": radix,
        "proposed_radix_name": approved["radical"],
        "proposed_canonical_radical": radical_resolution["canonical_radical"],
        "proposed_strokes": strokes,
        "proposed_struct_type": struct_type,
        "proposed_struct_name": merge["approved_agent_structure"],
        "proposed_index": current_index,
        "proposed_ext": ext,
        "roundtrip_pass": decoded
        == {
            "radix": radix,
            "strokes": strokes,
            "struct_type": struct_type,
            "index": current_index,
            "ext": ext,
        },
        "decoded_radix": decoded["radix"],
        "decoded_strokes": decoded["strokes"],
        "decoded_struct_type": decoded["struct_type"],
        "decoded_index": decoded["index"],
        "decoded_ext": decoded["ext"],
        "write_gate": "NO_WRITE_DRY_RUN_ONLY",
    }


def current_index_from_merge(merge: dict[str, Any]) -> int | None:
    current_cnbe = parse_int(merge.get("current_cnbe"))
    if current_cnbe is None:
        return None
    decoded = decode_cnbe_fields(current_cnbe)
    return decoded["index"]


def build() -> dict[str, Any]:
    approved_by_char = approved_rows_by_char()
    merge_model = read_json(MERGE_MODEL)
    radical_source = load_radical_code_source(KNOWLEDGE_BASE)
    radical_to_code = radical_source["radical_to_code"]
    records: list[dict[str, Any]] = []
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for merge in merge_model["records"]:
        approved = approved_by_char[merge["character"]]
        merge = dict(merge)
        index = current_index_from_merge(merge)
        if index is not None:
            merge["current_index"] = index
        radical = approved.get("radical", "")
        strokes = parse_int(approved.get("stroke_count"))
        struct_type = parse_int(merge.get("approved_agent_struct_type"))
        if merge["merge_status"] == "MISSING_FROM_CURRENT_CNBE_AGENT_INSERT_CANDIDATE":
            record = block_record(merge, "missing_current_model_row", "No current CNBE32 index/ext can be preserved.")
        elif merge["unicode_status"] != "UNICODE_MATCH":
            record = block_record(merge, "unicode_not_matched", merge["unicode_status"])
        elif not radical:
            record = block_record(merge, "missing_approved_radical", "Approved packet has no radical for CNBE32 radix.")
        elif strokes is None or not 0 <= strokes <= MAX_STROKES:
            record = block_record(merge, "invalid_approved_stroke_count", str(approved.get("stroke_count", "")))
        elif struct_type is None or not 0 <= struct_type <= MAX_STRUCT_TYPE:
            record = block_record(merge, "invalid_approved_structure_type", str(merge.get("approved_agent_struct_type", "")))
        elif index is None or not 0 <= index <= MAX_INDEX:
            record = block_record(merge, "invalid_current_index", str(index))
        else:
            resolution = resolve_radical(radical, radical_to_code)
            if resolution["status"] == "BLOCKED":
                record = block_record(merge, "radical_resolution_blocked", resolution["reason"])
                record["approved_radical"] = radical
                record["approved_strokes"] = strokes
                record["current_index"] = index
            else:
                record = dry_run_record(merge, approved, resolution)
        records.append(record)
        if record["status"] == "DRY_RUN_READY":
            ready.append(record)
        else:
            blocked.append(record)

    ready.sort(key=lambda row: int(row["standard_rank"]))
    blocked.sort(key=lambda row: int(row["standard_rank"]))
    status_counts = Counter(row["status"] for row in records)
    block_counts = Counter(row.get("block_reason", "") for row in blocked)
    merge_status_counts = Counter(row.get("merge_status", "BLOCKED_BEFORE_MERGE_STATUS") for row in ready)
    radical_resolution_counts = Counter(row.get("approved_radical_resolution", "") for row in ready)
    changed_field_counts: Counter[str] = Counter()
    for row in ready:
        for current_key, proposed_key, field in [
            ("current_cnbe", "proposed_cnbe", "cnbe"),
            ("current_radix", "proposed_radix", "radix"),
            ("current_radix_name", "proposed_radix_name", "radix_name"),
            ("current_strokes", "proposed_strokes", "strokes"),
            ("current_struct_type", "proposed_struct_type", "struct_type"),
            ("current_struct_name", "proposed_struct_name", "struct_name"),
        ]:
            if str(row[current_key]) != str(row[proposed_key]):
                changed_field_counts[field] += 1

    known = {
        char: next((row for row in records if row["character"] == char), None)
        for char in ("家", "侵", "偶", "冁", "孓", "㑇")
    }
    checks = {
        "row_count_is_8105": len(records) == EXPECTED_8105_ROWS,
        "ready_plus_blocked_equals_total": len(ready) + len(blocked) == len(records),
        "all_ready_roundtrips_pass": all(row["roundtrip_pass"] is True for row in ready),
        "all_ready_use_current_index": all(row["current_index"] == row["proposed_index"] for row in ready),
        "all_ready_have_no_write_gate": all(row["write_gate"] == "NO_WRITE_DRY_RUN_ONLY" for row in ready),
        "all_blocked_have_reason": all(row.get("block_reason") for row in blocked),
        "known_samples_routed_correctly": all(
            known[char]
            and known[char]["approved_agent_structure"]
            == {"家": "上下", "侵": "左右", "偶": "左右", "冁": "左右", "孓": "独体字"}[char]
            and known[char]["status"] in {"DRY_RUN_READY", "DRY_RUN_BLOCKED"}
            for char in ("家", "侵", "偶", "冁", "孓")
        )
        and known["㑇"]
        and known["㑇"]["block_reason"] == "missing_current_model_row",
        "no_source_table_writes": True,
        "no_database_rebuild": True,
    }
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "approved_8105_agent_structure_to_cnbe32_dry_run_patch",
            "approved_packet": str(APPROVED_PACKET),
            "merge_model": str(MERGE_MODEL),
            "radical_code_source": str(KNOWLEDGE_BASE),
            "write_gate": "NO_WRITE_DRY_RUN_ONLY",
        },
        "overall_status": "PASS_8105_APPROVED_CNBE32_DRY_RUN_READY" if all(checks.values()) else "BLOCKED",
        "summary": {
            "total_rows": len(records),
            "dry_run_ready_rows": len(ready),
            "dry_run_blocked_rows": len(blocked),
            "status_counts": dict(status_counts),
            "block_reason_counts": dict(block_counts),
            "ready_merge_status_counts": dict(merge_status_counts),
            "radical_resolution_counts": dict(radical_resolution_counts),
            "changed_field_counts": dict(changed_field_counts),
            "source_table_rows_written": 0,
            "cnbe32_source_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "known_samples": known,
        "samples": {
            "first_ready": ready[:30],
            "first_blocked": blocked[:30],
        },
        "records": records,
        "patch": ready,
        "blocked": blocked,
        "outputs": {
            "json": str(JSON_OUTPUT),
            "csv": str(CSV_OUTPUT),
            "markdown": str(MD_OUTPUT),
        },
        "decision": {
            "may_review_cnbe32_dry_run_patch": all(checks.values()),
            "may_write_data_cnbe32_json": False,
            "may_rebuild_sqlite_database": False,
            "recommended_next_step": (
                "Review dry-run ready and blocked rows. A future write phase must "
                "copy the source table first, resolve blocked radicals and missing "
                "current-model indices, then regenerate dependent artifacts in a "
                "separate authorization step."
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
    for char, row in model["known_samples"].items():
        known_rows.append(
            [
                char,
                row["unicode_codepoint"],
                row["status"],
                row.get("block_reason", ""),
                row["approved_agent_structure"],
                row["approved_agent_struct_type"],
                row.get("current_cnbe_hex", row.get("current_cnbe", "")),
                row.get("proposed_cnbe_hex", ""),
            ]
        )
    lines = [
        "# CNBE 8105 Approved CNBE32 Dry-Run Patch",
        "",
        f"- Overall status: `{model['overall_status']}`",
        f"- Total rows: {summary['total_rows']}",
        f"- Dry-run ready rows: {summary['dry_run_ready_rows']}",
        f"- Dry-run blocked rows: {summary['dry_run_blocked_rows']}",
        f"- Source table rows written: {summary['source_table_rows_written']}",
        f"- CNBE32 source rows written: {summary['cnbe32_source_rows_written']}",
        f"- Database rebuild allowed: `{summary['database_rebuild_allowed']}`",
        "",
        "This artifact previews CNBE32 field values only. It preserves the",
        "current model index and extension bits, uses the approved 8105 Agent",
        "structure baseline, and blocks missing or ambiguous rows.",
        "",
        "## Block Reasons",
        "",
        markdown_table(["Reason", "Rows"], [[key, value] for key, value in sorted(summary["block_reason_counts"].items())]),
        "",
        "## Changed Field Counts",
        "",
        markdown_table(["Field", "Rows"], [[key, value] for key, value in sorted(summary["changed_field_counts"].items())]),
        "",
        "## Known Samples",
        "",
        markdown_table(
            [
                "Char",
                "Unicode",
                "Status",
                "Block reason",
                "Approved structure",
                "Approved type",
                "Current CNBE",
                "Proposed CNBE",
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
    print(f"dry_run_ready_rows={model['summary']['dry_run_ready_rows']}")
    print(f"dry_run_blocked_rows={model['summary']['dry_run_blocked_rows']}")
    print(f"cnbe32_source_rows_written={model['summary']['cnbe32_source_rows_written']}")
    print(f"database_rebuild_allowed={model['summary']['database_rebuild_allowed']}")


if __name__ == "__main__":
    main()
