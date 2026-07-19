#!/usr/bin/env python3
"""Evaluate full-catalog GF0017 batch readiness without assigning scores."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

UNICODE_IDENTITY = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
BASELINE_8105 = Path("evidence/8105/cnbe8105_standard_baseline.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")
STRUCTURED_DIFF = Path("reports/structured_8105_knowledge_diff_packet.json")
SOURCE_AUDIT = Path("reports/cnbe_research_source_audit.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_batch_readiness.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_BATCH_READINESS.md")
SAMPLE_LIMIT = 25


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def classify_row(row: dict[str, Any], baseline_chars: set[str]) -> tuple[str, list[str]]:
    issues = row.get("issues") or []
    if issues:
        return "BLOCKER_UNICODE_IDENTITY", list(issues)
    char = row["char"]
    if char in baseline_chars:
        return "READY_8105_DIRECT_BASELINE_ASSESSMENT", []
    return "AGENT_STANDARD_MAPPING_REQUIRED", ["outside_8105_direct_baseline"]


def build_batch_readiness() -> dict[str, Any]:
    identity = load_json(UNICODE_IDENTITY)
    baseline = load_json(BASELINE_8105)
    source_mapping = load_json(SOURCE_MAPPING)
    structured_diff = load_json(STRUCTURED_DIFF)
    source_audit = load_json(SOURCE_AUDIT)
    knowledge_inventory = load_json(KNOWLEDGE_INVENTORY)

    baseline_chars = set(baseline["characters"])
    rows = identity["row_identities"]
    status_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, Any]]] = {
        "ready_8105": [],
        "agent_standard_required": [],
        "blockers": [],
    }
    for offset, row in enumerate(rows):
        status, issues = classify_row(row, baseline_chars)
        status_counts[status] += 1
        for issue in issues:
            issue_counts[issue] += 1
        sample_row = {
            "offset": offset,
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "status": status,
            "issues": issues,
        }
        if status == "READY_8105_DIRECT_BASELINE_ASSESSMENT" and len(samples["ready_8105"]) < SAMPLE_LIMIT:
            samples["ready_8105"].append(sample_row)
        elif status == "AGENT_STANDARD_MAPPING_REQUIRED" and len(samples["agent_standard_required"]) < SAMPLE_LIMIT:
            samples["agent_standard_required"].append(sample_row)
        elif status.startswith("BLOCKER") and len(samples["blockers"]) < SAMPLE_LIMIT:
            samples["blockers"].append(sample_row)

    structured_clean = (
        structured_diff["summary"]["total_missing"] == 0
        and structured_diff["summary"]["total_extra"] == 0
        and structured_diff["summary"]["total_unicode_label_issues"] == 0
    )
    source_files_clean = (
        source_audit["summary"]["sources_pass"] == source_audit["summary"]["sources_total"]
        and source_audit["summary"]["sources_attention"] == 0
        and source_audit["summary"]["sources_fail"] == 0
    )
    remaining_inventory_blocker_is_excluded_archive = (
        knowledge_inventory["gates"]["blocker_count"] == 1
        and any(
            item.get("asset") == "Unihan.zip"
            and "exclude or replace" in item.get("next_step", "")
            for item in knowledge_inventory.get("action_items", [])
            if item.get("severity") == "BLOCKER"
        )
    )
    row_blockers = status_counts.get("BLOCKER_UNICODE_IDENTITY", 0)
    readiness_status = (
        "PASS_READY_FOR_SOURCE_JOIN_BATCH"
        if structured_clean and source_files_clean and row_blockers == 0
        else "BLOCKED"
    )
    source_gap_items = [
        item["id"] for item in source_mapping["items"] if item["source_status"] == "SOURCE_GAP"
    ]
    source_required_items = [
        item["id"] for item in source_mapping["items"] if item["source_status"] == "SOURCE_EVIDENCE_REQUIRED"
    ]

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_batch_readiness",
        "overall_status": readiness_status,
        "next_workflow_status": "SOURCE_JOIN_BATCH_ALLOWED_FORMAL_SCORING_BLOCKED"
        if readiness_status.startswith("PASS")
        else "BATCH_READINESS_BLOCKED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "total_rows": len(rows),
            "unique_unicode_status": identity["summary"]["status"],
            "baseline_8105_rows": len(baseline_chars),
            "status_counts": dict(status_counts),
            "issue_counts": dict(issue_counts),
            "structured_knowledge_clean": structured_clean,
            "source_files_clean": source_files_clean,
            "remaining_inventory_blocker_is_excluded_archive": remaining_inventory_blocker_is_excluded_archive,
            "source_gap_items": source_gap_items,
            "source_evidence_required_items": source_required_items,
            "formal_gf0017_scoring_allowed": False,
            "source_join_batch_allowed": readiness_status.startswith("PASS"),
        },
        "samples": samples,
        "decision": {
            "may_start_source_join_batch": readiness_status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_rebuild_database": False,
            "reason": (
                "Rows are ready for a source-join batch assessment. Formal GF0017 scoring "
                "remains blocked until SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED items are joined "
                "to per-row evidence."
            ),
        },
        "next_artifacts": [
            "reports/full_catalog_gf0017_source_join_batch.json",
            "reports/FULL_CATALOG_GF0017_SOURCE_JOIN_BATCH.md",
            "scripts/run_full_catalog_gf0017_source_join_batch.py",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Batch Readiness",
        "",
        "## Purpose",
        "",
        "This report evaluates whether the 97,686-row v4_fixed catalog can enter",
        "a source-join batch assessment.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total rows: `{report['summary']['total_rows']}`",
        f"- 8105 baseline rows: `{report['summary']['baseline_8105_rows']}`",
        f"- Source join batch allowed: `{report['summary']['source_join_batch_allowed']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        "",
        "## Row Status Counts",
        "",
    ]
    for key, value in sorted(report["summary"]["status_counts"].items()):
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Remaining Source-Gate Classes", ""])
    lines.append("- SOURCE_GAP items: " + ", ".join(f"`{item}`" for item in report["summary"]["source_gap_items"]))
    lines.append(
        "- SOURCE_EVIDENCE_REQUIRED items: "
        + ", ".join(f"`{item}`" for item in report["summary"]["source_evidence_required_items"])
    )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed step is source-join batch assessment. Formal scoring",
            "and database reconstruction remain blocked.",
            "",
            "## Next Artifacts",
            "",
        ]
    )
    for artifact in report["next_artifacts"]:
        lines.append(f"- `{artifact}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_batch_readiness()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"next_workflow_status={report['next_workflow_status']}")
    if not report["overall_status"].startswith("PASS"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
