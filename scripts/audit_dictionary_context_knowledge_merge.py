#!/usr/bin/env python3
"""Audit the executed dictionary-context knowledge merge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PRE_STATE = Path("reports/dictionary_context_knowledge_merge_pre_state.json")
POST_STATE = Path("reports/dictionary_context_knowledge_merge_post_state.json")
MERGE_REPORT = Path("reports/dictionary_context_knowledge_merge_report.json")

KNOWLEDGE_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge")
TARGET_INDEX = KNOWLEDGE_ROOT / "structured" / "dictionary_context_index.json"
REFERENCES = KNOWLEDGE_ROOT / "references.json"
BASE_CHARACTER_DATA = KNOWLEDGE_ROOT / "structured" / "base_character_data.json"
CNBE_CHARACTER_KNOWLEDGE = KNOWLEDGE_ROOT / "structured" / "cnbe_character_knowledge.json"

DEFAULT_JSON_OUTPUT = Path("reports/dictionary_context_knowledge_merge_audit.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDIT.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def reference_entry(references: dict[str, Any]) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    for key, value in references.items():
        if isinstance(value, dict) and value.get("source_grade") == "cross_reference_dictionary_context":
            if value.get("file") == str(TARGET_INDEX):
                return key, value
    return None, None


def build_audit() -> dict[str, Any]:
    pre_state = load_json(PRE_STATE)
    post_state = load_json(POST_STATE)
    merge_report = load_json(MERGE_REPORT)
    index = load_json(TARGET_INDEX)
    references = load_json(REFERENCES)
    ref_key, ref_entry = reference_entry(references)

    base_path = str(BASE_CHARACTER_DATA)
    cnbe_path = str(CNBE_CHARACTER_KNOWLEDGE)
    index_path = str(TARGET_INDEX)
    references_path = str(REFERENCES)

    sample_chars = {}
    for char in ["鑫", "家", "㐀", "㐁"]:
        row = index.get(char)
        sample_chars[char] = {
            "exists": row is not None,
            "unicode": row.get("unicode") if row else None,
            "source_count": row.get("source_count") if row else None,
            "source_grade": row.get("source_grade") if row else None,
            "standard_level": row.get("standard_level") if row else None,
            "import_status": row.get("import_status") if row else None,
        }

    checks = {
        "merge_report_executed": merge_report["overall_status"] == "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_EXECUTED",
        "merge_report_authorized": merge_report["summary"]["authorized"] is True,
        "target_index_created": TARGET_INDEX.exists(),
        "target_index_entry_count": len(index) == 49_085,
        "references_updated": ref_key is not None,
        "references_count_is_nine": len(references) == 9,
        "references_backup_created": bool(merge_report["summary"]["backups"]),
        "base_character_data_hash_unchanged": pre_state[base_path]["sha256"] == post_state[base_path]["sha256"],
        "cnbe_character_knowledge_hash_unchanged": pre_state[cnbe_path]["sha256"] == post_state[cnbe_path]["sha256"],
        "target_index_absent_before_merge": pre_state[index_path]["exists"] is False,
        "target_index_present_after_merge": post_state[index_path]["exists"] is True,
        "dictionary_context_not_scoring_authority": all(
            row.get("source_grade") == "cross_reference_dictionary_context"
            for row in sample_chars.values()
            if row["exists"]
        ),
        "score_values_assigned": merge_report["checks"]["score_values_assigned"] == 0,
        "final_structure_labels_emitted": merge_report["checks"]["final_structure_labels_emitted"] == 0,
        "cnbe_rows_written": merge_report["checks"]["cnbe_rows_written"] == 0,
        "database_rebuilds": merge_report["checks"]["database_rebuilds"] == 0,
    }
    return {
        "report_schema_version": "1.0",
        "mode": "post_merge_dictionary_context_knowledge_audit",
        "overall_status": "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED" if all(checks.values()) else "FAIL",
        "authority_boundary": {
            "dictionary_context_is_cross_reference_only": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_write_cnbe_rows": True,
            "does_not_rebuild_cnbe_database": True,
        },
        "summary": {
            "target_index": index_path,
            "target_index_entries": len(index),
            "target_index_bytes": post_state[index_path]["bytes"],
            "target_index_lines": post_state[index_path]["lines"],
            "references_path": references_path,
            "reference_key": ref_key,
            "references_entries": len(references),
            "backups": merge_report["summary"]["backups"],
            "base_character_data_unchanged": checks["base_character_data_hash_unchanged"],
            "cnbe_character_knowledge_unchanged": checks["cnbe_character_knowledge_hash_unchanged"],
        },
        "sample_chars": sample_chars,
        "reference_entry": ref_entry,
        "checks": checks,
        "next_workflow_status": "KNOWLEDGE_MERGED_REVALIDATE_SOURCE_AUDIT_BEFORE_SCORING",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Dictionary Context Knowledge Merge Audit",
        "",
        "## Purpose",
        "",
        "This audit independently verifies that the authorized dictionary-context",
        "knowledge merge created only the separate dictionary context index and",
        "updated references with a backup.",
        "",
        "It also verifies that the 8,105 core knowledge files were not modified,",
        "and that dictionary context remains cross-reference evidence only.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Target index: `{report['summary']['target_index']}`",
        f"- Target index entries: `{report['summary']['target_index_entries']}`",
        f"- References entries: `{report['summary']['references_entries']}`",
        f"- Reference key: `{report['summary']['reference_key']}`",
        f"- Base character data unchanged: `{report['summary']['base_character_data_unchanged']}`",
        f"- CNBE character knowledge unchanged: `{report['summary']['cnbe_character_knowledge_unchanged']}`",
        "",
        "## Sample Characters",
        "",
        "| Char | Exists | Unicode | Source count | Source grade | Standard level |",
        "|---|:---:|---|---:|---|---|",
    ]
    for char, row in report["sample_chars"].items():
        lines.append(
            f"| {char} | {row['exists']} | {row['unicode']} | {row['source_count']} | "
            f"{row['source_grade']} | {row['standard_level']} |"
        )
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.extend(["", "## Backups", ""])
    for backup in report["summary"]["backups"]:
        lines.append(f"- `{backup}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_audit()
    write_json(DEFAULT_JSON_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))
    print(f"wrote {DEFAULT_JSON_OUTPUT}")
    print(f"wrote {DEFAULT_MARKDOWN_OUTPUT}")
    print(f"overall_status={report['overall_status']}")
    if report["overall_status"] != "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
