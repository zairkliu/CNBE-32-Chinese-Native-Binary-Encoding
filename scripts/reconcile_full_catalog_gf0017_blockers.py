#!/usr/bin/env python3
"""Reconcile full-catalog GF0017 blockers without changing source assets.

This script turns known source/knowledge blockers into an explicit action
matrix. It is a decision-support gate, not a repair operation and not a row
scoring operation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

JOIN_SCHEMA = Path("reports/full_catalog_gf0017_join_schema.json")
SOURCE_MAPPING = Path("reports/full_catalog_gf0017_source_mapping.json")
KNOWLEDGE_INVENTORY = Path("reports/cnbe_research_knowledge_inventory.json")
SOURCE_AUDIT = Path("reports/cnbe_research_source_audit.json")

DEFAULT_JSON_OUTPUT = Path("reports/full_catalog_gf0017_blocker_reconciliation.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/FULL_CATALOG_GF0017_BLOCKER_RECONCILIATION.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def classify_blocker(item: dict[str, Any]) -> dict[str, Any]:
    asset = item["asset"]
    if asset == "Unihan.zip":
        return {
            **item,
            "blocker_code": "CORRUPT_EXTERNAL_ARCHIVE",
            "classification": "EXCLUDE_OR_REPLACE_EXTERNAL_ARCHIVE",
            "automation_level": "requires_human_or_network_asset_decision",
            "recommended_action": "Use the already verified Unihan2.zip or exclude Unihan.zip from authoritative inputs after human approval.",
            "allowed_now": "document decision options only",
            "forbidden_now": "delete, replace, or download archive without authorization",
            "batch_scoring_impact": "blocks external archive authority but does not block 8105 Unicode identity gates already passed",
        }
    if asset == "structured/base_character_data.json":
        return {
            **item,
            "blocker_code": "8105_COUNT_AND_UNICODE_LABEL_MISMATCH",
            "classification": "REPAIR_PLAN_REQUIRED",
            "automation_level": "plan_only_until_source_diff_is_reviewed",
            "recommended_action": "Generate a read-only diff against the 8105 baseline to identify the missing character and Unicode label normalization scope.",
            "allowed_now": "design diff script and review packet",
            "forbidden_now": "rewrite structured knowledge JSON without reviewed patch",
            "batch_scoring_impact": "blocks treating this structured file as standard-derived evidence",
        }
    if asset == "structured/cnbe_character_knowledge.json":
        return {
            **item,
            "blocker_code": "ENRICHED_KNOWLEDGE_COUNT_AND_UNICODE_LABEL_MISMATCH",
            "classification": "REPAIR_PLAN_REQUIRED",
            "automation_level": "plan_only_until_source_diff_is_reviewed",
            "recommended_action": "Generate a read-only diff against the 8105 baseline and base_character_data repair plan before touching enriched rows.",
            "allowed_now": "design dependency-aware repair packet",
            "forbidden_now": "rewrite enriched knowledge before base table reconciliation",
            "batch_scoring_impact": "blocks using enriched dictionary/wiki rows as joined standard knowledge",
        }
    return {
        **item,
        "blocker_code": "UNKNOWN_BLOCKER",
        "classification": "HUMAN_REVIEW_REQUIRED",
        "automation_level": "manual_triage",
        "recommended_action": "Classify blocker before any repair work.",
        "allowed_now": "document only",
        "forbidden_now": "automatic repair",
        "batch_scoring_impact": "blocks affected evidence source",
    }


def build_reconciliation() -> dict[str, Any]:
    join_schema = load_json(JOIN_SCHEMA)
    source_mapping = load_json(SOURCE_MAPPING)
    knowledge_inventory = load_json(KNOWLEDGE_INVENTORY)
    source_audit = load_json(SOURCE_AUDIT)

    blockers = [
        classify_blocker(item)
        for item in knowledge_inventory.get("action_items", [])
        if item.get("severity") == "BLOCKER"
    ]
    classifications: dict[str, int] = {}
    automation_levels: dict[str, int] = {}
    for blocker in blockers:
        classifications[blocker["classification"]] = classifications.get(blocker["classification"], 0) + 1
        automation_levels[blocker["automation_level"]] = automation_levels.get(blocker["automation_level"], 0) + 1

    has_structured_repair_blocker = any(blocker["classification"] == "REPAIR_PLAN_REQUIRED" for blocker in blockers)
    decision_point = {
        "requires_human_decision": bool(blockers),
        "decision_needed": (
            "Choose whether to exclude or replace the corrupt Unihan.zip before treating that archive as authoritative."
            if not has_structured_repair_blocker
            else "Choose whether to exclude/replace the corrupt Unihan.zip and whether to authorize "
            "structured 8105 knowledge repair."
        ),
        "safe_next_step_without_data_write": "continue batch readiness and source-join assessment"
        if not has_structured_repair_blocker
        else "create read-only structured-knowledge diff packet",
        "requires_authorization_before_write": [
            "delete or replace Unihan.zip",
            "start batch GF0017 scoring",
            "rebuild database",
        ],
    }
    if has_structured_repair_blocker:
        decision_point["requires_authorization_before_write"][1:1] = [
            "modify structured/base_character_data.json",
            "modify structured/cnbe_character_knowledge.json",
        ]

    return {
        "report_schema_version": "1.0",
        "mode": "read_only_full_catalog_gf0017_blocker_reconciliation",
        "overall_status": "PASS",
        "next_workflow_status": "DECISION_POINT_REACHED_READ_ONLY_DIFF_ALLOWED",
        "authority_boundary": {
            "does_not_modify_knowledge_assets": True,
            "does_not_score_rows": True,
            "does_not_rebuild_database": True,
            "does_not_publish_release": True,
            "preserves_source_gap": True,
        },
        "inputs": {
            "join_schema": str(JOIN_SCHEMA),
            "source_mapping": str(SOURCE_MAPPING),
            "knowledge_inventory": str(KNOWLEDGE_INVENTORY),
            "source_audit": str(SOURCE_AUDIT),
        },
        "summary": {
            "blockers": len(blockers),
            "classification_counts": classifications,
            "automation_level_counts": automation_levels,
            "join_schema_status": join_schema["overall_status"],
            "source_mapping_status": source_mapping["overall_status"],
            "source_audit_status": source_audit["summary"]["status"],
            "batch_scoring_allowed": False,
            "database_rebuild_allowed": False,
        },
        "blockers": blockers,
        "decision_point": decision_point,
        "next_artifacts": [
            "reports/structured_8105_knowledge_diff_packet.json",
            "reports/STRUCTURED_8105_KNOWLEDGE_DIFF_PACKET.md",
            "scripts/diff_structured_8105_knowledge.py",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Full Catalog GF0017 Blocker Reconciliation",
        "",
        "## Purpose",
        "",
        "This report classifies the remaining knowledge/source blockers before any",
        "full-catalog GF0017 row scoring or database reconstruction begins.",
        "",
        "It is read-only. It does not modify `cnbe-research`, change CNBE rows,",
        "score workbook rows, rebuild databases, create tags, publish releases,",
        "or upload to PyPI.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Blockers: `{report['summary']['blockers']}`",
        f"- Batch scoring allowed: `{report['summary']['batch_scoring_allowed']}`",
        f"- Database rebuild allowed: `{report['summary']['database_rebuild_allowed']}`",
        f"- Human decision required: `{report['decision_point']['requires_human_decision']}`",
        "",
        "## Classification Counts",
        "",
    ]
    for key, count in sorted(report["summary"]["classification_counts"].items()):
        lines.append(f"- `{key}`: {count}")

    lines.extend(
        [
            "",
            "## Blockers",
            "",
            "| Asset | Classification | Automation | Recommended action |",
            "|---|---|---|---|",
        ]
    )
    for blocker in report["blockers"]:
        lines.append(
            f"| `{blocker['asset']}` | {blocker['classification']} | "
            f"{blocker['automation_level']} | {blocker['recommended_action']} |"
        )

    lines.extend(
        [
            "",
            "## Decision Point",
            "",
            report["decision_point"]["decision_needed"],
            "",
            "Requires authorization before write:",
            "",
        ]
    )
    for item in report["decision_point"]["requires_authorization_before_write"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "Safe next step without data write:",
            "",
            f"- {report['decision_point']['safe_next_step_without_data_write']}",
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
    report = build_reconciliation()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    print(f"next_workflow_status={report['next_workflow_status']}")
    if report["overall_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
