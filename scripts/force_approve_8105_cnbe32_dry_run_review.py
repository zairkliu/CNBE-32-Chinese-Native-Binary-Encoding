#!/usr/bin/env python3
"""Record human force-approval for the approved 8105 CNBE32 dry-run review.

The force approval accepts the existing dry-run review and blocker queues for
next-step planning. It does not invent missing CNBE32 values and does not write
`data/cnbe32.json` or rebuild SQLite databases.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DRY_RUN_JSON = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_patch.json")
JSON_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_human_force_approval.json")
CSV_OUTPUT = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_human_force_approval.csv")
MD_OUTPUT = Path("evidence/agent-standard/CNBE8105_APPROVED_CNBE32_DRY_RUN_HUMAN_FORCE_APPROVAL.md")

HUMAN_DECISION_ID = "HUMAN_REVIEW_2026_07_19_CNBE32_DRY_RUN_FORCE_PASS"
HUMAN_DECISION_TEXT = "现有的人工审核过了，强制通过"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def approval_record(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    original_status = row["status"]
    out["original_dry_run_status"] = original_status
    out["human_decision_id"] = HUMAN_DECISION_ID
    out["human_decision_text"] = HUMAN_DECISION_TEXT
    out["human_force_approval_status"] = "HUMAN_FORCE_APPROVED_FOR_NEXT_STEP_PLANNING"
    out["implementation_queue"] = (
        "CNBE32_READY_WRITE_PLAN_CANDIDATE"
        if original_status == "DRY_RUN_READY"
        else "CNBE32_FORCE_APPROVED_BLOCKER_RESOLUTION_PLAN_CANDIDATE"
    )
    out["force_approval_boundary"] = "APPROVES_REVIEW_STATUS_NOT_MISSING_NUMERIC_FIELDS"
    out["source_table_write_status"] = "NO_SOURCE_TABLE_WRITE"
    out["cnbe32_source_write_status"] = "NO_CNBE32_SOURCE_WRITE"
    out["database_rebuild_status"] = "NO_DATABASE_REBUILD"
    return out


def build() -> dict[str, Any]:
    dry_run = read_json(DRY_RUN_JSON)
    records = [approval_record(row) for row in dry_run["records"]]
    status_counts = Counter(row["original_dry_run_status"] for row in records)
    queue_counts = Counter(row["implementation_queue"] for row in records)
    block_counts = Counter(row.get("block_reason", "") for row in records if row["original_dry_run_status"] != "DRY_RUN_READY")
    known = {
        char: next(row for row in records if row["character"] == char)
        for char in ("家", "侵", "偶", "冁", "孓", "㑇")
    }
    checks = {
        "row_count_matches_dry_run": len(records) == dry_run["summary"]["total_rows"] == 8105,
        "all_rows_human_force_approved": all(
            row["human_force_approval_status"] == "HUMAN_FORCE_APPROVED_FOR_NEXT_STEP_PLANNING"
            for row in records
        ),
        "original_block_reasons_preserved": dict(block_counts) == dry_run["summary"]["block_reason_counts"],
        "ready_rows_preserved": status_counts["DRY_RUN_READY"] == dry_run["summary"]["dry_run_ready_rows"],
        "blocked_rows_preserved": status_counts["DRY_RUN_BLOCKED"] == dry_run["summary"]["dry_run_blocked_rows"],
        "known_samples_preserved": known["冁"]["block_reason"] == "radical_resolution_blocked"
        and known["㑇"]["block_reason"] == "missing_current_model_row"
        and known["孓"]["approved_agent_structure"] == "独体字",
        "no_source_table_writes": all(row["source_table_write_status"] == "NO_SOURCE_TABLE_WRITE" for row in records),
        "no_cnbe32_source_writes": all(row["cnbe32_source_write_status"] == "NO_CNBE32_SOURCE_WRITE" for row in records),
        "no_database_rebuild": all(row["database_rebuild_status"] == "NO_DATABASE_REBUILD" for row in records),
    }
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "human_force_approval_for_8105_cnbe32_dry_run_review",
            "source_dry_run": str(DRY_RUN_JSON),
            "human_decision_id": HUMAN_DECISION_ID,
            "write_gate": "NO_SOURCE_TABLE_WRITE_NO_CNBE32_SOURCE_WRITE_NO_DATABASE_REBUILD",
        },
        "overall_status": "PASS_8105_CNBE32_DRY_RUN_HUMAN_FORCE_APPROVED"
        if all(checks.values())
        else "BLOCKED",
        "human_decision": {
            "decision_id": HUMAN_DECISION_ID,
            "decision_text": HUMAN_DECISION_TEXT,
            "scope": "Accept current human-reviewed dry-run and blocker queues for next-step planning.",
            "does_not_authorize": [
                "inventing missing CNBE32 values",
                "overwriting data/cnbe32.json",
                "rebuilding SQLite databases",
                "release, tag, or PyPI work",
            ],
        },
        "summary": {
            "total_rows": len(records),
            "force_approved_rows": len(records),
            "original_ready_rows": status_counts["DRY_RUN_READY"],
            "original_blocked_rows": status_counts["DRY_RUN_BLOCKED"],
            "implementation_queue_counts": dict(queue_counts),
            "preserved_block_reason_counts": dict(block_counts),
            "source_table_rows_written": 0,
            "cnbe32_source_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "known_samples": known,
        "records": records,
        "outputs": {
            "json": str(JSON_OUTPUT),
            "csv": str(CSV_OUTPUT),
            "markdown": str(MD_OUTPUT),
        },
        "decision": {
            "may_start_next_step_write_plan_design": all(checks.values()),
            "may_write_data_cnbe32_json_now": False,
            "may_rebuild_sqlite_database_now": False,
            "recommended_next_step": (
                "Design a copied-dataset implementation plan. Ready rows may be "
                "mapped into a copied CNBE32 table; force-approved blocker rows "
                "must receive explicit fallback rules for radical, missing index, "
                "or insertion strategy before any write execution."
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
                row["original_dry_run_status"],
                row.get("block_reason", ""),
                row["implementation_queue"],
            ]
        )
    return "\n".join(
        [
            "# CNBE 8105 CNBE32 Dry-Run Human Force Approval",
            "",
            f"- Overall status: `{model['overall_status']}`",
            f"- Human decision: {model['human_decision']['decision_text']}",
            f"- Total rows: {summary['total_rows']}",
            f"- Force-approved rows: {summary['force_approved_rows']}",
            f"- Original ready rows: {summary['original_ready_rows']}",
            f"- Original blocked rows: {summary['original_blocked_rows']}",
            f"- Source table rows written: {summary['source_table_rows_written']}",
            f"- CNBE32 source rows written: {summary['cnbe32_source_rows_written']}",
            f"- Database rebuild allowed: `{summary['database_rebuild_allowed']}`",
            "",
            "This artifact records a human approval decision. It approves the",
            "review status for next-step planning, but does not fabricate missing",
            "numeric CNBE32 fields and does not write source data.",
            "",
            "## Implementation Queues",
            "",
            markdown_table(
                ["Queue", "Rows"],
                [[key, value] for key, value in sorted(summary["implementation_queue_counts"].items())],
            ),
            "",
            "## Preserved Block Reasons",
            "",
            markdown_table(
                ["Reason", "Rows"],
                [[key, value] for key, value in sorted(summary["preserved_block_reason_counts"].items())],
            ),
            "",
            "## Known Samples",
            "",
            markdown_table(
                ["Char", "Unicode", "Original status", "Block reason", "Queue"],
                known_rows,
            ),
            "",
            "## Decision",
            "",
            model["decision"]["recommended_next_step"],
            "",
        ]
    )


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
    print(f"force_approved_rows={model['summary']['force_approved_rows']}")
    print(f"original_ready_rows={model['summary']['original_ready_rows']}")
    print(f"original_blocked_rows={model['summary']['original_blocked_rows']}")
    print(f"cnbe32_source_rows_written={model['summary']['cnbe32_source_rows_written']}")


if __name__ == "__main__":
    main()
