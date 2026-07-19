#!/usr/bin/env python3
"""Plan deterministic review samples for Agent-standard structure candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

FEATURE_TABLE = Path("reports/remaining_structure_agent_standard_feature_table.json")
REVIEW_PRIOR_AUDIT = Path("reports/remaining_structure_agent_standard_review_prior_audit.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_review_samples.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_REVIEW_SAMPLES.md")

EXPECTED_ROWS = 73_831
EXPECTED_TOTAL_SAMPLES = 150
SAMPLE_QUOTAS = {
    "review_prior_medium": 50,
    "review_prior_low_medium": 50,
    "review_prior_low": 50,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def deterministic_indices(count: int, quota: int) -> list[int]:
    """Return stable, spread-out zero-based indices without randomness."""
    if quota <= 0:
        return []
    if count < quota:
        raise ValueError(f"cannot sample {quota} rows from bucket of {count}")
    if quota == 1:
        return [0]
    return sorted({round(i * (count - 1) / (quota - 1)) for i in range(quota)})


def sample_record(row: dict[str, Any], sample_id: str) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "offset": row["offset"],
        "worksheet_row": row["worksheet_row"],
        "char": row["char"],
        "unicode": row["unicode"],
        "unicode_block": row["unicode_block"],
        "review_queue": row["review_queue"],
        "review_prior": row["review_prior"],
        "standard_level": row["standard_level"],
        "score_status": row["score_status"],
        "feature_flags": row["feature_flags"],
        "source_gap_failure_codes": row["source_gap_failure_codes"],
        "allowed_next_action": row["allowed_next_action"],
    }


def build_review_sample_plan() -> dict[str, Any]:
    feature_table = load_json(FEATURE_TABLE)
    audit = load_json(REVIEW_PRIOR_AUDIT)
    rows = feature_table["row_records"]
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} feature rows, got {len(rows)}")
    if audit["overall_status"] != "PASS_AGENT_STANDARD_REVIEW_PRIOR_AUDIT_READY":
        raise ValueError("review-prior audit must pass before sample planning")

    samples: list[dict[str, Any]] = []
    bucket_counts = Counter(row["review_prior"] for row in rows)
    for prior, quota in SAMPLE_QUOTAS.items():
        bucket = [row for row in rows if row["review_prior"] == prior]
        for local_index, row_index in enumerate(deterministic_indices(len(bucket), quota), start=1):
            sample_id = f"{prior}:{local_index:03d}"
            samples.append(sample_record(bucket[row_index], sample_id))

    sample_prior_counts = Counter(row["review_prior"] for row in samples)
    sample_queue_counts = Counter(row["review_queue"] for row in samples)
    sample_block_counts = Counter(row["unicode_block"] for row in samples)
    duplicate_keys = [
        key
        for key, count in Counter((row["unicode"], row["offset"]) for row in samples).items()
        if count > 1
    ]
    forbidden_leaks = [
        row["sample_id"]
        for row in samples
        if {"final_structure_label", "gf0017_score", "cnbe32_fields"} & set(row)
    ]
    point_assignment_leaks = [
        row["sample_id"]
        for row in samples
        if row.get("score") is not None or row.get("can_assign_points") is True
    ]

    checks = {
        "feature_table_passed": feature_table["overall_status"] == "PASS_AGENT_STANDARD_FEATURE_TABLE_READY",
        "review_prior_audit_passed": audit["overall_status"] == "PASS_AGENT_STANDARD_REVIEW_PRIOR_AUDIT_READY",
        "feature_rows_match_expected": len(rows) == EXPECTED_ROWS,
        "sample_total_matches_expected": len(samples) == EXPECTED_TOTAL_SAMPLES,
        "sample_prior_counts_match_quota": dict(sample_prior_counts) == SAMPLE_QUOTAS,
        "duplicate_sample_keys_zero": len(duplicate_keys) == 0,
        "forbidden_field_leaks_zero": len(forbidden_leaks) == 0,
        "point_assignment_leaks_zero": len(point_assignment_leaks) == 0,
    }
    status = (
        "PASS_AGENT_STANDARD_REVIEW_SAMPLE_PLAN_READY"
        if all(checks.values())
        else "BLOCKED"
    )

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_agent_standard_review_sample_plan",
        "overall_status": status,
        "next_workflow_status": "HUMAN_REVIEW_SAMPLE_PACKET_READY_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
        },
        "sampling_method": {
            "method": "deterministic_even_spread_by_review_prior",
            "total_samples": EXPECTED_TOTAL_SAMPLES,
            "quotas": SAMPLE_QUOTAS,
            "random_seed": None,
            "reason": (
                "Use evenly spaced offsets inside each audited review-prior bucket so the sample "
                "can be reproduced without random state and without changing source data."
            ),
        },
        "summary": {
            "feature_rows": len(rows),
            "sample_rows": len(samples),
            "source_bucket_counts": dict(sorted(bucket_counts.items())),
            "sample_prior_counts": dict(sorted(sample_prior_counts.items())),
            "sample_queue_counts": dict(sorted(sample_queue_counts.items())),
            "sample_unicode_block_counts": dict(sorted(sample_block_counts.items())),
            "duplicate_sample_key_count": len(duplicate_keys),
            "forbidden_field_leak_count": len(forbidden_leaks),
            "point_assignment_leak_count": len(point_assignment_leaks),
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_gf0017_scoring_allowed": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
            "source_asset_write_allowed": False,
        },
        "checks": checks,
        "samples": samples,
        "decision": {
            "may_start_human_review_packet": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Deterministic review samples are ready for human or expert review packet "
                "construction. Formal scoring and encoding writes remain blocked."
            ),
        },
        "next_artifacts": [
            "reports/remaining_structure_agent_standard_human_review_packet.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_HUMAN_REVIEW_PACKET.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Review Samples",
        "",
        "## Purpose",
        "",
        "This report defines deterministic review samples for remaining",
        "Agent-standard structure candidates.",
        "",
        "It does not assign GF0017 scores, emit final structure labels, write",
        "CNBE rows, rebuild databases, modify source assets, or claim national",
        "standard status for outside-8105 rows.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Feature rows: `{report['summary']['feature_rows']}`",
        f"- Sample rows: `{report['summary']['sample_rows']}`",
        f"- Duplicate sample keys: `{report['summary']['duplicate_sample_key_count']}`",
        f"- Forbidden field leaks: `{report['summary']['forbidden_field_leak_count']}`",
        f"- Point assignment leaks: `{report['summary']['point_assignment_leak_count']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Final structure labels emitted: `{report['summary']['final_structure_labels_emitted']}`",
        "",
        "## Sample Prior Counts",
        "",
    ]
    for prior, count in report["summary"]["sample_prior_counts"].items():
        lines.append(f"- `{prior}`: {count}")
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_review_sample_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
