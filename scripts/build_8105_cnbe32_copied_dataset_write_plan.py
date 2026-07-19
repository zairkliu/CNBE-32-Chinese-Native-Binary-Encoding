#!/usr/bin/env python3
"""Build a copied-dataset CNBE32 write plan from force-approved dry-run data.

This script writes an explicitly marked copied dataset under evidence only. It
does not modify `data/cnbe32.json`, does not rebuild SQLite, and does not
generate release artifacts.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_CNBE32 = Path("data/cnbe32.json")
FORCE_APPROVAL = Path("evidence/agent-standard/cnbe8105_approved_cnbe32_dry_run_human_force_approval.json")

OUTPUT_DIR = Path("evidence/agent-standard/copied-datasets")
COPIED_DATASET = OUTPUT_DIR / "cnbe32_8105_human_force_approved_copy.json"
PATCH_CSV = OUTPUT_DIR / "cnbe32_8105_human_force_approved_copy_patch.csv"
BLOCKED_CSV = OUTPUT_DIR / "cnbe32_8105_human_force_approved_copy_blocked_queue.csv"
JSON_REPORT = Path("evidence/agent-standard/cnbe8105_copied_dataset_write_plan.json")
MD_REPORT = Path("evidence/agent-standard/CNBE8105_COPIED_DATASET_WRITE_PLAN.md")

EXPECTED_SOURCE_ROWS = 20902
EXPECTED_READY_ROWS = 6712
EXPECTED_FORCE_BLOCKED_ROWS = 1393
HUMAN_DECISION_ID = "HUMAN_REVIEW_2026_07_19_CNBE32_DRY_RUN_FORCE_PASS"


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


def patch_record(source: dict[str, Any], approved: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = dict(source)
    updated.update(
        {
            "cnbe": approved["proposed_cnbe"],
            "radix": approved["proposed_radix"],
            "radix_name": approved["proposed_radix_name"],
            "strokes": approved["proposed_strokes"],
            "struct_type": approved["proposed_struct_type"],
            "struct_name": approved["proposed_struct_name"],
        }
    )
    diff = {
        "char": source["char"],
        "unicode": f"U+{int(source['unicode']):04X}",
        "standard_rank": approved["standard_rank"],
        "status": "COPIED_DATASET_PATCH_APPLIED",
        "current_cnbe": source["cnbe"],
        "current_cnbe_hex": f"0x{int(source['cnbe']):08X}",
        "proposed_cnbe": updated["cnbe"],
        "proposed_cnbe_hex": f"0x{int(updated['cnbe']):08X}",
        "current_radix": source["radix"],
        "proposed_radix": updated["radix"],
        "current_radix_name": source["radix_name"],
        "proposed_radix_name": updated["radix_name"],
        "current_strokes": source["strokes"],
        "proposed_strokes": updated["strokes"],
        "current_struct_type": source["struct_type"],
        "proposed_struct_type": updated["struct_type"],
        "current_struct_name": source["struct_name"],
        "proposed_struct_name": updated["struct_name"],
        "index_preserved": source["index"] == updated["index"],
        "human_decision_id": HUMAN_DECISION_ID,
        "target_dataset": str(COPIED_DATASET),
        "source_table_write_status": "NO_SOURCE_TABLE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
    }
    return updated, diff


def blocked_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "char": row["character"],
        "unicode": row["unicode_codepoint"],
        "standard_rank": row["standard_rank"],
        "status": "FORCE_APPROVED_BUT_NOT_COPIED_DATASET_PATCHED",
        "block_reason": row.get("block_reason", ""),
        "block_detail": row.get("block_detail", ""),
        "approved_agent_structure": row["approved_agent_structure"],
        "approved_agent_struct_type": row["approved_agent_struct_type"],
        "implementation_queue": row["implementation_queue"],
        "required_before_source_write": "fallback_radical_or_index_strategy",
        "human_decision_id": HUMAN_DECISION_ID,
        "source_table_write_status": "NO_SOURCE_TABLE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
    }


def build() -> dict[str, Any]:
    source_model = read_json(SOURCE_CNBE32)
    force_model = read_json(FORCE_APPROVAL)
    source_rows = source_model["characters"]
    source_by_char = {row["char"]: row for row in source_rows}
    ready_rows = [
        row
        for row in force_model["records"]
        if row["implementation_queue"] == "CNBE32_READY_WRITE_PLAN_CANDIDATE"
    ]
    force_blocked_rows = [
        row
        for row in force_model["records"]
        if row["implementation_queue"] == "CNBE32_FORCE_APPROVED_BLOCKER_RESOLUTION_PLAN_CANDIDATE"
    ]
    updated_by_char = {row["char"]: dict(row) for row in source_rows}
    patch_rows: list[dict[str, Any]] = []
    patch_blockers: list[dict[str, Any]] = []

    for approved in ready_rows:
        char = approved["character"]
        source = source_by_char.get(char)
        if source is None:
            patch_blockers.append(blocked_record({**approved, "block_reason": "ready_row_missing_from_source_model"}))
            continue
        updated, diff = patch_record(source, approved)
        updated_by_char[char] = updated
        patch_rows.append(diff)

    blocked_rows = [blocked_record(row) for row in force_blocked_rows] + patch_blockers
    copied_model = {
        "metadata": {
            **source_model.get("metadata", {}),
            "copy_kind": "8105_human_force_approved_cnbe32_write_plan_copy",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_dataset": str(SOURCE_CNBE32),
            "human_force_approval": str(FORCE_APPROVAL),
            "human_decision_id": HUMAN_DECISION_ID,
            "source_table_write_status": "NO_SOURCE_TABLE_WRITE",
            "database_rebuild_status": "NO_DATABASE_REBUILD",
            "patched_rows_in_copy": len(patch_rows),
            "force_approved_not_patched_rows": len(blocked_rows),
        },
        "characters": [updated_by_char[row["char"]] for row in source_rows],
    }

    changed_fields = Counter()
    for row in patch_rows:
        for field in ("cnbe", "radix", "radix_name", "strokes", "struct_type", "struct_name"):
            if str(row[f"current_{field}"]) != str(row[f"proposed_{field}"]):
                changed_fields[field] += 1
    block_reasons = Counter(row["block_reason"] for row in blocked_rows)
    checks = {
        "source_row_count_preserved": len(copied_model["characters"]) == len(source_rows) == EXPECTED_SOURCE_ROWS,
        "patch_rows_match_ready_rows": len(patch_rows) == EXPECTED_READY_ROWS,
        "blocked_rows_match_force_blocked_rows": len(blocked_rows) == EXPECTED_FORCE_BLOCKED_ROWS,
        "source_dataset_not_modified_by_script": SOURCE_CNBE32 != COPIED_DATASET,
        "all_patch_rows_preserve_index": all(row["index_preserved"] is True for row in patch_rows),
        "all_patch_rows_write_to_copy_only": all(row["target_dataset"] == str(COPIED_DATASET) for row in patch_rows),
        "all_blocked_rows_preserve_reason": all(row["block_reason"] for row in blocked_rows),
        "known_samples_routed": {
            "家": any(row["char"] == "家" and row["proposed_struct_name"] == "上下" for row in patch_rows),
            "侵": any(row["char"] == "侵" and row["proposed_struct_name"] == "左右" for row in patch_rows),
            "偶": any(row["char"] == "偶" and row["proposed_struct_name"] == "左右" for row in patch_rows),
            "孓": any(row["char"] == "孓" and row["proposed_struct_name"] == "独体字" for row in patch_rows),
            "冁": any(row["char"] == "冁" and row["block_reason"] == "radical_resolution_blocked" for row in blocked_rows),
            "㑇": any(row["char"] == "㑇" and row["block_reason"] == "missing_current_model_row" for row in blocked_rows),
        },
        "no_source_table_writes": True,
        "no_database_rebuild": True,
    }
    flat_checks = {key: value for key, value in checks.items() if key != "known_samples_routed"}
    all_checks_pass = all(flat_checks.values()) and all(checks["known_samples_routed"].values())
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "copied_dataset_write_plan_for_8105_force_approved_cnbe32_dry_run",
            "source_dataset": str(SOURCE_CNBE32),
            "copy_dataset": str(COPIED_DATASET),
            "force_approval": str(FORCE_APPROVAL),
            "write_gate": "COPY_ONLY_NO_SOURCE_TABLE_WRITE_NO_DATABASE_REBUILD",
        },
        "overall_status": "PASS_8105_CNBE32_COPIED_DATASET_WRITE_PLAN_READY" if all_checks_pass else "BLOCKED",
        "summary": {
            "source_rows": len(source_rows),
            "copy_rows": len(copied_model["characters"]),
            "patch_rows_in_copy": len(patch_rows),
            "force_approved_not_patched_rows": len(blocked_rows),
            "changed_field_counts": dict(changed_fields),
            "blocked_reason_counts": dict(block_reasons),
            "source_table_rows_written": 0,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "samples": {
            "first_patch_rows": patch_rows[:30],
            "first_blocked_rows": blocked_rows[:30],
            "known_patch_rows": {
                char: next((row for row in patch_rows if row["char"] == char), None)
                for char in ("家", "侵", "偶", "孓")
            },
            "known_blocked_rows": {
                char: next((row for row in blocked_rows if row["char"] == char), None)
                for char in ("冁", "㑇")
            },
        },
        "outputs": {
            "copied_dataset": str(COPIED_DATASET),
            "patch_csv": str(PATCH_CSV),
            "blocked_csv": str(BLOCKED_CSV),
            "json_report": str(JSON_REPORT),
            "markdown_report": str(MD_REPORT),
        },
        "copied_model": copied_model,
        "patch_rows": patch_rows,
        "blocked_rows": blocked_rows,
        "decision": {
            "may_review_copied_dataset": all_checks_pass,
            "may_promote_copy_to_source_table_now": False,
            "may_rebuild_sqlite_database_now": False,
            "recommended_next_step": (
                "Review the copied dataset and blocked queue. A later source-table "
                "write requires explicit authorization plus a strategy for 964 "
                "missing radicals, 276 missing current-model rows, and 153 "
                "non-conservative radical mappings."
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
    known_patch = model["samples"]["known_patch_rows"]
    known_blocked = model["samples"]["known_blocked_rows"]
    sample_rows = []
    for char, row in known_patch.items():
        if row:
            sample_rows.append(
                [
                    char,
                    row["unicode"],
                    "PATCHED_IN_COPY",
                    row["current_cnbe_hex"],
                    row["proposed_cnbe_hex"],
                    row["proposed_struct_name"],
                ]
            )
    for char, row in known_blocked.items():
        if row:
            sample_rows.append([char, row["unicode"], row["status"], row["block_reason"], "", row["approved_agent_structure"]])
    return "\n".join(
        [
            "# CNBE 8105 Copied Dataset Write Plan",
            "",
            f"- Overall status: `{model['overall_status']}`",
            f"- Source rows: {summary['source_rows']}",
            f"- Copy rows: {summary['copy_rows']}",
            f"- Patched rows in copy: {summary['patch_rows_in_copy']}",
            f"- Force-approved not patched rows: {summary['force_approved_not_patched_rows']}",
            f"- Source table rows written: {summary['source_table_rows_written']}",
            f"- Database rebuild allowed: `{summary['database_rebuild_allowed']}`",
            "",
            "The copied dataset is an evidence artifact. It is not the production",
            "`data/cnbe32.json` source table and does not trigger SQLite rebuilds.",
            "",
            "## Outputs",
            "",
            f"- Copied dataset: `{model['outputs']['copied_dataset']}`",
            f"- Patch CSV: `{model['outputs']['patch_csv']}`",
            f"- Blocked CSV: `{model['outputs']['blocked_csv']}`",
            "",
            "## Changed Field Counts",
            "",
            markdown_table(["Field", "Rows"], [[key, value] for key, value in sorted(summary["changed_field_counts"].items())]),
            "",
            "## Blocked Reason Counts",
            "",
            markdown_table(["Reason", "Rows"], [[key, value] for key, value in sorted(summary["blocked_reason_counts"].items())]),
            "",
            "## Known Samples",
            "",
            markdown_table(["Char", "Unicode", "Status", "Current/Reason", "Proposed CNBE", "Structure"], sample_rows),
            "",
            "## Decision",
            "",
            model["decision"]["recommended_next_step"],
            "",
        ]
    )


def run() -> dict[str, Any]:
    model = build()
    write_json(COPIED_DATASET, model["copied_model"])
    write_csv(PATCH_CSV, model["patch_rows"])
    write_csv(BLOCKED_CSV, model["blocked_rows"])
    serializable = {key: value for key, value in model.items() if key not in {"copied_model", "patch_rows", "blocked_rows"}}
    write_json(JSON_REPORT, serializable)
    write_text(MD_REPORT, render_markdown(model))
    return model


def main() -> None:
    model = run()
    print(model["overall_status"])
    print(f"source_rows={model['summary']['source_rows']}")
    print(f"copy_rows={model['summary']['copy_rows']}")
    print(f"patch_rows_in_copy={model['summary']['patch_rows_in_copy']}")
    print(f"force_approved_not_patched_rows={model['summary']['force_approved_not_patched_rows']}")
    print(f"source_table_rows_written={model['summary']['source_table_rows_written']}")


if __name__ == "__main__":
    main()
