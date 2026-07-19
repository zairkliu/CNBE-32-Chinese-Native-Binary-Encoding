#!/usr/bin/env python3
"""Run read-only feature-table materialization for Agent-standard candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

RULE_LEARNING_DESIGN = Path("reports/remaining_structure_agent_standard_rule_learning_design.json")
WIKI_INDEX = Path("reports/wikipedia_structure_cross_reference_index.json")
SOURCE_ACQUISITION = Path("reports/remaining_structure_source_acquisition_plan.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_feature_table.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_FEATURE_TABLE.md")

EXPECTED_REMAINING_ROWS = 73_831
EXPECTED_RULE_LEARNING_ROWS = 5_885
EXPECTED_EXTENSION_REVIEW_ROWS = 67_946
SAMPLE_LIMIT = 120

RULE_LEARNING_BLOCKS = {
    "CJK Unified Ideographs",
    "CJK Unified Ideographs Extension A",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def remaining_records() -> list[dict[str, Any]]:
    wiki = load_json(WIKI_INDEX)
    return [
        record
        for record in wiki["row_records"]
        if record["wiki_review_status"] == "NO_WIKI_CROSS_REFERENCE_HIT"
    ]


def block_family(unicode_block: str) -> str:
    if unicode_block == "CJK Unified Ideographs":
        return "base_cjk"
    if unicode_block == "CJK Unified Ideographs Extension A":
        return "extension_a"
    return "extension_b_or_later"


def review_queue(unicode_block: str) -> str:
    if unicode_block in RULE_LEARNING_BLOCKS:
        return "agent_standard_rule_learning_candidate"
    return "agent_standard_extension_review_candidate"


def confidence_bucket(queue: str, unicode_block: str) -> str:
    if queue == "agent_standard_rule_learning_candidate" and unicode_block == "CJK Unified Ideographs":
        return "review_prior_medium"
    if queue == "agent_standard_rule_learning_candidate":
        return "review_prior_low_medium"
    return "review_prior_low"


def build_feature_record(record: dict[str, Any]) -> dict[str, Any]:
    queue = review_queue(record["unicode_block"])
    return {
        "offset": record["offset"],
        "worksheet_row": record["worksheet_row"],
        "char": record["char"],
        "unicode": record["unicode"],
        "unicode_block": record["unicode_block"],
        "block_family": block_family(record["unicode_block"]),
        "standard_level": "agent_standard_candidate_not_national_standard",
        "review_queue": queue,
        "review_prior": confidence_bucket(queue, record["unicode_block"]),
        "feature_flags": {
            "unicode_identity_available": True,
            "allowed_structure_label_set_available": True,
            "has_wiki_cross_reference": False,
            "has_dictionary_review_hit": False,
            "has_stronger_authoritative_row_level_ids": False,
            "has_unresolved_structure_gap": True,
        },
        "source_gap_failure_codes": record["source_gap_failure_codes"],
        "allowed_next_action": "human_review_or_agent_rule_learning_design_only",
        "forbidden_outputs": [
            "final_structure_label",
            "formal_gf0017_score",
            "cnbe32_fields",
            "national_standard_claim",
        ],
        "score": None,
        "score_status": "NOT_SCORED_AGENT_STANDARD_FEATURE_ONLY",
        "can_assign_points": False,
    }


def sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return records[:SAMPLE_LIMIT]


def build_feature_table() -> dict[str, Any]:
    design = load_json(RULE_LEARNING_DESIGN)
    acquisition = load_json(SOURCE_ACQUISITION)
    feature_records = [build_feature_record(record) for record in remaining_records()]
    queue_counts = Counter(record["review_queue"] for record in feature_records)
    prior_counts = Counter(record["review_prior"] for record in feature_records)
    block_counts = Counter(record["unicode_block"] for record in feature_records)

    status = (
        "PASS_AGENT_STANDARD_FEATURE_TABLE_READY"
        if design["overall_status"] == "PASS_AGENT_STANDARD_RULE_LEARNING_DESIGN_READY"
        and acquisition["summary"]["stronger_authoritative_source_available"] is False
        and len(feature_records) == EXPECTED_REMAINING_ROWS
        and queue_counts["agent_standard_rule_learning_candidate"] == EXPECTED_RULE_LEARNING_ROWS
        and queue_counts["agent_standard_extension_review_candidate"] == EXPECTED_EXTENSION_REVIEW_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_agent_standard_feature_table",
        "overall_status": status,
        "next_workflow_status": "AGENT_STANDARD_REVIEW_PRIOR_AUDIT_ALLOWED_FORMAL_SCORING_BLOCKED",
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
            "feature_rows": len(feature_records),
            "review_queue_counts": dict(sorted(queue_counts.items())),
            "review_prior_counts": dict(sorted(prior_counts.items())),
            "unicode_block_counts": dict(sorted(block_counts.items())),
            "standard_level": "agent_standard_candidate_not_national_standard",
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "feature_schema": {
            "identity_fields": ["char", "unicode", "offset", "worksheet_row"],
            "review_fields": ["review_queue", "review_prior", "feature_flags", "source_gap_failure_codes"],
            "forbidden_fields": ["final_structure_label", "gf0017_score", "cnbe32_fields"],
        },
        "samples": {
            "agent_standard_rule_learning_candidate": sample(
                [
                    record
                    for record in feature_records
                    if record["review_queue"] == "agent_standard_rule_learning_candidate"
                ]
            ),
            "agent_standard_extension_review_candidate": sample(
                [
                    record
                    for record in feature_records
                    if record["review_queue"] == "agent_standard_extension_review_candidate"
                ]
            ),
        },
        "row_records": feature_records,
        "decision": {
            "may_start_review_prior_audit": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Read-only Agent-standard feature rows are materialized. The next step may audit review priors, "
                "but final structures, GF0017 points, and CNBE rows remain blocked."
            ),
        },
        "next_artifacts": [
            "scripts/audit_remaining_structure_agent_standard_review_priors.py",
            "reports/remaining_structure_agent_standard_review_prior_audit.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_REVIEW_PRIOR_AUDIT.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Feature Table",
        "",
        "## Purpose",
        "",
        "This report materializes read-only feature rows for remaining",
        "Agent-standard structure candidates. It emits review queues and review",
        "priors only.",
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
        f"- Standard level: `{report['summary']['standard_level']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Final structure labels emitted: `{report['summary']['final_structure_labels_emitted']}`",
        "",
        "## Review Queue Counts",
        "",
    ]
    for queue, count in report["summary"]["review_queue_counts"].items():
        lines.append(f"- `{queue}`: {count}")
    lines.extend(["", "## Review Prior Counts", ""])
    for prior, count in report["summary"]["review_prior_counts"].items():
        lines.append(f"- `{prior}`: {count}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_feature_table()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
