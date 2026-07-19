#!/usr/bin/env python3
"""Build a human-review packet for Agent-standard structure samples."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

REVIEW_SAMPLES = Path("reports/remaining_structure_agent_standard_review_samples.json")

DEFAULT_JSON_OUTPUT = Path("reports/remaining_structure_agent_standard_human_review_packet.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/REMAINING_STRUCTURE_AGENT_STANDARD_HUMAN_REVIEW_PACKET.md")
DEFAULT_CSV_OUTPUT = Path("reports/remaining_structure_agent_standard_human_review_packet.csv")

EXPECTED_SAMPLE_ROWS = 150
ALLOWED_STRUCTURE_LABELS = [
    "独体字",
    "上下",
    "上中下",
    "左右",
    "左中右",
    "左上包",
    "右上包",
    "左三包",
    "左下包",
    "上三包",
    "下三包",
    "全包围",
    "镶嵌",
]
REVIEW_STATUS_VALUES = [
    "未审核",
    "同意进入后续证据补强",
    "需要查标准/字典",
    "样本暂缓",
    "排除本轮",
]

REVIEW_COLUMNS = [
    "sample_id",
    "char",
    "unicode",
    "codepoint_dec",
    "worksheet_row",
    "source_offset",
    "unicode_block",
    "review_prior",
    "review_queue",
    "standard_level",
    "score_status",
    "source_gap_failure_codes",
    "unicode_identity_available",
    "has_unresolved_structure_gap",
    "has_wiki_cross_reference",
    "has_dictionary_review_hit",
    "has_stronger_authoritative_row_level_ids",
    "allowed_next_action",
    "human_review_status",
    "human_structure_label",
    "human_decomposition",
    "human_radical_or_component_note",
    "human_evidence_source",
    "human_reviewer",
    "human_review_notes",
    "adjudication_result",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def codepoint_dec(unicode_label: str) -> int:
    if not unicode_label.startswith("U+"):
        raise ValueError(f"invalid Unicode label: {unicode_label}")
    return int(unicode_label[2:], 16)


def packet_row(sample: dict[str, Any]) -> dict[str, Any]:
    flags = sample["feature_flags"]
    return {
        "sample_id": sample["sample_id"],
        "char": sample["char"],
        "unicode": sample["unicode"],
        "codepoint_dec": codepoint_dec(sample["unicode"]),
        "worksheet_row": sample["worksheet_row"],
        "source_offset": sample["offset"],
        "unicode_block": sample["unicode_block"],
        "review_prior": sample["review_prior"],
        "review_queue": sample["review_queue"],
        "standard_level": sample["standard_level"],
        "score_status": sample["score_status"],
        "source_gap_failure_codes": ";".join(sample["source_gap_failure_codes"]),
        "unicode_identity_available": flags["unicode_identity_available"],
        "has_unresolved_structure_gap": flags["has_unresolved_structure_gap"],
        "has_wiki_cross_reference": flags["has_wiki_cross_reference"],
        "has_dictionary_review_hit": flags["has_dictionary_review_hit"],
        "has_stronger_authoritative_row_level_ids": flags["has_stronger_authoritative_row_level_ids"],
        "allowed_next_action": sample["allowed_next_action"],
        "human_review_status": "未审核",
        "human_structure_label": "",
        "human_decomposition": "",
        "human_radical_or_component_note": "",
        "human_evidence_source": "",
        "human_reviewer": "",
        "human_review_notes": "",
        "adjudication_result": "",
    }


def build_human_review_packet() -> dict[str, Any]:
    sample_plan = load_json(REVIEW_SAMPLES)
    samples = sample_plan["samples"]
    rows = [packet_row(sample) for sample in samples]
    prior_counts = Counter(row["review_prior"] for row in rows)
    queue_counts = Counter(row["review_queue"] for row in rows)
    block_counts = Counter(row["unicode_block"] for row in rows)
    duplicate_keys = [
        key
        for key, count in Counter((row["unicode"], row["source_offset"]) for row in rows).items()
        if count > 1
    ]
    forbidden_field_rows = [
        row["sample_id"]
        for row in rows
        if {"final_structure_label", "gf0017_score", "cnbe32_fields"} & set(row)
    ]
    non_blank_human_labels = [
        row["sample_id"]
        for row in rows
        if row["human_structure_label"] or row["human_decomposition"]
    ]

    checks = {
        "review_sample_plan_passed": sample_plan["overall_status"] == "PASS_AGENT_STANDARD_REVIEW_SAMPLE_PLAN_READY",
        "row_count_matches_expected": len(rows) == EXPECTED_SAMPLE_ROWS,
        "duplicate_keys_zero": len(duplicate_keys) == 0,
        "forbidden_field_rows_zero": len(forbidden_field_rows) == 0,
        "human_labels_blank_before_review": len(non_blank_human_labels) == 0,
        "formal_scores_assigned_zero": True,
        "final_structure_labels_emitted_zero": True,
    }
    status = "PASS_HUMAN_REVIEW_PACKET_READY" if all(checks.values()) else "BLOCKED"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_agent_standard_human_review_packet",
        "overall_status": status,
        "next_workflow_status": "HUMAN_REVIEW_XLSX_READY_FORMAL_SCORING_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_modify_source_assets": True,
            "does_not_claim_national_standard_for_outside_8105": True,
        },
        "review_instructions": {
            "review_status_values": REVIEW_STATUS_VALUES,
            "allowed_structure_labels": ALLOWED_STRUCTURE_LABELS,
            "required_first_step": "Confirm literal character and Unicode identity before any structure note.",
            "scoring_boundary": "Reviewer notes are evidence inputs only; they are not formal GF0017 scores.",
        },
        "summary": {
            "packet_rows": len(rows),
            "review_prior_counts": dict(sorted(prior_counts.items())),
            "review_queue_counts": dict(sorted(queue_counts.items())),
            "unicode_block_counts": dict(sorted(block_counts.items())),
            "duplicate_key_count": len(duplicate_keys),
            "forbidden_field_row_count": len(forbidden_field_rows),
            "human_label_prefill_count": len(non_blank_human_labels),
            "score_values_assigned": 0,
            "final_structure_labels_emitted": 0,
            "formal_gf0017_scoring_allowed": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
            "source_asset_write_allowed": False,
        },
        "checks": checks,
        "columns": REVIEW_COLUMNS,
        "rows": rows,
        "decision": {
            "may_start_human_review": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_emit_final_structure_labels": False,
            "may_modify_source_assets": False,
            "may_rebuild_database": False,
            "may_modify_cnbe_rows": False,
            "reason": (
                "Human-review packet is ready as an evidence collection surface. "
                "Formal scoring and encoding writes remain blocked until review results "
                "are merged, audited, and explicitly authorized."
            ),
        },
    }


def write_csv(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["rows"])


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Remaining Structure Agent-Standard Human Review Packet",
        "",
        "## Purpose",
        "",
        "This packet prepares deterministic Agent-standard samples for human",
        "review in a coding-directory workbook.",
        "",
        "It does not assign GF0017 scores, emit final structure labels, write",
        "CNBE rows, rebuild databases, modify source assets, or claim national",
        "standard status for outside-8105 rows.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Packet rows: `{report['summary']['packet_rows']}`",
        f"- Duplicate keys: `{report['summary']['duplicate_key_count']}`",
        f"- Forbidden field rows: `{report['summary']['forbidden_field_row_count']}`",
        f"- Human label prefill count: `{report['summary']['human_label_prefill_count']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Final structure labels emitted: `{report['summary']['final_structure_labels_emitted']}`",
        "",
        "## Review Prior Counts",
        "",
    ]
    for prior, count in report["summary"]["review_prior_counts"].items():
        lines.append(f"- `{prior}`: {count}")
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Decision", "", report["decision"]["reason"], ""])
    return "\n".join(lines)


def main() -> None:
    report = build_human_review_packet()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    write_csv(DEFAULT_CSV_OUTPUT, report)


if __name__ == "__main__":
    main()
