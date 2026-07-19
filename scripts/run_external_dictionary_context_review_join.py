#!/usr/bin/env python3
"""Join staged dictionary context to review targets without scoring or import."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

STAGING_DB = Path("build/dictionary_context_staging/dictionary_context_entries.sqlite")
HUMAN_REVIEW_PACKET = Path("reports/remaining_structure_agent_standard_human_review_packet.json")
FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")

DEFAULT_JSON_OUTPUT = Path("reports/external_dictionary_context_review_join.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/EXTERNAL_DICTIONARY_CONTEXT_REVIEW_JOIN.md")
DEFAULT_CSV_OUTPUT = Path("reports/external_dictionary_context_human_review_join.csv")

HUMAN_ROWS_EXPECTED = 150
REMAINING_ROWS_EXPECTED = 73_831
PREVIEW_LIMIT = 180
REMAINING_SAMPLE_LIMIT = 200


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_context_by_char() -> dict[str, list[dict[str, Any]]]:
    with sqlite3.connect(STAGING_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            select source_id, source_repo, source_commit, license, source_grade,
                   char, unicode, content_preview, import_status
            from dictionary_context_entries
            order by char, source_id
            """
        ).fetchall()
    context: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        context.setdefault(row["char"], []).append(
            {
                "source_id": row["source_id"],
                "source_repo": row["source_repo"],
                "source_commit": row["source_commit"],
                "license": row["license"],
                "source_grade": row["source_grade"],
                "unicode": row["unicode"],
                "content_preview": (row["content_preview"] or "")[:PREVIEW_LIMIT],
                "import_status": row["import_status"],
            }
        )
    return context


def context_class(entries: list[dict[str, Any]]) -> str:
    source_count = len({entry["source_id"] for entry in entries})
    if source_count >= 2:
        return "dictionary_context_dual_source"
    if source_count == 1:
        return "dictionary_context_single_source"
    return "dictionary_context_gap"


