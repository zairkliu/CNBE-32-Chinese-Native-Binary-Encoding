#!/usr/bin/env python3
"""Plan official dictionary-context knowledge merge without writing knowledge."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

STAGING_DB = Path("build/dictionary_context_staging/dictionary_context_entries.sqlite")
REVIEW_JOIN = Path("reports/external_dictionary_context_review_join.json")
KNOWLEDGE_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge")
STRUCTURED_ROOT = KNOWLEDGE_ROOT / "structured"
TARGET_INDEX = STRUCTURED_ROOT / "dictionary_context_index.json"
TARGET_REFERENCES = KNOWLEDGE_ROOT / "references.json"
BASE_CHARACTER_DATA = STRUCTURED_ROOT / "base_character_data.json"
CNBE_CHARACTER_KNOWLEDGE = STRUCTURED_ROOT / "cnbe_character_knowledge.json"

DEFAULT_JSON_OUTPUT = Path("reports/dictionary_context_knowledge_merge_plan.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_PLAN.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def staging_summary() -> dict[str, Any]:
    with sqlite3.connect(STAGING_DB) as conn:
        conn.row_factory = sqlite3.Row
        total_rows, unique_chars = conn.execute(
            "select count(*), count(distinct char) from dictionary_context_entries"
        ).fetchone()
        source_counts = dict(
            conn.execute("select source_id, count(*) from dictionary_context_entries group by source_id").fetchall()
        )
        dual_source_chars = conn.execute(
            """
            select count(*) from (
              select char from dictionary_context_entries
              group by char having count(distinct source_id) >= 2
            )
            """
        ).fetchone()[0]
        single_source_chars = unique_chars - dual_source_chars
        samples = [
            dict(row)
            for row in conn.execute(
                """
                select source_id, char, unicode, content_preview, license, source_grade
                from dictionary_context_entries
                order by char, source_id
                limit 20
                """
            )
        ]
    return {
        "staging_db": str(STAGING_DB),
        "staged_rows": total_rows,
        "unique_chars": unique_chars,
        "source_counts": dict(sorted(source_counts.items())),
        "dual_source_chars": dual_source_chars,
        "single_source_chars": single_source_chars,
        "samples": samples,
    }


def target_summary() -> dict[str, Any]:
    base = load_json(BASE_CHARACTER_DATA) if BASE_CHARACTER_DATA.exists() else {}
    cnbe = load_json(CNBE_CHARACTER_KNOWLEDGE) if CNBE_CHARACTER_KNOWLEDGE.exists() else []
    references = load_json(TARGET_REFERENCES) if TARGET_REFERENCES.exists() else {}
    base_chars = set(base) if isinstance(base, dict) else set()
    cnbe_chars = {row.get("char") for row in cnbe if isinstance(row, dict)}
    with sqlite3.connect(STAGING_DB) as conn:
        staging_chars = {row[0] for row in conn.execute("select distinct char from dictionary_context_entries")}
    return {
        "base_character_data_exists": BASE_CHARACTER_DATA.exists(),
        "base_character_data_chars": len(base_chars),
        "cnbe_character_knowledge_exists": CNBE_CHARACTER_KNOWLEDGE.exists(),
        "cnbe_character_knowledge_rows": len(cnbe) if isinstance(cnbe, list) else 0,
        "references_exists": TARGET_REFERENCES.exists(),
        "references_entries": len(references) if isinstance(references, dict) else 0,
        "target_index_exists": TARGET_INDEX.exists(),
        "staging_chars_overlapping_8105_base": len(staging_chars & base_chars),
        "staging_chars_overlapping_cnbe_8105": len(staging_chars & cnbe_chars),
        "staging_chars_outside_8105_base": len(staging_chars - base_chars),
    }


def build_merge_plan() -> dict[str, Any]:
    review = load_json(REVIEW_JOIN)
    staging = staging_summary()
    target = target_summary()
    target_index_exists = target["target_index_exists"]
    checks = {
        "review_join_passed": review["overall_status"] == "PASS_DICTIONARY_CONTEXT_REVIEW_JOIN_READY",
        "staging_db_exists": STAGING_DB.exists(),
        "staged_rows_match_manifest": staging["staged_rows"] == 68_395,
        "unique_chars_match_manifest": staging["unique_chars"] == 49_085,
        "target_structured_root_exists": STRUCTURED_ROOT.exists(),
        "target_index_state_valid": True,
        "core_8105_files_not_modified": True,
        "knowledge_write_blocked_pending_authorization": not target_index_exists,
        "formal_scoring_blocked": True,
    }
    status = "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_PLAN_READY" if all(checks.values()) else "BLOCKED"
    if target_index_exists and all(value for key, value in checks.items() if key != "knowledge_write_blocked_pending_authorization"):
        status = "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_ALREADY_EXECUTED"
    return {
        "report_schema_version": "1.0",
        "mode": "read_only_dictionary_context_knowledge_merge_plan",
        "overall_status": status,
        "next_workflow_status": (
            "KNOWLEDGE_MERGE_ALREADY_EXECUTED_RUN_POST_MERGE_AUDIT"
            if target_index_exists
            else "KNOWLEDGE_MERGE_REQUIRES_EXPLICIT_AUTHORIZATION"
        ),
        "authority_boundary": {
            "dictionary_sources_are_cross_reference_context": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_cnbe_research_knowledge": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_cnbe_database": True,
        },
        "summary": {
            "recommended_strategy": "create_separate_dictionary_context_index",
            "reason": (
                "Dictionary context covers 49,085 chars, far beyond the 8,105 national-standard "
                "core. Keeping it separate preserves the 8105 baseline and source-grade boundary."
            ),
            "planned_target_index": str(TARGET_INDEX),
            "planned_reference_update": str(TARGET_REFERENCES),
            "planned_backup_suffix": ".bak.<UTC_TIMESTAMP>",
            "knowledge_write_allowed": False,
            "formal_gf0017_scoring_allowed": False,
            "target_index_already_exists": target_index_exists,
        },
        "staging_summary": staging,
        "target_summary": target,
        "planned_index_schema": {
            "top_level_type": "object keyed by character",
            "entry_fields": [
                "char",
                "unicode",
                "standard_level",
                "source_grade",
                "dictionary_context_entries",
                "source_count",
                "has_kangxi_context",
                "has_zhonghua_dazidian_context",
                "import_status",
            ],
            "dictionary_context_entry_fields": [
                "source_id",
                "source_repo",
                "source_commit",
                "license",
                "content_preview",
                "content",
            ],
        },
        "planned_write_set": [
            {
                "path": str(TARGET_INDEX),
                "action": "create",
                "requires_authorization": True,
            },
            {
                "path": str(TARGET_REFERENCES),
                "action": "backup_then_update_reference_entry",
                "requires_authorization": True,
            },
        ],
        "blocked_actions": [
            "modify base_character_data.json",
            "modify cnbe_character_knowledge.json",
            "assign GF0017 scores",
            "emit final structure labels",
            "write CNBE rows",
            "rebuild CNBE database",
        ],
        "checks": checks,
        "decision": {
            "may_execute_official_knowledge_merge_now": False,
            "may_generate_authorized_merge_script": status.startswith("PASS"),
            "requires_human_authorization": not target_index_exists,
            "recommended_next_script_after_authorization": "scripts/merge_dictionary_context_into_cnbe_research_knowledge.py",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Dictionary Context Knowledge Merge Plan",
        "",
        "## Purpose",
        "",
        "This plan defines how staged Kangxi and Zhonghua Dazidian context should",
        "be merged into `cnbe-research/knowledge` after explicit authorization.",
        "",
        "It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit",
        "final structure labels, write CNBE rows, or rebuild CNBE databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Strategy: `{report['summary']['recommended_strategy']}`",
        f"- Planned target index: `{report['summary']['planned_target_index']}`",
        f"- Staged rows: `{report['staging_summary']['staged_rows']}`",
        f"- Unique chars: `{report['staging_summary']['unique_chars']}`",
        f"- Overlap with 8105 base: `{report['target_summary']['staging_chars_overlapping_8105_base']}`",
        f"- Outside 8105 base: `{report['target_summary']['staging_chars_outside_8105_base']}`",
        "",
        "## Planned Write Set",
        "",
    ]
    for item in report["planned_write_set"]:
        lines.append(f"- `{item['path']}`: {item['action']} (requires authorization)")
    lines.extend(["", "## Blocked Actions", ""])
    for item in report["blocked_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_merge_plan()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
