#!/usr/bin/env python3
"""Materialize read-only structure/decomposition evidence status from the index.

This is the first GF0017 source-evidence repair package. It does not assign
points, emit final structure labels, write CNBE rows, or rebuild databases.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

UNIFIED_INDEX = Path("reports/unified_hanzi_evidence_index.json")
REPAIR_PLAN = Path("reports/gf0017_source_evidence_repair_plan_from_index.json")
PHASE1_PARSER = Path("reports/structure_decomposition_evidence_parser.json")
DICTIONARY_GAP = Path("reports/structure_decomposition_dictionary_gap_extractor.json")
WIKI_CROSS_REFERENCE = Path("reports/wikipedia_structure_cross_reference_index.json")
FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")

DEFAULT_JSON_OUTPUT = Path("reports/gf0017_structure_decomposition_evidence_repair_from_index.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/GF0017_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_FROM_INDEX.md")

SAMPLE_UNICODES = ["U+4E00", "U+5BB6", "U+946B", "U+3400", "U+3401", "U+323AF"]


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


def row_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["unicode"]: row for row in report.get("row_records", [])}


def structure_status(
    *,
    scope: str,
    phase1_row: dict[str, Any] | None,
    dictionary_row: dict[str, Any] | None,
    wiki_row: dict[str, Any] | None,
    feature_row: dict[str, Any] | None,
    dictionary_source_count: int,
    has_origin_context: bool,
    wiki_hit_count: int,
) -> tuple[str, str, str]:
    if scope == "8105_core":
        return (
            "CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED",
            "standard_derived_join_pending",
            "join_8105_structure_decomposition_sources",
        )
    if phase1_row:
        evidence_status = phase1_row.get("evidence_status")
        if evidence_status == "STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW":
            return (
                "STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY",
                phase1_row.get("source_grade", "cross_reference"),
                "human_review_source_context",
            )
        if evidence_status == "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED":
            return (
                "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED",
                phase1_row.get("source_grade", "cross_reference"),
                "repair_partial_structure_context",
            )
    if dictionary_source_count or has_origin_context or wiki_hit_count:
        return (
            "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT",
            "cross_reference_context",
            "promote_or_reject_review_context_after_source_check",
        )
    if dictionary_row and dictionary_row.get("review_status") != "NO_DICTIONARY_REVIEW_HIT":
        return (
            "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT",
            dictionary_row.get("source_grade", "cross_reference"),
            "review_dictionary_context",
        )
    if wiki_row and wiki_row.get("wiki_review_status") == "WIKI_CROSS_REFERENCE_HIT":
        return (
            "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_WIKI_CONTEXT",
            "lowest_tier_cross_reference",
            "review_wiki_context_only",
        )
    if feature_row:
        return (
            "STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY",
            "agent_standard_candidate_not_national_standard",
            feature_row.get("allowed_next_action", "human_review_or_agent_rule_learning_design_only"),
        )
    return (
        "STRUCTURE_DECOMPOSITION_SOURCE_GAP_NO_CONTEXT",
        "unresolved",
        "source_acquisition_required",
    )


def build_repair_report() -> dict[str, Any]:
    unified = load_json(UNIFIED_INDEX)
    repair_plan = load_json(REPAIR_PLAN)
    phase1 = row_map(load_json(PHASE1_PARSER))
    dictionary = row_map(load_json(DICTIONARY_GAP))
    wiki = row_map(load_json(WIKI_CROSS_REFERENCE))
    feature = row_map(load_json(FEATURE_TABLE))
    positions = schema_index(unified["index_schema"])

    row_schema = [
        "char",
        "catalog_scope",
        "structure_evidence_status",
        "source_grade",
        "next_action",
        "phase1_status",
        "dictionary_review_status",
        "wiki_review_status",
        "feature_review_queue",
        "dictionary_source_count",
        "has_origin_context",
        "wiki_hit_count",
    ]
    rows: dict[str, list[Any]] = {}
    samples: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    source_grade_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()

    for unicode_label, row in unified["index"].items():
        char = row[positions["char"]]
        scope = row[positions["catalog_scope"]]
        dictionary_source_count = row[positions["dictionary_source_count"]]
        has_origin_context = row[positions["has_origin_context"]]
        wiki_hit_count = row[positions["wiki_hit_count"]]
        phase1_row = phase1.get(unicode_label)
        dictionary_row = dictionary.get(unicode_label)
        wiki_row = wiki.get(unicode_label)
        feature_row = feature.get(unicode_label)
        status, source_grade, next_action = structure_status(
            scope=scope,
            phase1_row=phase1_row,
            dictionary_row=dictionary_row,
            wiki_row=wiki_row,
            feature_row=feature_row,
            dictionary_source_count=dictionary_source_count,
            has_origin_context=has_origin_context,
            wiki_hit_count=wiki_hit_count,
        )
        status_counts[status] += 1
        source_grade_counts[source_grade] += 1
        next_action_counts[next_action] += 1
        rows[unicode_label] = [
            char,
            scope,
            status,
            source_grade,
            next_action,
            (phase1_row or {}).get("evidence_status"),
            (dictionary_row or {}).get("review_status"),
            (wiki_row or {}).get("wiki_review_status"),
            (feature_row or {}).get("review_queue"),
            dictionary_source_count,
            has_origin_context,
            wiki_hit_count,
        ]
        if unicode_label in SAMPLE_UNICODES:
            samples[unicode_label] = {
                "unicode": unicode_label,
                "char": char,
                "catalog_scope": scope,
                "structure_evidence_status": status,
                "source_grade": source_grade,
                "next_action": next_action,
                "phase1_status": (phase1_row or {}).get("evidence_status"),
                "dictionary_review_status": (dictionary_row or {}).get("review_status"),
                "wiki_review_status": (wiki_row or {}).get("wiki_review_status"),
                "feature_review_queue": (feature_row or {}).get("review_queue"),
                "score": None,
                "score_status": "NOT_SCORED_STRUCTURE_EVIDENCE_REPAIR_ONLY",
                "final_structure_label": None,
                "can_assign_points": False,
            }

    checks = {
        "repair_plan_ready": repair_plan["overall_status"] == "PASS_GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_READY",
        "uses_existing_unified_index_only": True,
        "row_count_match": len(rows) == unified["summary"]["total_entries"],
        "does_not_regenerate_unicode": True,
        "does_not_assign_points": True,
        "does_not_emit_final_structure_labels": True,
        "does_not_write_cnbe_rows": True,
        "does_not_rebuild_database": True,
    }
    status = "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_structure_decomposition_evidence_repair_from_existing_index",
        "overall_status": status,
        "next_workflow_status": "STRUCTURE_DECOMPOSITION_REVIEW_REQUIRED_NO_SCORING",
        "authority_boundary": {
            "uses_existing_unified_index_only": True,
            "does_not_regenerate_full_unicode_catalog": True,
            "does_not_assign_gf0017_points": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
        },
        "summary": {
            "total_rows": len(rows),
            "status_counts": dict(status_counts),
            "source_grade_counts": dict(source_grade_counts),
            "next_action_counts": dict(next_action_counts),
            "reviewable_or_partial_rows": (
                status_counts["STRUCTURE_DECOMPOSITION_REVIEWABLE_CONTEXT_READY"]
                + status_counts["STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED"]
            ),
            "source_gap_rows": (
                status_counts["STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT"]
                + status_counts["STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_DICTIONARY_CONTEXT"]
                + status_counts["STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_WIKI_CONTEXT"]
                + status_counts["STRUCTURE_DECOMPOSITION_SOURCE_GAP_NO_CONTEXT"]
            ),
            "core_8105_standard_join_required_rows": status_counts[
                "CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED"
            ],
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_scoring_allowed": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
        },
        "row_schema": row_schema,
        "row_records": rows,
        "samples": samples,
        "checks": checks,
        "decision": {
            "may_start_structure_decomposition_review_packet": status.startswith("PASS"),
            "may_assign_gf0017_points": False,
            "may_emit_final_structure_labels": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "Structure/decomposition evidence statuses have been materialized "
                "from existing reports. They support review queue planning but "
                "do not yet authorize scoring or final labels."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# GF0017 Structure/Decomposition Evidence Repair From Existing Index",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total rows: {report['summary']['total_rows']}",
        f"- Reviewable or partial rows: {report['summary']['reviewable_or_partial_rows']}",
        f"- Source-gap rows: {report['summary']['source_gap_rows']}",
        f"- 8105 standard-join required rows: {report['summary']['core_8105_standard_join_required_rows']}",
        f"- Score values assigned: {report['summary']['score_values_assigned']}",
        f"- Final structure labels emitted: {report['summary']['final_structure_labels_emitted']}",
        "",
        "This report does not regenerate Unicode identity, assign GF0017 points,",
        "emit final structure labels, write CNBE rows, or rebuild databases.",
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(report["summary"]["status_counts"].items()):
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "## Samples", ""])
    for unicode_label, sample in report["samples"].items():
        lines.extend(
            [
                f"### {sample['char']} `{unicode_label}`",
                "",
                f"- Scope: `{sample['catalog_scope']}`",
                f"- Structure evidence status: `{sample['structure_evidence_status']}`",
                f"- Source grade: `{sample['source_grade']}`",
                f"- Next action: `{sample['next_action']}`",
                f"- Score status: `{sample['score_status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed step is review-packet planning for structure and",
            "decomposition evidence. Scoring and encoding writes remain blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    report = build_repair_report()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"rows={report['summary']['total_rows']}")
    print(f"reviewable_or_partial={report['summary']['reviewable_or_partial_rows']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
