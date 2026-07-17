#!/usr/bin/env python3
"""Confirm the CNBE 8105 encoding core before publishing the branch.

This confirmation is intentionally lightweight. It reads already tracked 8105
evidence artifacts and emits a small JSON/Markdown summary that fixes the
current project boundary: 8105 is the national-standard core, current CNBE rows
are still a repair/review target, and full scoring/encoding writes remain
blocked until the missing evidence gates are completed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASELINE = Path("evidence/8105/cnbe8105_standard_baseline.json")
COMPARISON = Path("evidence/8105/cnbe8105_encoding_comparison.json")
GF0017_SCORES = Path("evidence/gf0017/cnbe8105_gf0017_normativity_scores.json")
AGENT_PREENCODING = Path("evidence/agent-standard/cnbe20902_agent_preencoding_test.json")

DEFAULT_JSON_OUTPUT = Path("reports/cnbe8105_core_confirmation.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/CNBE8105_CORE_CONFIRMATION.md")

EXPECTED_8105_ROWS = 8105


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_confirmation() -> dict[str, Any]:
    baseline = load_json(BASELINE)
    comparison = load_json(COMPARISON)
    gf0017 = load_json(GF0017_SCORES)
    agent = load_json(AGENT_PREENCODING)

    baseline_summary = baseline["summary"]
    comparison_summary = comparison["summary"]
    gf0017_summary = gf0017["summary"]
    agent_summary = agent["summary"]

    checks = {
        "baseline_row_count_is_8105": baseline_summary["row_count"] == EXPECTED_8105_ROWS,
        "baseline_row_count_matches_expected": baseline_summary["row_count_matches_expected"] is True,
        "comparison_standard_rows_are_8105": comparison_summary["total_standard_rows"] == EXPECTED_8105_ROWS,
        "gf0017_score_rows_are_8105": gf0017_summary["row_count"] == EXPECTED_8105_ROWS,
        "agent_preencoding_is_read_only": agent["metadata"]["no_write"] is True,
        "agent_preencoding_has_no_first_blocker": agent_summary["first_blocker_char"] is None,
        "current_cnbe_not_claimed_complete": comparison_summary["missing_from_current_rows"] > 0
        or comparison_summary["status_counts"].get("EVIDENCE_GAP", 0) > 0,
        "full_gf0017_not_claimed_complete": gf0017_summary["overall_status_counts"].get("EVIDENCE_GAP", 0) > 0
        or gf0017_summary["overall_status_counts"].get("PARTIAL", 0) > 0,
    }
    overall_status = "PASS_CNBE8105_CORE_CONFIRMATION_READY_TO_PUSH" if all(checks.values()) else "BLOCKED"

    return {
        "report_schema_version": "1.0",
        "mode": "cnbe8105_core_confirmation",
        "overall_status": overall_status,
        "scope": {
            "core": "8105 通用规范汉字表",
            "core_status": "national_standard_core",
            "outside_8105_status": "agent_standard_candidate_not_national_standard",
        },
        "tracked_inputs": {
            "baseline": str(BASELINE),
            "comparison": str(COMPARISON),
            "gf0017_scores": str(GF0017_SCORES),
            "agent_preencoding": str(AGENT_PREENCODING),
        },
        "summary": {
            "baseline_rows": baseline_summary["row_count"],
            "baseline_complete_rows": baseline_summary["evidence_status_counts"].get("COMPLETE", 0),
            "baseline_review_required_rows": baseline_summary["evidence_status_counts"].get("REVIEW_REQUIRED", 0),
            "current_cnbe_rows_in_scope": comparison_summary["current_rows_in_scope"],
            "missing_from_current_cnbe": comparison_summary["missing_from_current_rows"],
            "comparison_status_counts": comparison_summary["status_counts"],
            "gf0017_average_score": gf0017_summary["average_score"],
            "gf0017_min_score": gf0017_summary["min_score"],
            "gf0017_max_score": gf0017_summary["max_score"],
            "gf0017_overall_status_counts": gf0017_summary["overall_status_counts"],
            "gf0017_source_gap_items": gf0017["metadata"]["source_gap_item_ids"],
            "agent_preencoding_rows": agent_summary["row_count"],
            "agent_preencoding_status_counts": agent_summary["agent_status_counts"],
        },
        "confirmation": {
            "unicode_first_core_confirmed": True,
            "8105_is_controlling_core": True,
            "current_cnbe_requires_repair_or_review": True,
            "gf0017_full_scoring_not_complete": True,
            "cnbe32_write_allowed": False,
            "database_rebuild_allowed": False,
            "release_or_pypi_allowed": False,
            "push_scope_is_lightweight_core_confirmation": True,
        },
        "checks": checks,
        "next_workflow_status": "READY_FOR_REMOTE_REVIEW_OF_8105_CORE_CONFIRMATION",
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# CNBE 8105 Core Confirmation",
        "",
        f"Overall status: `{report['overall_status']}`",
        f"Next workflow status: `{report['next_workflow_status']}`",
        "",
        "## Scope",
        "",
        "- Core: 8105 通用规范汉字表",
        "- Core status: national-standard core",
        "- Outside-8105 status: Agent-standard candidate, not national-standard output",
        "",
        "## Confirmed Counts",
        "",
        f"- Baseline rows: {summary['baseline_rows']}",
        f"- Baseline complete rows: {summary['baseline_complete_rows']}",
        f"- Baseline review-required rows: {summary['baseline_review_required_rows']}",
        f"- Current CNBE rows in 8105 scope: {summary['current_cnbe_rows_in_scope']}",
        f"- Missing from current CNBE: {summary['missing_from_current_cnbe']}",
        f"- GF0017 average score: {summary['gf0017_average_score']}",
        f"- GF0017 min/max score: {summary['gf0017_min_score']} / {summary['gf0017_max_score']}",
        f"- Agent preencoding rows: {summary['agent_preencoding_rows']}",
        "",
        "## Boundary",
        "",
        "- CNBE32 writes are not allowed by this confirmation.",
        "- SQLite database rebuild is not allowed.",
        "- Release and PyPI actions are not allowed.",
        "- Missing evidence is not treated as a pass.",
        "- Full GF0017 scoring remains incomplete until source gaps are resolved.",
        "",
        "## Checks",
        "",
    ]
    for name, passed in report["checks"].items():
        lines.append(f"- {name}: `{passed}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_confirmation()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])


if __name__ == "__main__":
    main()
