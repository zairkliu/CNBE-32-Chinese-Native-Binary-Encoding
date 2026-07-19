#!/usr/bin/env python3
"""Plan Phase 1 review for structure/decomposition parser output."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

PARSER_OUTPUT = Path("reports/structure_decomposition_evidence_parser.json")

DEFAULT_JSON_OUTPUT = Path("reports/structure_decomposition_evidence_review.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURE_DECOMPOSITION_EVIDENCE_REVIEW.md")

EXPECTED_OUTSIDE_8105_ROWS = 89_581
SAMPLE_LIMIT = 120

QUEUE_RULES = {
    "STRUCTURE_DECOMPOSITION_EVIDENCE_READY_FOR_REVIEW": {
        "queue": "human_review_ready",
        "priority": 1,
        "action": "review source anchors, confirm 13-label structure, keep as evidence candidate only",
    },
    "STRUCTURE_DECOMPOSITION_PARTIAL_REVIEW_REQUIRED": {
        "queue": "partial_evidence_review",
        "priority": 2,
        "action": "inspect component-only or cross-reference evidence before accepting any structure label",
    },
    "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP": {
        "queue": "source_gap_resolution_required",
        "priority": 3,
        "action": "do not infer structure; route to source-expansion or manual evidence acquisition plan",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sample_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "offset": record["offset"],
        "worksheet_row": record["worksheet_row"],
        "char": record["char"],
        "unicode": record["unicode"],
        "unicode_block": record["unicode_block"],
        "structure_label": record["structure_label"],
        "decomposition": record["decomposition"],
        "components": record["components"],
        "failure_codes": record["failure_codes"],
        "source_hits": record["source_hits"],
    }


def build_review_plan() -> dict[str, Any]:
    parser = load_json(PARSER_OUTPUT)
    records = parser["row_records"]
    queue_counts: Counter[str] = Counter()
    block_counts: Counter[str] = Counter()
    block_by_unicode_block: dict[str, Counter[str]] = {}
    samples: dict[str, list[dict[str, Any]]] = {
        "human_review_ready": [],
        "partial_evidence_review": [],
        "source_gap_resolution_required": [],
        "ambiguous_decomposition": [],
    }

    for record in records:
        rule = QUEUE_RULES[record["evidence_status"]]
        queue = rule["queue"]
        queue_counts[queue] += 1
        block_counter = block_by_unicode_block.setdefault(record["unicode_block"], Counter())
        block_counter[queue] += 1
        for failure in record["failure_codes"]:
            block_counts[failure] += 1
        if len(samples[queue]) < SAMPLE_LIMIT:
            samples[queue].append(sample_record(record))
        if (
            "AMBIGUOUS_DECOMPOSITION" in record["failure_codes"]
            and len(samples["ambiguous_decomposition"]) < SAMPLE_LIMIT
        ):
            samples["ambiguous_decomposition"].append(sample_record(record))

    review_queues = []
    for status, rule in QUEUE_RULES.items():
        review_queues.append(
            {
                "queue": rule["queue"],
                "source_status": status,
                "priority": rule["priority"],
                "row_count": queue_counts[rule["queue"]],
                "action": rule["action"],
                "can_assign_points_after_review": False,
                "requires_human_before_scoring": True,
            }
        )

    overall_status = (
        "PASS_PHASE_1_EVIDENCE_REVIEW_PLAN_READY"
        if parser["overall_status"] == "PASS_PHASE_1_STRUCTURE_DECOMPOSITION_EVIDENCE_PARSED"
        and len(records) == EXPECTED_OUTSIDE_8105_ROWS
        else "BLOCKED"
    )
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_phase_1_structure_decomposition_evidence_review_plan",
        "overall_status": overall_status,
        "next_workflow_status": "SOURCE_GAP_RESOLUTION_AND_HUMAN_REVIEW_REQUIRED_FORMAL_SCORING_BLOCKED",
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
            "outside_8105_rows": len(records),
            "gf0017_item": "structure_first_decomposition",
            "review_queue_counts": dict(sorted(queue_counts.items())),
            "failure_code_counts": dict(sorted(block_counts.items())),
            "unicode_block_queue_counts": {
                block: dict(sorted(counter.items()))
                for block, counter in sorted(block_by_unicode_block.items())
            },
            "dominant_blocker": block_counts.most_common(1)[0][0] if block_counts else None,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
            "cnbe_row_write_allowed": False,
            "source_asset_write_allowed": False,
        },
        "review_queues": sorted(review_queues, key=lambda item: item["priority"]),
        "samples": samples,
        "decision": {
            "may_start_formal_gf0017_scoring": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "may_design_source_gap_resolution_plan": overall_status.startswith("PASS"),
            "reason": (
                "Phase 1 review planning is complete. The parser output exposes a large source gap, so "
                "formal scoring and CNBE row writes remain blocked until source-gap resolution and human review occur."
            ),
        },
        "next_artifacts": [
            "scripts/plan_structure_decomposition_source_gap_resolution.py",
            "reports/structure_decomposition_source_gap_resolution_plan.json",
            "reports/STRUCTURE_DECOMPOSITION_SOURCE_GAP_RESOLUTION_PLAN.md",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Structure/Decomposition Evidence Review Plan",
        "",
        "## Purpose",
        "",
        "This report turns Phase 1 parser output into review queues. It does not",
        "accept evidence, assign GF0017 scores, modify source assets, write CNBE",
        "rows, rebuild databases, create tags, publish releases, or upload to",
        "PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Outside-8105 rows: `{report['summary']['outside_8105_rows']}`",
        f"- GF0017 item: `{report['summary']['gf0017_item']}`",
        f"- Dominant blocker: `{report['summary']['dominant_blocker']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        "",
        "## Review Queues",
        "",
    ]
    for queue in report["review_queues"]:
        lines.append(
            f"- `{queue['queue']}`: {queue['row_count']} rows; action: {queue['action']}"
        )

    lines.extend(["", "## Failure Code Counts", ""])
    for code, count in report["summary"]["failure_code_counts"].items():
        lines.append(f"- `{code}`: {count}")

    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_review_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
