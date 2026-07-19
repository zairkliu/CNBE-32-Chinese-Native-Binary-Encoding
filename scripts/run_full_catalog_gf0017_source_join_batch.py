#!/usr/bin/env python3
"""Run a full-catalog GF0017 source-join batch assessment without scores."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

RESEARCH_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research")
UNICODE_IDENTITY = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
BASELINE_8105 = Path("evidence/8105/cnbe8105_standard_baseline.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")
BATCH_READINESS = Path("reports/full_catalog_gf0017_batch_readiness.json")
BASE_CHARACTER_DATA = RESEARCH_ROOT / "knowledge/structured/base_character_data.json"
ENRICHED_KNOWLEDGE = RESEARCH_ROOT / "knowledge/structured/cnbe_character_knowledge.json"

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_source_join_batch.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_SOURCE_JOIN_BATCH.md")
SAMPLE_LIMIT = 20


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def keyed_enriched(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        row["char"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("char"), str) and len(row["char"]) == 1
    }


def source_item_statuses(source_mapping: dict[str, Any]) -> dict[str, str]:
    return {item["id"]: item["source_status"] for item in source_mapping["items"]}


def classify_join(
    row: dict[str, Any],
    *,
    baseline_chars: set[str],
    base_chars: set[str],
    enriched_chars: set[str],
) -> tuple[str, list[str]]:
    issues: list[str] = []
    if row.get("issues"):
        return "BLOCKER_UNICODE_IDENTITY", list(row["issues"])
    char = row["char"]
    if char in baseline_chars:
        if char not in base_chars:
            issues.append("missing_base_character_data")
        if char not in enriched_chars:
            issues.append("missing_enriched_knowledge")
        if issues:
            return "BLOCKER_8105_SOURCE_JOIN", issues
        return "JOINED_8105_STANDARD_DERIVED_KNOWLEDGE", []
    return "OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED", ["outside_8105_direct_baseline"]


def build_source_join_batch() -> dict[str, Any]:
    identity = load_json(UNICODE_IDENTITY)
    baseline = load_json(BASELINE_8105)
    source_mapping = load_json(SOURCE_MAPPING)
    readiness = load_json(BATCH_READINESS)
    base_rows = load_json(BASE_CHARACTER_DATA)
    enriched_rows = load_json(ENRICHED_KNOWLEDGE)

    baseline_chars = set(baseline["characters"])
    base_chars = set(base_rows)
    enriched_chars = set(keyed_enriched(enriched_rows))
    item_statuses = source_item_statuses(source_mapping)

    status_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    rows_out: list[dict[str, Any]] = []
    samples: dict[str, list[dict[str, Any]]] = {
        "joined_8105": [],
        "agent_standard_required": [],
        "blockers": [],
    }
    for offset, row in enumerate(identity["row_identities"]):
        status, issues = classify_join(
            row,
            baseline_chars=baseline_chars,
            base_chars=base_chars,
            enriched_chars=enriched_chars,
        )
        status_counts[status] += 1
        for issue in issues:
            issue_counts[issue] += 1
        record = {
            "offset": offset,
            "worksheet_row": row["worksheet_row"],
            "char": row["char"],
            "unicode": row["unicode"],
            "join_status": status,
            "standard_level": "national_standard_8105_baseline" if row["char"] in baseline_chars else "agent_standard_required_not_national_standard",
            "gf0017_source_item_statuses": item_statuses,
            "score": None,
            "score_status": "NOT_SCORED_SOURCE_JOIN_ONLY",
            "issues": issues,
        }
        rows_out.append(record)
        sample = {
            "offset": record["offset"],
            "worksheet_row": record["worksheet_row"],
            "char": record["char"],
            "unicode": record["unicode"],
            "join_status": record["join_status"],
            "issues": record["issues"],
        }
        if status == "JOINED_8105_STANDARD_DERIVED_KNOWLEDGE" and len(samples["joined_8105"]) < SAMPLE_LIMIT:
            samples["joined_8105"].append(sample)
        elif status == "OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED" and len(samples["agent_standard_required"]) < SAMPLE_LIMIT:
            samples["agent_standard_required"].append(sample)
        elif status.startswith("BLOCKER") and len(samples["blockers"]) < SAMPLE_LIMIT:
            samples["blockers"].append(sample)

    blocker_count = sum(count for status, count in status_counts.items() if status.startswith("BLOCKER"))
    source_join_ok = blocker_count == 0 and readiness["summary"]["source_join_batch_allowed"] is True
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_source_join_batch",
        "overall_status": "PASS_SOURCE_JOIN_BATCH_ASSESSED" if source_join_ok else "BLOCKED",
        "next_workflow_status": "FORMAL_SCORING_BLOCKED_SOURCE_EVIDENCE_JOIN_REQUIRED",
        "authority_boundary": {
            "does_not_assign_gf0017_scores": True,
            "does_not_modify_workbook": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
        },
        "summary": {
            "total_rows": len(rows_out),
            "status_counts": dict(status_counts),
            "issue_counts": dict(issue_counts),
            "blocker_count": blocker_count,
            "gf0017_source_item_statuses": item_statuses,
            "score_values_assigned": 0,
            "formal_gf0017_scoring_allowed": False,
            "database_rebuild_allowed": False,
        },
        "samples": samples,
        "row_records": rows_out,
        "decision": {
            "may_start_formal_gf0017_scoring": False,
            "may_start_agent_standard_mapping_design": source_join_ok,
            "may_rebuild_database": False,
            "reason": (
                "Source-join batch assessment completed. Formal scoring remains blocked because "
                "SOURCE_GAP and SOURCE_EVIDENCE_REQUIRED item statuses must be resolved into per-row evidence."
            ),
        },
        "next_artifacts": [
            "reports/full_catalog_agent_standard_mapping_plan.json",
            "reports/FULL_CATALOG_AGENT_STANDARD_MAPPING_PLAN.md",
            "scripts/plan_full_catalog_agent_standard_mapping.py",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Source-Join Batch",
        "",
        "## Purpose",
        "",
        "This report runs a full 97,686-row source-join assessment for the v4_fixed",
        "catalog. It separates rows with direct 8105 structured evidence from rows",
        "that require Agent-standard mapping.",
        "",
        "It does not assign GF0017 scores, modify the workbook, change CNBE rows,",
        "rebuild databases, create tags, publish releases, or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total rows: `{report['summary']['total_rows']}`",
        f"- Blocker count: `{report['summary']['blocker_count']}`",
        f"- Score values assigned: `{report['summary']['score_values_assigned']}`",
        f"- Formal GF0017 scoring allowed: `{report['summary']['formal_gf0017_scoring_allowed']}`",
        "",
        "## Join Status Counts",
        "",
    ]
    for key, value in sorted(report["summary"]["status_counts"].items()):
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## GF0017 Source Item Statuses", ""])
    for key, value in report["summary"]["gf0017_source_item_statuses"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            report["decision"]["reason"],
            "",
            "The next allowed step is Agent-standard mapping design for rows outside",
            "the direct 8105 baseline. Formal scoring and database reconstruction",
            "remain blocked.",
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
    report = build_source_join_batch()
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
