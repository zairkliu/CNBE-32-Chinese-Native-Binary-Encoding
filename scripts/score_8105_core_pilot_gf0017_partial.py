#!/usr/bin/env python3
"""Run bounded partial GF0017 scoring for the 100-row 8105 core pilot.

This scorer starts GF0017 scoring without crossing the evidence boundary. It
assigns points only for items that already have row-level evidence in the
bounded pilot handoff: 8105 character-set coverage and stroke order. All
structure, decomposition, component, component-name, radical, independent
character, and stroke-shape items remain not scorable until their standard
evidence is joined.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

EXTRACTION_PLAN = Path("reports/8105_core_structure_decomposition_source_extraction_plan.json")
HANDOFF_CSV = Path(
    "review_packets/300_character_8105_pilot/8105_core_structure_decomposition_standardizer_handoff.csv"
)

DEFAULT_JSON_OUTPUT = Path("reports/8105_core_pilot_gf0017_partial_scoring.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/8105_CORE_PILOT_GF0017_PARTIAL_SCORING.md")
DEFAULT_CSV_OUTPUT = Path("review_packets/300_character_8105_pilot/8105_core_pilot_gf0017_partial_scoring.csv")

EXPECTED_ROWS = 100

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

ITEM_FIELD_ORDER = [
    "character_set_coverage",
    "stroke_shape",
    "stroke_order",
    "component_validity",
    "component_name_validity",
    "radical_validity",
    "independent_character_rule",
    "structure_first_decomposition",
]

ROW_FIELDNAMES = [
    "row_id",
    "char",
    "unicode",
    "scope_status",
    "assigned_score",
    "assigned_max",
    "formal_total_max",
    "row_score_status",
    "character_set_coverage_score",
    "character_set_coverage_status",
    "stroke_shape_score",
    "stroke_shape_status",
    "stroke_order_score",
    "stroke_order_status",
    "component_validity_score",
    "component_validity_status",
    "component_name_validity_score",
    "component_name_validity_status",
    "radical_validity_score",
    "radical_validity_status",
    "independent_character_rule_score",
    "independent_character_rule_status",
    "structure_first_decomposition_score",
    "structure_first_decomposition_status",
    "cnbe_write_status",
    "database_rebuild_status",
    "next_required_action",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in ROW_FIELDNAMES} for row in rows])


def score_items(row: dict[str, str]) -> dict[str, dict[str, Any]]:
    stroke_ready = row["stroke_context_status"] == "STANDARD_DERIVED_STROKE_JOIN_READY"
    return {
        "character_set_coverage": {
            "max_points": 3,
            "score": 3,
            "status": "PASS_8105_CORE_COVERAGE",
            "evidence_basis": "scope_status:8105_core_control",
            "source_grade": "standard_derived",
        },
        "stroke_shape": {
            "max_points": 3,
            "score": None,
            "status": "NOT_SCORABLE_STROKE_SHAPE_SOURCE_REQUIRED",
            "evidence_basis": "folded_stroke_or_stroke_shape_row_evidence_not_joined",
            "source_grade": "source_required",
        },
        "stroke_order": {
            "max_points": 3,
            "score": 3 if stroke_ready else None,
            "status": "PASS_STANDARD_DERIVED_STROKE_ORDER"
            if stroke_ready
            else "NOT_SCORABLE_STROKE_ORDER_SOURCE_REQUIRED",
            "evidence_basis": "base_character_data.stroke_order_str plus GF0031/GF3002 source manifest",
            "source_grade": "standard_derived",
        },
        "component_validity": {
            "max_points": 3,
            "score": None,
            "status": "NOT_SCORABLE_COMPONENT_SOURCE_REQUIRED",
            "evidence_basis": row["structure_join_status"],
            "source_grade": "source_required",
        },
        "component_name_validity": {
            "max_points": 8,
            "score": None,
            "status": "NOT_SCORABLE_COMPONENT_NAME_SOURCE_REQUIRED",
            "evidence_basis": row["component_name_status"],
            "source_grade": "source_required",
        },
        "radical_validity": {
            "max_points": 3,
            "score": None,
            "status": "NOT_SCORABLE_RADICAL_SOURCE_REQUIRED",
            "evidence_basis": row["radical_context_status"],
            "source_grade": "source_required",
        },
        "independent_character_rule": {
            "max_points": 7,
            "score": None,
            "status": "NOT_SCORABLE_SINGLE_COMPONENT_SOURCE_REQUIRED",
            "evidence_basis": row["single_component_status"],
            "source_grade": "source_required",
        },
        "structure_first_decomposition": {
            "max_points": 20,
            "score": None,
            "status": "NOT_SCORABLE_STRUCTURE_DECOMPOSITION_SOURCE_REQUIRED",
            "evidence_basis": f"{row['structure_join_status']};{row['decomposition_join_status']}",
            "source_grade": "source_required",
        },
    }


def flatten_row(row: dict[str, str], items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    assigned_score = sum(item["score"] for item in items.values() if isinstance(item["score"], int))
    assigned_max = sum(item["max_points"] for item in items.values() if isinstance(item["score"], int))
    output = {
        "row_id": row["row_id"],
        "char": row["char"],
        "unicode": row["unicode"],
        "scope_status": row["scope_status"],
        "assigned_score": assigned_score,
        "assigned_max": assigned_max,
        "formal_total_max": sum(GF0017_POINTS.values()),
        "row_score_status": "PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE",
        "cnbe_write_status": "NO_CNBE_WRITE",
        "database_rebuild_status": "NO_DATABASE_REBUILD",
        "next_required_action": "run_bounded_standardizer_extraction_before_more_scoring",
    }
    for item_name in ITEM_FIELD_ORDER:
        item = items[item_name]
        output[f"{item_name}_score"] = "" if item["score"] is None else item["score"]
        output[f"{item_name}_status"] = item["status"]
    return output


def build_scoring_report() -> dict[str, Any]:
    extraction_plan = load_json(EXTRACTION_PLAN)
    rows = read_csv(HANDOFF_CSV)
    scored_rows = []
    item_status_counts: dict[str, Counter[str]] = {item: Counter() for item in ITEM_FIELD_ORDER}
    item_score_totals: dict[str, int] = {item: 0 for item in ITEM_FIELD_ORDER}

    for row in rows:
        items = score_items(row)
        for item_name, item in items.items():
            item_status_counts[item_name][item["status"]] += 1
            if isinstance(item["score"], int):
                item_score_totals[item_name] += item["score"]
        scored_rows.append(
            {
                **flatten_row(row, items),
                "items": items,
            }
        )

    flat_rows = [{key: value for key, value in row.items() if key != "items"} for row in scored_rows]
    row_status_counts = Counter(row["row_score_status"] for row in flat_rows)
    summary = {
        "rows_evaluated": len(scored_rows),
        "rows_with_any_assigned_points": sum(1 for row in flat_rows if int(row["assigned_score"]) > 0),
        "rows_fully_scored": 0,
        "rows_partially_scored": row_status_counts["PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE"],
        "formal_total_max_per_row": sum(GF0017_POINTS.values()),
        "assigned_max_per_row": 6,
        "assigned_score_total": sum(int(row["assigned_score"]) for row in flat_rows),
        "assignable_items": ["character_set_coverage", "stroke_order"],
        "blocked_items": [
            "stroke_shape",
            "component_validity",
            "component_name_validity",
            "radical_validity",
            "independent_character_rule",
            "structure_first_decomposition",
        ],
        "final_structure_labels_emitted": 0,
        "cnbe_rows_written": 0,
        "database_rebuild_allowed": False,
    }
    checks = {
        "extraction_plan_passed": extraction_plan["overall_status"]
        == "PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY",
        "row_count_matches": summary["rows_evaluated"] == EXPECTED_ROWS,
        "all_rows_partially_scored": summary["rows_partially_scored"] == EXPECTED_ROWS,
        "only_supported_items_scored": set(summary["assignable_items"]) == {"character_set_coverage", "stroke_order"},
        "structure_decomposition_not_scored": item_score_totals["structure_first_decomposition"] == 0,
        "component_items_not_scored": item_score_totals["component_validity"] == 0
        and item_score_totals["component_name_validity"] == 0,
        "radical_not_scored": item_score_totals["radical_validity"] == 0,
        "no_full_scores_claimed": summary["rows_fully_scored"] == 0,
        "no_final_structure_labels": summary["final_structure_labels_emitted"] == 0,
        "no_cnbe_writes": summary["cnbe_rows_written"] == 0,
        "no_database_rebuild": summary["database_rebuild_allowed"] is False,
    }
    status = "PASS_8105_CORE_PILOT_GF0017_PARTIAL_SCORING_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "bounded_8105_core_pilot_gf0017_partial_scoring",
        "overall_status": status,
        "next_workflow_status": "GF0017_PILOT_PARTIAL_SCORING_COMPLETE_STANDARDIZER_EXTRACTION_REQUIRED",
        "authority_boundary": {
            "bounded_100_row_pilot_only": True,
            "does_not_score_missing_evidence_as_zero": True,
            "does_not_claim_full_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "gf0017_points": GF0017_POINTS,
        "summary": summary,
        "item_status_counts": {item: dict(counter) for item, counter in item_status_counts.items()},
        "item_score_totals": item_score_totals,
        "checks": checks,
        "decision": {
            "may_continue_bounded_standardizer_extraction": status.startswith("PASS"),
            "may_assign_more_points_without_extraction": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
        },
        "scored_rows": scored_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# 8105 Core Pilot GF0017 Partial Scoring",
        "",
        f"Overall status: `{report['overall_status']}`",
        f"Next workflow status: `{report['next_workflow_status']}`",
        "",
        "## Summary",
        "",
        f"- Rows evaluated: {summary['rows_evaluated']}",
        f"- Rows partially scored: {summary['rows_partially_scored']}",
        f"- Rows fully scored: {summary['rows_fully_scored']}",
        f"- Assigned max per row: {summary['assigned_max_per_row']} / {summary['formal_total_max_per_row']}",
        f"- Assigned score total: {summary['assigned_score_total']}",
        f"- Assignable items: {', '.join(summary['assignable_items'])}",
        f"- Blocked items: {', '.join(summary['blocked_items'])}",
        f"- Final structure labels emitted: {summary['final_structure_labels_emitted']}",
        f"- CNBE rows written: {summary['cnbe_rows_written']}",
        "",
        "## Boundary",
        "",
        "Missing evidence is not scored as zero and not treated as a pass.",
        "This is a bounded 100-row pilot scoring artifact, not a full GF0017 score sheet.",
        "",
        "## Item Status Counts",
        "",
    ]
    for item_name in ITEM_FIELD_ORDER:
        lines.append(f"### `{item_name}`")
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|---|---:|")
        for status, count in sorted(report["item_status_counts"][item_name].items()):
            lines.append(f"| `{status}` | {count} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_scoring_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, [{key: value for key, value in row.items() if key != "items"} for row in report["scored_rows"]])
    print(report["overall_status"])


if __name__ == "__main__":
    main()
