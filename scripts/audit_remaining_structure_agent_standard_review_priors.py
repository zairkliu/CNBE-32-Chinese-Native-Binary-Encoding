#!/usr/bin/env python3
"""Audit Agent-standard review priors without scoring or final labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_review_prior_audit.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_REVIEW_PRIOR_AUDIT.md")

EXPECTED_ROWS = 73_831
EXPECTED_QUEUE_COUNTS = {
    "agent_standard_rule_learning_candidate": 5_885,
    "agent_standard_extension_review_candidate": 67_946,
}
EXPECTED_PRIOR_COUNTS = {
    "review_prior_medium": 1_080,
    "review_prior_low_medium": 4_805,
    "review_prior_low": 67_946,
}
FORBIDDEN_FIELDS = {
    "final_structure_label",
    "gf0017_score",
    "cnbe32_fields",
}
SAMPLE_LIMIT = 120


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def expected_prior(row: dict[str, Any]) -> str:
    if row["review_queue"] == "agent_standard_extension_review_candidate":
        return "review_prior_low"
    if row["unicode_block"] == "CJK Unified Ideographs":
        return "review_prior_medium"
    return "review_prior_low_medium"


def sample_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "offset": row["offset"],
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "unicode_block": row["unicode_block"],
            "review_queue": row["review_queue"],
            "review_prior": row["review_prior"],
        }
        for row in rows[:SAMPLE_LIMIT]
    ]


def build_review_prior_audit() -> dict[str, Any]:
    feature_table = load_json(FEATURE_TABLE)
    rows = feature_table["row_records"]
    queue_counts = Counter(row["review_queue"] for row in rows)
    prior_counts = Counter(row["review_prior"] for row in rows)
    prior_by_block: dict[str, Counter[str]] = defaultdict(Counter)
    prior_mismatches: list[dict[str, Any]] = []
    forbidden_field_rows: list[dict[str, Any]] = []
    point_assignment_rows: list[dict[str, Any]] = []

    for row in rows:
        prior_by_block[row["unicode_block"]][row["review_prior"]] += 1
        expected = expected_prior(row)
        if row["review_prior"] != expected:
            prior_mismatches.append(
                {
                    "char": row["char"],
                    "unicode": row["unicode"],
                    "unicode_block": row["unicode_block"],
                    "review_queue": row["review_queue"],
                    "review_prior": row["review_prior"],
                    "expected_review_prior": expected,
                }
            )
        leaked = sorted(FORBIDDEN_FIELDS & set(row))
        if leaked:
            forbidden_field_rows.append(
                {
                    "char": row["char"],
                    "unicode": row["unicode"],
                    "forbidden_fields": leaked,
                }
            )
        if row.get("can_assign_points") is not False or row.get("score") is not None:
            point_assignment_rows.append(
                {
                    "char": row["char"],
                    "unicode": row["unicode"],
                    "can_assign_points": row.get("can_assign_points"),
                    "score": row.get("score"),
                }
            )

    checks = {
        "row_count_matches_expected": len(rows) == EXPECTED_ROWS,
        "queue_counts_match_expected": dict(queue_counts) == EXPECTED_QUEUE_COUNTS,
        "prior_counts_match_expected": dict(prior_counts) == EXPECTED_PRIOR_COUNTS,
        "prior_mismatches_zero": len(prior_mismatches) == 0,
        "forbidden_field_rows_zero": len(forbidden_field_rows) == 0,
        "point_assignment_rows_zero": len(point_assignment_rows) == 0,
        "feature_table_passed": feature_table["overall_status"] == "PASS_AGENT_STANDARD_FEATURE_TABLE_READY",
    }
    status = (
        "PASS_AGENT_STANDARD_REVIEW_PRIOR_AUDIT_READY"
        if all(checks.values())
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_agent_standard_review_prior_audit",
        "overall_status": status,
        "next_workflow_status": "AGENT_STANDARD_REVIEW_SAMPLE_PLAN_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "feature_rows": len(rows),
            "review_queue_counts": dict(sorted(queue_counts.items())),
            "review_prior_counts": dict(sorted(prior_counts.items())),
            "prior_by_unicode_block": {
                block: dict(sorted(counter.items()))
                for block, counter in sorted(prior_by_block.items())
            },
            "prior_mismatch_count": len(prior_mismatches),
            "forbidden_field_row_count": len(forbidden_field_rows),
            "point_assignment_row_count": len(point_assignment_rows),
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "checks": checks,
        "samples": {
            "review_prior_medium": sample_rows([row for row in rows if row["review_prior"] == "review_prior_medium"]),
            "review_prior_low_medium": sample_rows([row for row in rows if row["review_prior"] == "review_prior_low_medium"]),
            "review_prior_low": sample_rows([row for row in rows if row["review_prior"] == "review_prior_low"]),
            "prior_mismatches": prior_mismatches[:SAMPLE_LIMIT],
            "forbidden_field_rows": forbidden_field_rows[:SAMPLE_LIMIT],
            "point_assignment_rows": point_assignment_rows[:SAMPLE_LIMIT],
        },
        "decision": {
            "may_start_review_sample_plan": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Review-prior audit passed. The next step may design deterministic review samples, "
                "but final structures, GF0017 points, and CNBE rows remain blocked."
            ),
        },
        "next_artifacts": [
            "scripts/plan_remaining_structure_agent_standard_review_samples.py",
            "reports/remaining_structure_agent_standard_review_samples.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_REVIEW_SAMPLES.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Review-Prior Audit",
        "",
        "## Purpose",
        "",
        "This report audits review queues and review-prior buckets for remaining",
        "Agent-standard structure candidates.",
        "",
        "It does not assign GF0017 scores, emit final structure labels, modify",
        "source assets, write CNBE rows, rebuild databases, create tags, publish",
        "releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Feature rows: `{report['summary']['feature_rows']}`",
        f"- Prior mismatches: `{report['summary']['prior_mismatch_count']}`",
        f"- Forbidden field rows: `{report['summary']['forbidden_field_row_count']}`",
        f"- Point assignment rows: `{report['summary']['point_assignment_row_count']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Final structure labels emitted: `{report['summary']['final_structure_labels_emitted']}`",
        "",
        "## Checks",
        "",
    ]
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_review_prior_audit()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
