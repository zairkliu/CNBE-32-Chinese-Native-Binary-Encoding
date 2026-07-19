#!/usr/bin/env python3
"""Create a read-only diff packet for structured 8105 knowledge blockers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
BASELINE = Path("evidence/8105/cnbe8105_standard_baseline.json")
BASE_CHARACTER_DATA = RESEARCH_ROOT / "knowledge/structured/base_character_data.json"
ENRICHED_KNOWLEDGE = RESEARCH_ROOT / "knowledge/structured/cnbe_character_knowledge.json"
BLOCKER_RECONCILIATION = Path("reports/full_catalog_gf0017_blocker_reconciliation.json")

DEFAULT_JSON_OUTPUT = Path("reports/structured_8105_knowledge_diff_packet.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/STRUCTURED_8105_KNOWLEDGE_DIFF_PACKET.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def expected_unicode(char: str) -> str:
    return f"U+{ord(char):04X}"


def keyed_enriched(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        char = row.get("char")
        if isinstance(char, str) and len(char) == 1:
            if char in keyed:
                duplicates.append(char)
            keyed[char] = row
    if duplicates:
        keyed["__duplicates__"] = {"chars": duplicates}
    return keyed


def unicode_label_issues(rows: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for char, row in rows.items():
        if len(char) != 1:
            continue
        observed = row.get("unicode")
        expected = expected_unicode(char)
        if observed != expected:
            issues.append(
                {
                    "char": char,
                    "observed": str(observed),
                    "expected": expected,
                    "repair": "normalize_unicode_label_only",
                }
            )
    return issues


def build_dataset_diff(
    *,
    dataset_id: str,
    source_path: Path,
    rows_by_char: dict[str, dict[str, Any]],
    baseline_chars: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    baseline_set = set(baseline_chars)
    row_set = {char for char in rows_by_char if len(char) == 1}
    missing = sorted(baseline_set - row_set, key=ord)
    extra = sorted(row_set - baseline_set, key=ord)
    unicode_issues = unicode_label_issues(rows_by_char)
    return {
        "dataset_id": dataset_id,
        "source_path": str(source_path),
        "source_exists": source_path.is_file(),
        "baseline_count": len(baseline_set),
        "dataset_count": len(row_set),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "unicode_label_issue_count": len(unicode_issues),
        "missing_chars": [
            {
                "char": char,
                "unicode": expected_unicode(char),
                "baseline_rank": baseline_chars[char].get("standard_rank"),
                "level": baseline_chars[char].get("level"),
                "stroke_count": baseline_chars[char].get("stroke_count"),
            }
            for char in missing
        ],
        "extra_chars": [{"char": char, "unicode": expected_unicode(char)} for char in extra],
        "unicode_label_issue_samples": unicode_issues[:50],
        "repair_plan": {
            "safe_automatic_candidate": (
                len(extra) == 0
                and len(missing) <= 1
                and len(unicode_issues) > 0
            ),
            "requires_review_before_write": True,
            "steps": [
                "review missing character against 8105 baseline",
                "normalize Unicode labels to U+XXXX or wider without unnecessary leading zero",
                "regenerate enriched knowledge only after base_character_data is reconciled",
                "rerun source audit and knowledge inventory",
            ],
        },
    }


def build_diff_packet() -> dict[str, Any]:
    baseline = load_json(BASELINE)
    base_rows = load_json(BASE_CHARACTER_DATA)
    enriched_rows = load_json(ENRICHED_KNOWLEDGE)
    blocker_report = load_json(BLOCKER_RECONCILIATION)

    baseline_chars = baseline["characters"]
    enriched_by_char = keyed_enriched(enriched_rows)
    base_diff = build_dataset_diff(
        dataset_id="base_character_data",
        source_path=BASE_CHARACTER_DATA,
        rows_by_char=base_rows,
        baseline_chars=baseline_chars,
    )
    enriched_diff = build_dataset_diff(
        dataset_id="cnbe_character_knowledge",
        source_path=ENRICHED_KNOWLEDGE,
        rows_by_char=enriched_by_char,
        baseline_chars=baseline_chars,
    )
    datasets = [base_diff, enriched_diff]
    total_missing = sum(item["missing_count"] for item in datasets)
    total_extra = sum(item["extra_count"] for item in datasets)
    total_unicode_issues = sum(item["unicode_label_issue_count"] for item in datasets)
    diff_clean = total_missing == 0 and total_extra == 0 and total_unicode_issues == 0

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_structured_8105_knowledge_diff_packet",
        "overall_status": "PASS",
        "next_workflow_status": "STRUCTURED_KNOWLEDGE_DIFF_CLEAN"
        if diff_clean
        else "PATCH_REVIEW_REQUIRED_BEFORE_SOURCE_WRITE",
        "authority_boundary": {
            "does_not_modify_research_assets": True,
            "does_not_score_rows": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
        },
        "inputs": {
            "baseline": str(BASELINE),
            "base_character_data": str(BASE_CHARACTER_DATA),
            "cnbe_character_knowledge": str(ENRICHED_KNOWLEDGE),
            "blocker_reconciliation": str(BLOCKER_RECONCILIATION),
        },
        "summary": {
            "baseline_count": len(baseline_chars),
            "datasets_checked": len(datasets),
            "total_missing": total_missing,
            "total_extra": total_extra,
            "total_unicode_label_issues": total_unicode_issues,
            "blockers_from_previous_gate": blocker_report["summary"]["blockers"],
            "batch_scoring_allowed": False,
            "source_write_allowed": False,
        },
        "datasets": datasets,
        "decision_point": {
            "requires_human_authorization": not diff_clean,
            "safe_patch_scope_if_authorized": [
                "add missing 8105 rows to base_character_data.json",
                "review or exclude extra rows that are outside the repository 8105 baseline",
                "add or regenerate corresponding enriched knowledge rows",
                "normalize Unicode labels in both structured files",
            ],
            "still_forbidden_without_authorization": [
                "write to cnbe-research/knowledge/structured",
                "start full-catalog GF0017 row scoring",
                "rebuild CNBE SQLite database",
            ],
        },
        "next_artifacts_after_authorization": [
            "reports/structured_8105_knowledge_patch_plan.json",
            "reports/STRUCTURED_8105_KNOWLEDGE_PATCH_PLAN.md",
            "scripts/patch_structured_8105_knowledge.py",
        ],
    }


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Structured 8105 Knowledge Diff Packet",
        "",
        "## Purpose",
        "",
        "This packet compares the repository 8105 baseline with structured",
        "`cnbe-research` knowledge files that currently block full-catalog GF0017",
        "batch scoring.",
        "",
        "It is read-only. It does not modify `cnbe-research`, score workbook rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{packet['overall_status']}`",
        f"- Next workflow status: `{packet['next_workflow_status']}`",
        f"- Baseline count: `{packet['summary']['baseline_count']}`",
        f"- Datasets checked: `{packet['summary']['datasets_checked']}`",
        f"- Total missing rows: `{packet['summary']['total_missing']}`",
        f"- Total extra rows: `{packet['summary']['total_extra']}`",
        f"- Total Unicode label issues: `{packet['summary']['total_unicode_label_issues']}`",
        f"- Source write allowed: `{packet['summary']['source_write_allowed']}`",
        f"- Batch scoring allowed: `{packet['summary']['batch_scoring_allowed']}`",
        f"- Human authorization required: `{packet['decision_point']['requires_human_authorization']}`",
        "",
        "## Dataset Diffs",
        "",
        "| Dataset | Count | Missing | Extra | Unicode label issues |",
        "|---|---:|---:|---:|---:|",
    ]
    for dataset in packet["datasets"]:
        lines.append(
            f"| `{dataset['dataset_id']}` | {dataset['dataset_count']} | "
            f"{dataset['missing_count']} | {dataset['extra_count']} | "
            f"{dataset['unicode_label_issue_count']} |"
        )

    lines.extend(["", "## Missing Characters", ""])
    for dataset in packet["datasets"]:
        lines.append(f"### {dataset['dataset_id']}")
        if dataset["missing_chars"]:
            for row in dataset["missing_chars"]:
                lines.append(
                    f"- `{row['char']}` `{row['unicode']}` rank `{row['baseline_rank']}` "
                    f"level `{row['level']}` strokes `{row['stroke_count']}`"
                )
        else:
            lines.append("- None.")
        lines.append("")

    lines.extend(["## Extra Characters", ""])
    for dataset in packet["datasets"]:
        lines.append(f"### {dataset['dataset_id']}")
        if dataset["extra_chars"]:
            for row in dataset["extra_chars"]:
                lines.append(f"- `{row['char']}` `{row['unicode']}`")
        else:
            lines.append("- None.")
        lines.append("")

    lines.extend(
        [
            "## Decision Point",
            "",
            "Human authorization is required before writing to structured knowledge files."
            if packet["decision_point"]["requires_human_authorization"]
            else "No structured knowledge write is currently required.",
            "",
            "Safe patch scope if authorized:",
            "",
        ]
    )
    for item in packet["decision_point"]["safe_patch_scope_if_authorized"]:
        lines.append(f"- {item}")

    lines.extend(["", "Still forbidden without authorization:", ""])
    for item in packet["decision_point"]["still_forbidden_without_authorization"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Next Artifacts After Authorization", ""])
    for artifact in packet["next_artifacts_after_authorization"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    packet = build_diff_packet()
    write_json(DEFAULT_JSON_OUTPUT, packet)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(packet))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={packet['overall_status']}")
    print(f"next_workflow_status={packet['next_workflow_status']}")
    if packet["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
