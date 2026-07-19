#!/usr/bin/env python3
"""Plan resolution work for the remaining 8105 runtime promotion blockers.

This is a read-only planning script. It reviews the 1,393 force-approved rows
that were intentionally left out of the runtime patch and classifies what must
be resolved before any later source-table write can be considered.
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

from scripts.build_cnbe8105_dry_run_patch import decode_cnbe_fields

FORCE_APPROVAL = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_human_force_approval.json")
RUNTIME_PROMOTION = Path("reports/8105_cnbe32_runtime_promotion.json")
SOURCE_CNBE32 = Path("data/cnbe32.json")
JSON_OUTPUT = Path("reports/8105_runtime_blocker_resolution_plan.json")
MD_OUTPUT = Path("reports/8105_RUNTIME_BLOCKER_RESOLUTION_PLAN.md")
CSV_OUTPUT = Path("review_packets/8105_full/8105_runtime_blocker_resolution_queue.csv")

EXPECTED_BLOCKED_ROWS = 1393
EXPECTED_REASON_COUNTS = {
    "missing_approved_radical": 964,
    "missing_current_model_row": 276,
    "radical_resolution_blocked": 153,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def source_rows_by_char() -> dict[str, dict[str, Any]]:
    model = read_json(SOURCE_CNBE32)
    return {row["char"]: row for row in model["characters"]}


def blocked_force_rows() -> list[dict[str, Any]]:
    model = read_json(FORCE_APPROVAL)
    return [
        row
        for row in model["records"]
        if row["implementation_queue"] == "CNBE32_FORCE_APPROVED_BLOCKER_RESOLUTION_PLAN_CANDIDATE"
    ]


def decoded_current_fields(row: dict[str, Any]) -> dict[str, Any]:
    current_cnbe = row.get("current_cnbe", "")
    if current_cnbe in ("", None):
        return {"current_index_recoverable": False, "decoded_current_index": "", "decoded_ext": ""}
    decoded = decode_cnbe_fields(int(current_cnbe))
    return {
        "current_index_recoverable": True,
        "decoded_current_index": decoded["index"],
        "decoded_ext": decoded["ext"],
    }


def resolution_class(row: dict[str, Any], in_source_model: bool) -> tuple[str, str]:
    reason = row["block_reason"]
    radical = str(row.get("approved_radical", ""))
    detail = str(row.get("block_detail", ""))
    if reason == "missing_current_model_row":
        return (
            "requires_index_allocation_and_source_row_insertion_plan",
            "8105 character is absent from the current 20,902-row runtime model; no current index/ext can be preserved.",
        )
    if reason == "missing_approved_radical":
        return (
            "requires_standard_radical_and_stroke_join",
            "Approved Agent structure exists, but radical/stroke evidence is blank and must be joined before CNBE32 bitfields can be recomputed.",
        )
    if reason == "radical_resolution_blocked" and radical == "阝":
        return (
            "requires_position_sensitive_radical_rule",
            "阝 must be resolved as 阜 or 邑 by side/position evidence; current queue preserves the block until that rule is audited.",
        )
    if reason == "radical_resolution_blocked":
        if "component-like" in detail or "stroke/component-like" in detail:
            return (
                "requires_component_to_radical_policy_review",
                "Approved radical label is a component or stroke-like form that is not safely mapped to a CNBE32 radix yet.",
            )
        if "ambiguous" in detail:
            return (
                "requires_shape_group_disambiguation",
                "Approved radical label belongs to an ambiguous shape group and needs explicit standard-source disambiguation.",
            )
        return (
            "requires_radical_alias_extension_review",
            "Approved radical label is outside the conservative radical map and needs an audited alias or fallback policy.",
        )
    if not in_source_model:
        return (
            "requires_source_model_presence_check",
            "Row is not present in the current source model and cannot be patched without an insertion strategy.",
        )
    return (
        "requires_manual_triage",
        "Unexpected blocker shape; keep row out of writes until manually reviewed.",
    )


def queue_record(row: dict[str, Any], source_by_char: dict[str, dict[str, Any]]) -> dict[str, Any]:
    char = row["character"]
    source = source_by_char.get(char)
    decoded = decoded_current_fields(row)
    resolution, next_action = resolution_class(row, source is not None)
    return {
        "char": char,
        "unicode": row["unicode_codepoint"],
        "standard_rank": row["standard_rank"],
        "block_reason": row["block_reason"],
        "resolution_class": resolution,
        "next_required_action": next_action,
        "approved_radical": row.get("approved_radical", ""),
        "approved_strokes": row.get("approved_strokes", ""),
        "approved_agent_structure": row.get("approved_agent_structure", ""),
        "approved_agent_struct_type": row.get("approved_agent_struct_type", ""),
        "source_model_presence": "present" if source is not None else "missing",
        "current_index_recoverable": decoded["current_index_recoverable"],
        "decoded_current_index": decoded["decoded_current_index"],
        "decoded_ext": decoded["decoded_ext"],
        "write_status": "NO_SOURCE_TABLE_WRITE",
        "database_status": "NO_DATABASE_REBUILD",
    }


def top_counter(counter: Counter[str], limit: int = 20) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def build() -> dict[str, Any]:
    rows = blocked_force_rows()
    source_by_char = source_rows_by_char()
    runtime = read_json(RUNTIME_PROMOTION)
    queue = [queue_record(row, source_by_char) for row in rows]
    reason_counts = Counter(row["block_reason"] for row in queue)
    class_counts = Counter(row["resolution_class"] for row in queue)
    structure_counts = Counter(row["approved_agent_structure"] for row in queue)
    radical_counts = Counter(row["approved_radical"] for row in queue)
    source_presence_counts = Counter(row["source_model_presence"] for row in queue)
    recoverable_index_counts = Counter(str(row["current_index_recoverable"]) for row in queue)
    policy_order = [
        {
            "step": 1,
            "resolution_class": "requires_standard_radical_and_stroke_join",
            "scope": class_counts["requires_standard_radical_and_stroke_join"],
            "recommended_gate": "join standard radical and stroke evidence; no CNBE32 writes",
        },
        {
            "step": 2,
            "resolution_class": "requires_position_sensitive_radical_rule",
            "scope": class_counts["requires_position_sensitive_radical_rule"],
            "recommended_gate": "audit 阝 side rule against decomposition/source evidence",
        },
        {
            "step": 3,
            "resolution_class": "requires_component_to_radical_policy_review",
            "scope": class_counts["requires_component_to_radical_policy_review"],
            "recommended_gate": "decide whether component-like labels may map to canonical radicals",
        },
        {
            "step": 4,
            "resolution_class": "requires_shape_group_disambiguation",
            "scope": class_counts["requires_shape_group_disambiguation"],
            "recommended_gate": "resolve 己/已/巳 and similar groups from standard sources",
        },
        {
            "step": 5,
            "resolution_class": "requires_radical_alias_extension_review",
            "scope": class_counts["requires_radical_alias_extension_review"],
            "recommended_gate": "extend radical alias map only with explicit evidence",
        },
        {
            "step": 6,
            "resolution_class": "requires_index_allocation_and_source_row_insertion_plan",
            "scope": class_counts["requires_index_allocation_and_source_row_insertion_plan"],
            "recommended_gate": "design insertion/index policy before adding missing 8105 rows",
        },
    ]
    checks = {
        "blocked_row_count_matches_runtime": len(queue)
        == runtime["summary"]["force_approved_not_patched_rows"]
        == EXPECTED_BLOCKED_ROWS,
        "blocked_reason_counts_match_expected": dict(reason_counts) == EXPECTED_REASON_COUNTS,
        "all_rows_keep_no_write_status": all(row["write_status"] == "NO_SOURCE_TABLE_WRITE" for row in queue),
        "all_rows_keep_no_database_status": all(row["database_status"] == "NO_DATABASE_REBUILD" for row in queue),
        "all_rows_have_resolution_class": all(row["resolution_class"] for row in queue),
        "missing_current_rows_are_missing_from_source_model": all(
            row["source_model_presence"] == "missing"
            for row in queue
            if row["block_reason"] == "missing_current_model_row"
        ),
        "non_missing_current_rows_have_recoverable_index": all(
            row["current_index_recoverable"] is True
            for row in queue
            if row["block_reason"] != "missing_current_model_row"
        ),
    }
    all_checks_pass = all(checks.values())
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "read_only_8105_runtime_blocker_resolution_plan",
            "source": str(FORCE_APPROVAL),
            "runtime_promotion_report": str(RUNTIME_PROMOTION),
            "source_model": str(SOURCE_CNBE32),
            "write_gate": "NO_SOURCE_TABLE_WRITE_NO_DATABASE_REBUILD",
        },
        "overall_status": "PASS_8105_RUNTIME_BLOCKER_RESOLUTION_PLAN_READY" if all_checks_pass else "BLOCKED",
        "summary": {
            "total_blocked_rows": len(queue),
            "block_reason_counts": dict(reason_counts),
            "resolution_class_counts": dict(class_counts),
            "source_model_presence_counts": dict(source_presence_counts),
            "current_index_recoverable_counts": dict(recoverable_index_counts),
            "source_table_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "top_profiles": {
            "structures": top_counter(structure_counts),
            "approved_radicals": top_counter(radical_counts),
        },
        "policy_order": policy_order,
        "samples": {
            "first_queue_rows": queue[:30],
            "known_rows": {
                char: next((row for row in queue if row["char"] == char), None)
                for char in ("冁", "㑇", "匜", "刁", "队", "玕")
            },
        },
        "checks": checks,
        "outputs": {
            "json_report": str(JSON_OUTPUT),
            "markdown_report": str(MD_OUTPUT),
            "csv_queue": str(CSV_OUTPUT),
        },
        "queue": queue,
        "decision": {
            "may_review_resolution_plan": all_checks_pass,
            "may_write_source_table_now": False,
            "may_rebuild_sqlite_now": False,
            "recommended_next_step": (
                "Run bounded remediation in policy order. First join missing radical/stroke evidence, "
                "then audit position-sensitive and component-to-radical mappings, and only then design "
                "an insertion/index policy for 276 8105 rows absent from the current runtime model."
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
    reason_rows = [[key, value] for key, value in summary["block_reason_counts"].items()]
    class_rows = [[key, value] for key, value in summary["resolution_class_counts"].items()]
    policy_rows = [
        [item["step"], item["resolution_class"], item["scope"], item["recommended_gate"]]
        for item in model["policy_order"]
    ]
    sample_rows = [
        [
            row["char"],
            row["unicode"],
            row["block_reason"],
            row["resolution_class"],
            row["source_model_presence"],
            row["decoded_current_index"],
        ]
        for row in model["samples"]["first_queue_rows"][:12]
    ]
    return (
        "# 8105 Runtime Blocker Resolution Plan\n\n"
        f"- Status: `{model['overall_status']}`\n"
        f"- Total blocked rows: {summary['total_blocked_rows']}\n"
        "- Source-table rows written: 0\n"
        "- SQLite rebuild allowed: false\n"
        "- Scope: remaining force-approved 8105 rows left out of runtime promotion.\n\n"
        "## Block Reasons\n\n"
        + markdown_table(["Block reason", "Rows"], reason_rows)
        + "\n\n## Resolution Classes\n\n"
        + markdown_table(["Resolution class", "Rows"], class_rows)
        + "\n\n## Recommended Policy Order\n\n"
        + markdown_table(["Step", "Resolution class", "Rows", "Gate"], policy_rows)
        + "\n\n## Sample Queue Rows\n\n"
        + markdown_table(
            ["Char", "Unicode", "Block reason", "Resolution class", "Source presence", "Current index"],
            sample_rows,
        )
        + "\n\n## Decision Boundary\n\n"
        "This report is a read-only blocker-resolution plan. It does not change "
        "`data/cnbe32.json`, does not rebuild SQLite databases, and does not "
        "turn force approval into missing numeric CNBE32 fields. A later write "
        "phase still requires explicit authorization plus passing remediation "
        "evidence for radical/stroke joins, radical mapping policy, and index "
        "allocation.\n"
    )


def main() -> None:
    model = build()
    queue = model.pop("queue")
    write_json(JSON_OUTPUT, model)
    write_csv(CSV_OUTPUT, queue)
    write_text(MD_OUTPUT, render_markdown(model))
    print(model["overall_status"])
    print(f"Blocked rows: {model['summary']['total_blocked_rows']}")
    print(f"CSV: {CSV_OUTPUT}")


if __name__ == "__main__":
    main()
