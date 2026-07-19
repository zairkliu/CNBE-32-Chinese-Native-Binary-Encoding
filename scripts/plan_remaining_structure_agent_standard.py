#!/usr/bin/env python3
"""Plan Agent-standard handling for remaining structure gaps."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_ACQUISITION = Path("reports/remaining_structure_source_acquisition_plan.json")
WIKI_INDEX = Path("reports/wikipedia_structure_cross_reference_index.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_PLAN.md")

EXPECTED_REMAINING_ROWS = 73_831
SAMPLE_LIMIT = 120


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


def sample(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "unicode_block": record["unicode_block"],
        }
        for record in records[:SAMPLE_LIMIT]
    ]


def build_agent_standard_plan() -> dict[str, Any]:
    acquisition = load_json(SOURCE_ACQUISITION)
    records = remaining_records()
    block_counts = Counter(record["unicode_block"] for record in records)
    direct_agent_candidates = [
        record
        for record in records
        if record["unicode_block"] in {
            "CJK Unified Ideographs",
            "CJK Unified Ideographs Extension A",
        }
    ]
    extension_review_candidates = [
        record
        for record in records
        if record["unicode_block"] not in {
            "CJK Unified Ideographs",
            "CJK Unified Ideographs Extension A",
        }
    ]

    queue_counts = {
        "agent_standard_rule_learning_candidate": len(direct_agent_candidates),
        "agent_standard_extension_review_candidate": len(extension_review_candidates),
    }
    stronger = acquisition["summary"]["stronger_authoritative_source_available"]
    status = (
        "PASS_REMAINING_STRUCTURE_AGENT_STANDARD_PLAN_READY"
        if acquisition["overall_status"] == "PASS_REMAINING_STRUCTURE_SOURCE_ACQUISITION_PLAN_READY"
        and not stronger
        and len(records) == EXPECTED_REMAINING_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_remaining_structure_agent_standard_plan",
        "overall_status": status,
        "next_workflow_status": "AGENT_STANDARD_RULE_LEARNING_DESIGN_ALLOWED_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "remaining_rows": len(records),
            "remaining_unicode_block_counts": dict(sorted(block_counts.items())),
            "queue_counts": queue_counts,
            "standard_level": "agent_standard_candidate_not_national_standard",
            "stronger_authoritative_source_available": stronger,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "agent_standard_policy": {
            "allowed": status.startswith("PASS"),
            "standard_level": "agent_standard_candidate_not_national_standard",
            "input_basis": [
                "Unicode identity",
                "8105-aligned structure label set",
                "GF/GG/GB rule sources",
                "available cross-reference evidence",
                "explicit unresolved source-gap status",
            ],
            "forbidden_claims": [
                "national_standard",
                "formal_gf0017_score",
                "release_ready_encoding",
                "cnbe_row_repair",
            ],
            "required_next_stage": "design_agent_standard_rule_learning_without_point_assignment",
        },
        "queues": [
            {
                "queue": "agent_standard_rule_learning_candidate",
                "row_count": len(direct_agent_candidates),
                "scope": "BMP base and Extension A rows with no stronger local source",
                "action": "design 8105-aligned rule-learning candidates for review only",
                "can_assign_points": False,
            },
            {
                "queue": "agent_standard_extension_review_candidate",
                "row_count": len(extension_review_candidates),
                "scope": "Extension B and later rows with no stronger local source",
                "action": "retain as Agent-standard extension review candidates until stronger IDS/source is acquired",
                "can_assign_points": False,
            },
        ],
        "samples": {
            "agent_standard_rule_learning_candidate": sample(direct_agent_candidates),
            "agent_standard_extension_review_candidate": sample(extension_review_candidates),
        },
        "decision": {
            "may_design_agent_standard_rule_learning": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "No stronger authoritative row-level IDS source is available locally. "
                "The remaining rows may proceed only as Agent-standard candidates, with no national-standard claim or point assignment."
            ),
        },
        "next_artifacts": [
            "scripts/design_remaining_structure_agent_standard_rule_learning.py",
            "reports/remaining_structure_agent_standard_rule_learning_design.json",
            "reports/REMAINING_STRUCTURE_AGENT_STANDARD_RULE_LEARNING_DESIGN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Plan",
        "",
        "## Purpose",
        "",
        "This report routes remaining structure/decomposition source gaps into an",
        "Agent-standard workflow because no stronger local authoritative row-level",
        "IDS source was found.",
        "",
        "It does not assign GF0017 scores, modify source assets, write CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Remaining rows: `{report['summary']['remaining_rows']}`",
        f"- Standard level: `{report['summary']['standard_level']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        "",
        "## Queues",
        "",
    ]
    for queue in report["queues"]:
        lines.append(f"- `{queue['queue']}`: {queue['row_count']} rows; {queue['action']}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_agent_standard_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
