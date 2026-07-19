#!/usr/bin/env python3
"""Audit the read-only unified Hanzi evidence index."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

INDEX_REPORT = Path("reports/unified_hanzi_evidence_index.json")
DEFAULT_JSON_OUTPUT = Path("reports/unified_hanzi_evidence_index_audit.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/UNIFIED_HANZI_EVIDENCE_INDEX_AUDIT.md")

EXPECTED_ROWS = 97_686
EXPECTED_8105_ROWS = 8_105
EXPECTED_OUTSIDE_ROWS = 89_581
REQUIRED_SAMPLE_UNICODES = {"U+4E00", "U+5BB6", "U+946B", "U+3400", "U+3401", "U+323AF"}
FORBIDDEN_ENTRY_FIELDS = {
    "gf0017_score",
    "final_structure_label",
    "cnbe32_repair_value",
    "database_write_record",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def schema_index(schema: list[str]) -> dict[str, int]:
    return {field: index for index, field in enumerate(schema)}


def audit_index() -> dict[str, Any]:
    report = load_json(INDEX_REPORT)
    schema = report["index_schema"]
    positions = schema_index(schema)
    rows = report["index"]
    profiles = report["profiles"]

    scope_counts: Counter[str] = Counter()
    review_status_counts: Counter[str] = Counter()
    profile_reference_issues: list[dict[str, Any]] = []
    malformed_rows: list[dict[str, Any]] = []
    forbidden_sample_field_issues: list[dict[str, Any]] = []

    required_profile_fields = {
        "source_join_profile_id": "source_join_item_statuses",
        "agent_evidence_profile_id": "agent_evidence_item_statuses",
        "evidence_gap_profile_id": "evidence_gaps",
        "feature_flags_profile_id": "feature_flags",
    }

    for unicode_label, row in rows.items():
        if not isinstance(row, list) or len(row) != len(schema):
            malformed_rows.append({"unicode": unicode_label, "row_length": len(row) if isinstance(row, list) else None})
            continue
        scope_counts[row[positions["catalog_scope"]]] += 1
        review_status_counts[row[positions["review_status"]]] += 1
        for field, profile_group in required_profile_fields.items():
            profile_id = row[positions[field]]
            if profile_id not in profiles[profile_group]:
                profile_reference_issues.append(
                    {
                        "unicode": unicode_label,
                        "field": field,
                        "profile_group": profile_group,
                        "profile_id": profile_id,
                    }
                )
                if len(profile_reference_issues) >= 20:
                    break

    for unicode_label, sample in report["samples"].items():
        forbidden = sorted(FORBIDDEN_ENTRY_FIELDS & set(sample))
        if forbidden:
            forbidden_sample_field_issues.append({"unicode": unicode_label, "forbidden_fields": forbidden})

    checks = {
        "index_status_pass": report["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_BUILT",
        "row_count_match": len(rows) == EXPECTED_ROWS,
        "sample_set_complete": REQUIRED_SAMPLE_UNICODES <= set(report["samples"]),
        "schema_has_required_profile_refs": set(required_profile_fields) <= set(schema),
        "scope_counts_match": (
            scope_counts["8105_core"] == EXPECTED_8105_ROWS
            and scope_counts["outside_8105_agent_candidate"] == EXPECTED_OUTSIDE_ROWS
        ),
        "summary_blocks_scoring": report["summary"]["formal_gf0017_scoring_allowed"] is False,
        "summary_blocks_cnbe_writes": report["summary"]["cnbe_row_write_allowed"] is False,
        "summary_blocks_database_rebuild": report["summary"]["database_rebuild_allowed"] is False,
        "score_values_assigned_zero": report["summary"]["score_values_assigned"] == 0,
        "final_structure_labels_emitted_zero": report["summary"]["final_structure_labels_emitted"] == 0,
        "malformed_rows_zero": not malformed_rows,
        "profile_reference_issues_zero": not profile_reference_issues,
        "forbidden_sample_field_issues_zero": not forbidden_sample_field_issues,
    }
    status = "PASS_UNIFIED_EVIDENCE_INDEX_AUDITED" if all(checks.values()) else "BLOCKED_UNIFIED_EVIDENCE_INDEX_AUDIT"

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_unified_hanzi_evidence_index_audit",
        "overall_status": status,
        "next_workflow_status": "HUMAN_REVIEW_OR_FORMAL_SCORING_AUTHORIZATION_REQUIRED",
        "summary": {
            "total_entries": len(rows),
            "catalog_scope_counts": dict(scope_counts),
            "review_status_counts": dict(review_status_counts),
            "profile_counts": report["summary"]["profile_counts"],
            "malformed_row_sample_count": len(malformed_rows),
            "profile_reference_issue_sample_count": len(profile_reference_issues),
            "forbidden_sample_field_issue_count": len(forbidden_sample_field_issues),
            "formal_gf0017_scoring_allowed": False,
            "cnbe_row_write_allowed": False,
            "database_rebuild_allowed": False,
        },
        "checks": checks,
        "issue_samples": {
            "malformed_rows": malformed_rows[:20],
            "profile_reference_issues": profile_reference_issues[:20],
            "forbidden_sample_field_issues": forbidden_sample_field_issues[:20],
        },
        "decision": {
            "may_start_human_review": status.startswith("PASS"),
            "may_start_formal_gf0017_scoring": False,
            "may_write_cnbe_rows": False,
            "may_rebuild_database": False,
            "reason": (
                "The unified evidence index is internally consistent and read-only. "
                "Formal scoring, CNBE row writes, and database rebuilds still require "
                "separate human authorization."
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Unified Hanzi Evidence Index Audit",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Total entries: {report['summary']['total_entries']}",
        f"- May start human review: `{report['decision']['may_start_human_review']}`",
        f"- May start formal GF0017 scoring: `{report['decision']['may_start_formal_gf0017_scoring']}`",
        f"- May write CNBE rows: `{report['decision']['may_write_cnbe_rows']}`",
        f"- May rebuild database: `{report['decision']['may_rebuild_database']}`",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---:|",
    ]
    for check, passed in sorted(report["checks"].items()):
        lines.append(f"| `{check}` | `{passed}` |")
    lines.extend(["", "## Scope Counts", "", "| Scope | Count |", "|---|---:|"])
    for scope, count in sorted(report["summary"]["catalog_scope_counts"].items()):
        lines.append(f"| `{scope}` | {count} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    report = audit_index()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(report["overall_status"])
    print(f"entries={report['summary']['total_entries']}")
    print(f"next={report['next_workflow_status']}")


if __name__ == "__main__":
    main()
