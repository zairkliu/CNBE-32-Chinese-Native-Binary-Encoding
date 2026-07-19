#!/usr/bin/env python3
"""Score GF0017 readiness from the existing unified Hanzi evidence index.

This script intentionally does not regenerate the full Unicode catalog. It
uses only the schema-coded rows and profiles already present in
reports/unified_hanzi_evidence_index.json.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

INDEX_REPORT = Path("reports/unified_hanzi_evidence_index.json")
INDEX_AUDIT_REPORT = Path("reports/unified_hanzi_evidence_index_audit.json")
DEFAULT_JSON_OUTPUT = Path("reports/unified_hanzi_gf0017_scoring_from_index.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/UNIFIED_HANZI_GF0017_SCORING_FROM_INDEX.md")

GF0017_POINTS = {
    "character_set_coverage": 3,
    "stroke_shape": 3,
    "stroke_order": 3,
    "component_validity": 3,
    "component_name_validity": 8,
    "radical_validity": 3,
    "independent_character_rule": 7,
    "structure_first_decomposition": 20,
}

EXPECTED_ROWS = 97_686
EXPECTED_8105_ROWS = 8_105


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


def source_status_to_scoring_status(status: str | None) -> str:
    if status in {"SOURCE_GAP", "SOURCE_GAP_NOT_SCORABLE"}:
        return "NOT_SCORABLE_SOURCE_GAP"
    if status in {"SOURCE_EVIDENCE_REQUIRED", "ROW_LEVEL_EVIDENCE_JOIN_PENDING"}:
        return "NOT_SCORABLE_EVIDENCE_REQUIRED"
    if status in {"EVIDENCE_GAP", "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP"}:
        return "NOT_SCORABLE_EVIDENCE_GAP"
    if status in {"PASS", "READY_FOR_ROW_LEVEL_VALIDATION"}:
        return "READY_FOR_VALIDATED_SCORE"
    return "NOT_SCORABLE_UNKNOWN_STATUS"


def score_item_from_existing_index(
    *,
    item: str,
    scope: str,
    source_join_status: str | None,
    agent_evidence_status: str | None,
) -> dict[str, Any]:
    max_points = GF0017_POINTS[item]
    if item == "character_set_coverage" and scope == "8105_core":
        return {
            "max_points": max_points,
            "score": max_points,
            "status": "PASS_8105_CORE_COVERAGE",
            "source_status": source_join_status,
            "agent_evidence_status": agent_evidence_status,
            "evidence_basis": "catalog_scope:8105_core",
            "can_assign_points": True,
        }
    status = source_status_to_scoring_status(agent_evidence_status or source_join_status)
    return {
        "max_points": max_points,
        "score": None,
        "status": status,
        "source_status": source_join_status,
        "agent_evidence_status": agent_evidence_status,
        "evidence_basis": "existing_unified_index_profile_only",
        "can_assign_points": False,
    }


def classify_row(items: dict[str, dict[str, Any]]) -> str:
    if all(item["can_assign_points"] for item in items.values()):
        return "FULLY_SCORED"
    if any(item["can_assign_points"] for item in items.values()):
        return "PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE"
    return "NOT_SCORABLE_FROM_CURRENT_INDEX"


def build_scoring_report() -> dict[str, Any]:
    index_report = load_json(INDEX_REPORT)
    audit_report = load_json(INDEX_AUDIT_REPORT)
    positions = schema_index(index_report["index_schema"])
    source_profiles = index_report["profiles"]["source_join_item_statuses"]
    agent_profiles = index_report["profiles"]["agent_evidence_item_statuses"]

    item_status_counts: dict[str, Counter[str]] = {item: Counter() for item in GF0017_POINTS}
    row_score_status_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    total_assigned_points = 0
    rows_with_any_points = 0
    rows_fully_scored = 0
    rows_not_scorable = 0
    sample_rows: dict[str, dict[str, Any]] = {}

    for unicode_label, row in index_report["index"].items():
        char = row[positions["char"]]
        scope = row[positions["catalog_scope"]]
        source_profile = source_profiles[row[positions["source_join_profile_id"]]]
        agent_profile = agent_profiles[row[positions["agent_evidence_profile_id"]]]
        scope_counts[scope] += 1

        items = {
            item: score_item_from_existing_index(
                item=item,
                scope=scope,
                source_join_status=source_profile.get(item),
                agent_evidence_status=agent_profile.get(item),
            )
            for item in GF0017_POINTS
        }
        for item, item_result in items.items():
            item_status_counts[item][item_result["status"]] += 1

        assigned_score = sum(result["score"] for result in items.values() if isinstance(result["score"], int))
        assigned_max = sum(result["max_points"] for result in items.values() if result["can_assign_points"])
        row_status = classify_row(items)
        row_score_status_counts[row_status] += 1
        total_assigned_points += assigned_score
        rows_with_any_points += int(assigned_max > 0)
        rows_fully_scored += int(row_status == "FULLY_SCORED")
        rows_not_scorable += int(row_status == "NOT_SCORABLE_FROM_CURRENT_INDEX")

        if unicode_label in index_report["samples"]:
            sample_rows[unicode_label] = {
                "unicode": unicode_label,
                "char": char,
                "catalog_scope": scope,
                "score_status": row_status,
                "assigned_score": assigned_score,
                "assigned_max": assigned_max,
                "formal_total_max": sum(GF0017_POINTS.values()),
                "items": items,
            }

    checks = {
        "uses_existing_unified_index_only": True,
        "does_not_regenerate_unicode_identity": True,
        "index_audit_passed": audit_report["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_AUDITED",
        "row_count_match": len(index_report["index"]) == EXPECTED_ROWS,
        "scope_counts_match": scope_counts["8105_core"] == EXPECTED_8105_ROWS,
        "no_cnbe_row_writes": True,
        "no_database_rebuild": True,
        "no_final_structure_labels": True,
    }
    status = "PASS_GF0017_SCORING_FROM_EXISTING_INDEX_WITH_SOURCE_GAPS" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "formal_gf0017_scoring_from_existing_unified_index",
        "overall_status": status,
        "next_workflow_status": "GF0017_SOURCE_EVIDENCE_REPAIR_REQUIRED_BEFORE_FULL_SCORING",
        "authority_boundary": {
            "uses_existing_unified_index_only": True,
            "does_not_regenerate_full_unicode_catalog": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_emit_final_structure_labels": True,
        },
        "gf0017_points": GF0017_POINTS,
        "summary": {
            "total_rows_evaluated": len(index_report["index"]),
            "catalog_scope_counts": dict(scope_counts),
            "row_score_status_counts": dict(row_score_status_counts),
            "rows_with_any_assigned_points": rows_with_any_points,
            "rows_fully_scored": rows_fully_scored,
            "rows_not_scorable_from_current_index": rows_not_scorable,
            "total_assigned_points_across_rows": total_assigned_points,
            "formal_max_points_per_row": sum(GF0017_POINTS.values()),
            "assigned_item_policy": (
                "Only character_set_coverage for existing 8105_core rows is "
                "assigned from the current index. All other items remain "
                "unscored until source evidence is materialized."
            ),
        },
        "item_status_counts": {
            item: dict(counter)
            for item, counter in item_status_counts.items()
        },
        "checks": checks,
        "samples": sample_rows,
        "decision": {
            "may_continue_source_evidence_repair": status.startswith("PASS"),
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "may_claim_full_gf0017_scores": False,
            "reason": (
                "Formal scoring has started from the existing index, but most "
                "GF0017 items remain not scorable because row-level evidence is "
                "not yet materialized in the index."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GF0017 Scoring From Existing Unified Index",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Rows evaluated: {report['summary']['total_rows_evaluated']}",
        f"- Rows with any assigned points: {report['summary']['rows_with_any_assigned_points']}",
        f"- Fully scored rows: {report['summary']['rows_fully_scored']}",
        f"- Rows not scorable from current index: {report['summary']['rows_not_scorable_from_current_index']}",
        "",
        "This run did not regenerate the full Unicode catalog. It used the",
        "existing schema-coded unified evidence index only.",
        "",
        "## Boundary",
        "",
        "- CNBE rows were not written.",
        "- SQLite databases were not rebuilt.",
        "- Final structure labels were not emitted.",
        "- Missing source evidence was not converted into a numeric zero or pass.",
        "",
        "## Row Score Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["row_score_status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Item Status Counts", ""])
    for item, counts in report["item_status_counts"].items():
        lines.append(f"### `{item}`")
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|---|---:|")
        for status, count in sorted(counts.items()):
            lines.append(f"| `{status}` | {count} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_scoring_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"rows={report['summary']['total_rows_evaluated']}")
    print(f"fully_scored={report['summary']['rows_fully_scored']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