def human_join_row(row: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_source = {entry["source_id"]: entry for entry in entries}
    kangxi = by_source.get("nlp_han_dicts_kangxi_4w", {})
    zhdzd = by_source.get("nlp_han_dicts_zhonghua_dazidian", {})
    kangxi_preview = " ".join((kangxi.get("content_preview", "") or "").split())
    zhdzd_preview = " ".join((zhdzd.get("content_preview", "") or "").split())
    return {
        "sample_id": row["sample_id"],
        "char": row["char"],
        "unicode": row["unicode"],
        "review_prior": row["review_prior"],
        "review_queue": row["review_queue"],
        "source_gap_failure_codes": row["source_gap_failure_codes"],
        "dictionary_context_class": context_class(entries),
        "dictionary_source_count": len({entry["source_id"] for entry in entries}),
        "dictionary_source_ids": ";".join(entry["source_id"] for entry in entries),
        "kangxi_preview": kangxi_preview,
        "zhonghua_dazidian_preview": zhdzd_preview,
        "source_grade": "cross_reference_dictionary_context" if entries else "dictionary_context_gap",
        "human_review_status": row["human_review_status"],
        "human_structure_label": row["human_structure_label"],
        "human_decomposition": row["human_decomposition"],
        "human_evidence_source": row["human_evidence_source"],
        "human_review_notes": row["human_review_notes"],
    }


def coverage_for_rows(rows: list[dict[str, Any]], context: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    classes = Counter(context_class(context.get(row["char"], [])) for row in rows)
    hit_rows = sum(count for klass, count in classes.items() if klass != "dictionary_context_gap")
    return {
        "row_count": len(rows),
        "hit_rows": hit_rows,
        "gap_rows": classes.get("dictionary_context_gap", 0),
        "hit_rate": round(hit_rows / len(rows), 6) if rows else 0,
        "class_counts": dict(sorted(classes.items())),
    }


def build_review_join() -> dict[str, Any]:
    human = load_json(HUMAN_REVIEW_PACKET)
    feature = load_json(FEATURE_TABLE)
    human_rows = human["rows"]
    feature_rows = feature["row_records"]
    context = load_context_by_char()
    joined_human = [human_join_row(row, context.get(row["char"], [])) for row in human_rows]
    remaining_samples = [
        {
            "char": row["char"],
            "unicode": row["unicode"],
            "review_prior": row["review_prior"],
            "review_queue": row["review_queue"],
            "dictionary_context_class": context_class(context.get(row["char"], [])),
            "dictionary_source_ids": ";".join(entry["source_id"] for entry in context.get(row["char"], [])),
        }
        for row in feature_rows
        if context.get(row["char"])
    ][:REMAINING_SAMPLE_LIMIT]

    checks = {
        "staging_db_exists": STAGING_DB.exists(),
        "human_review_rows_match_expected": len(human_rows) == HUMAN_ROWS_EXPECTED,
        "remaining_feature_rows_match_expected": len(feature_rows) == REMAINING_ROWS_EXPECTED,
        "human_join_rows_match_expected": len(joined_human) == HUMAN_ROWS_EXPECTED,
        "dictionary_context_loaded": len(context) > 49_000,
        "knowledge_write_blocked": True,
        "formal_scoring_blocked": True,
        "final_structure_labels_blocked": True,
    }
    status = "PASS_DICTIONARY_CONTEXT_REVIEW_JOIN_READY" if all(checks.values()) else "BLOCKED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_external_dictionary_context_review_join",
        "overall_status": status,
        "next_workflow_status": "DICTIONARY_CONTEXT_REVIEW_PACKET_READY_KNOWLEDGE_IMPORT_BLOCKED",
        "authority_boundary": {
            "dictionary_sources_are_cross_reference_context": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_research_knowledge": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_cnbe_database": True,
        },
        "summary": {
            "staging_db": str(STAGING_DB),
            "dictionary_context_unique_chars": len(context),
            "human_review_coverage": coverage_for_rows(human_rows, context),
            "remaining_agent_standard_coverage": coverage_for_rows(feature_rows, context),
            "human_dual_source_rows": sum(
                1 for row in joined_human if row["dictionary_context_class"] == "dictionary_context_dual_source"
            ),
            "human_single_source_rows": sum(
                1 for row in joined_human if row["dictionary_context_class"] == "dictionary_context_single_source"
            ),
            "human_gap_rows": sum(
                1 for row in joined_human if row["dictionary_context_class"] == "dictionary_context_gap"
            ),
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "knowledge_write_allowed": False,
            "formal_gf0017_scoring_allowed": False,
        },
        "checks": checks,
        "human_review_join_rows": joined_human,
        "remaining_hit_samples": remaining_samples,
        "decision": {
            "may_export_dictionary_context_review_packet": status.startswith("PASS"),
            "may_modify_cnbe_research_knowledge": False,
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "recommended_next_step": "Export reviewer-facing XLSX/CSV with dictionary context columns, then merge human review results in a later audited gate.",
        },
    }


def write_csv(path: Path, report: dict[str, Any]) -> None:
    rows = report["human_review_join_rows"]
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(report: dict[str, Any]) -> str:
    human = report["summary"]["human_review_coverage"]
    remaining = report["summary"]["remaining_agent_standard_coverage"]
    lines = [
        "# External Dictionary Context Review Join",
        "",
        "## Purpose",
        "",
        "This report joins staged Kangxi and Zhonghua Dazidian dictionary context",
        "to the current human-review packet and remaining Agent-standard rows.",
        "",
        "It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit",
        "final structure labels, write CNBE rows, or rebuild CNBE databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Dictionary context unique chars: `{report['summary']['dictionary_context_unique_chars']}`",
        f"- Human review hit rows: `{human['hit_rows']}` / `{human['row_count']}`",
        f"- Human review hit rate: `{human['hit_rate']}`",
        f"- Remaining hit rows: `{remaining['hit_rows']}` / `{remaining['row_count']}`",
        f"- Remaining hit rate: `{remaining['hit_rate']}`",
        f"- Human dual-source rows: `{report['summary']['human_dual_source_rows']}`",
        f"- Human single-source rows: `{report['summary']['human_single_source_rows']}`",
        f"- Human gap rows: `{report['summary']['human_gap_rows']}`",
        "",
        "## Checks",
        "",
    ]
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["recommended_next_step"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_review_join()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, report)


if __name__ == "__main__":
    main()
