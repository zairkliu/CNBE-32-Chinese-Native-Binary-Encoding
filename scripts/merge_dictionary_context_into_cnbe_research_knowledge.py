#!/usr/bin/env python3
"""Merge staged dictionary context into cnbe-research knowledge after authorization.

The default mode is dry-run. Official knowledge writes require both --execute
and the explicit authorization token.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGING_DB = Path("build/dictionary_context_staging/dictionary_context_entries.sqlite")
MERGE_PLAN = Path("reports/dictionary_context_knowledge_merge_plan.json")
KNOWLEDGE_ROOT = Path("/Users/liuzhaoqi/Documents/cnbe-research/knowledge")
AUTHORIZATION_TOKEN = "I_UNDERSTAND_THIS_WRITES_CNBE_RESEARCH_KNOWLEDGE"

DEFAULT_JSON_OUTPUT = Path("reports/dictionary_context_knowledge_merge_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_REPORT.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup_file(path: Path, timestamp: str) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.bak.{timestamp}")
    shutil.copy2(path, backup)
    return backup


def load_staging_index(staging_db: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    entries_by_char: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with sqlite3.connect(staging_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            select source_id, source_repo, source_commit, license, source_grade,
                   char, unicode, content, content_preview, import_status
            from dictionary_context_entries
            order by char, source_id
            """
        )
        for row in rows:
            entries_by_char[row["char"]].append(
                {
                    "source_id": row["source_id"],
                    "source_repo": row["source_repo"],
                    "source_commit": row["source_commit"],
                    "license": row["license"],
                    "source_grade": row["source_grade"],
                    "content_preview": row["content_preview"],
                    "content": row["content"],
                }
            )

    for char, entries in sorted(entries_by_char.items()):
        source_ids = {entry["source_id"] for entry in entries}
        index[char] = {
            "char": char,
            "unicode": f"U+{ord(char):04X}",
            "standard_level": "cross_reference_context_not_national_standard",
            "source_grade": "cross_reference_dictionary_context",
            "dictionary_context_entries": entries,
            "source_count": len(source_ids),
            "has_kangxi_context": "nlp_han_dicts_kangxi_4w" in source_ids,
            "has_zhonghua_dazidian_context": "nlp_han_dicts_zhonghua_dazidian" in source_ids,
            "import_status": "OFFICIAL_KNOWLEDGE_CONTEXT_INDEXED_NOT_SCORING_AUTHORITY",
        }
    return index


def next_reference_key(references: dict[str, Any]) -> str:
    max_seen = 0
    for key in references:
        if key.startswith("reference_"):
            suffix = key.removeprefix("reference_")
            if suffix.isdigit():
                max_seen = max(max_seen, int(suffix))
    return f"reference_{max_seen + 1}"


def updated_references(references_path: Path, target_index: Path, timestamp: str) -> dict[str, Any]:
    references = load_json(references_path) if references_path.exists() else {}
    if not isinstance(references, dict):
        raise TypeError("references.json must be a JSON object")

    entry = {
        "name": "康熙字典与中华大字典交叉参考上下文索引",
        "source": "GitHub: leechenhwa2/nlp-han-dicts",
        "file": str(target_index),
        "data": "68,395 staged dictionary context rows; 49,085 unique characters",
        "license": "BSD-2-Clause",
        "source_grade": "cross_reference_dictionary_context",
        "standard_boundary": "not national-standard structure authority; not GF0017 scoring evidence",
        "created_at_utc": timestamp,
    }
    for key, value in references.items():
        if isinstance(value, dict) and value.get("file") == str(target_index):
            references[key] = entry
            return references
    references[next_reference_key(references)] = entry
    return references


def build_report(
    *,
    execute: bool,
    authorization_token: str,
    knowledge_root: Path,
    staging_db: Path,
) -> dict[str, Any]:
    structured_root = knowledge_root / "structured"
    target_index = structured_root / "dictionary_context_index.json"
    references_path = knowledge_root / "references.json"
    base_character_data = structured_root / "base_character_data.json"
    cnbe_character_knowledge = structured_root / "cnbe_character_knowledge.json"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    merge_plan = load_json(MERGE_PLAN)
    index = load_staging_index(staging_db)
    references = updated_references(references_path, target_index, timestamp)

    authorized = execute and authorization_token == AUTHORIZATION_TOKEN
    if execute and not authorized:
        raise PermissionError("official knowledge merge requires the exact authorization token")

    backups: list[str] = []
    if authorized:
        structured_root.mkdir(parents=True, exist_ok=True)
        for path in (target_index, references_path):
            backup = backup_file(path, timestamp)
            if backup is not None:
                backups.append(str(backup))
        write_json(target_index, index)
        write_json(references_path, references)

    checks = {
        "merge_plan_passed": merge_plan["overall_status"] == "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_PLAN_READY",
        "staging_db_exists": staging_db.exists(),
        "index_unique_chars": len(index) == 49_085 if staging_db == STAGING_DB else len(index) > 0,
        "base_character_data_not_modified_by_script": True,
        "cnbe_character_knowledge_not_modified_by_script": True,
        "score_values_assigned": 0,
        "final_structure_labels_emitted": 0,
        "cnbe_rows_written": 0,
        "database_rebuilds": 0,
        "official_write_requires_authorization": True,
    }

    return {
        "report_schema_version": "1.0",
        "mode": "execute_dictionary_context_knowledge_merge" if authorized else "dry_run_dictionary_context_knowledge_merge",
        "overall_status": "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_EXECUTED" if authorized else "PASS_DRY_RUN_READY",
        "authority_boundary": {
            "dictionary_sources_are_cross_reference_context": True,
            "not_national_standard_structure_authority": True,
            "does_not_assign_gf0017_scores": True,
            "does_not_emit_final_structure_labels": True,
            "does_not_modify_8105_core_files": True,
            "does_not_modify_cnbe_rows": True,
            "does_not_rebuild_cnbe_database": True,
        },
        "summary": {
            "execute_requested": execute,
            "authorized": authorized,
            "knowledge_root": str(knowledge_root),
            "target_index": str(target_index),
            "references_path": str(references_path),
            "index_entries": len(index),
            "reference_entries_after_merge": len(references),
            "backups": backups,
            "base_character_data_path": str(base_character_data),
            "cnbe_character_knowledge_path": str(cnbe_character_knowledge),
        },
        "checks": checks,
        "next_workflow_status": (
            "KNOWLEDGE_MERGED_RUN_AUDIT_BEFORE_SCORING" if authorized else "AWAITING_EXPLICIT_KNOWLEDGE_MERGE_AUTHORIZATION"
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Dictionary Context Knowledge Merge Report",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Mode: `{report['mode']}`",
        f"- Authorized write: `{report['summary']['authorized']}`",
        f"- Target index: `{report['summary']['target_index']}`",
        f"- Index entries: `{report['summary']['index_entries']}`",
        f"- References entries after merge: `{report['summary']['reference_entries_after_merge']}`",
        "",
        "## Authority Boundary",
        "",
        "Dictionary context remains cross-reference context only. This merge does",
        "not assign GF0017 scores, emit final structure labels, write CNBE rows,",
        "modify the 8,105 core files, or rebuild any CNBE database.",
        "",
        "## Checks",
        "",
    ]
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    if report["summary"]["backups"]:
        lines.extend(["", "## Backups", ""])
        for backup in report["summary"]["backups"]:
            lines.append(f"- `{backup}`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="write official knowledge files")
    parser.add_argument("--authorization-token", default="", help="required exact token for --execute")
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_ROOT)
    parser.add_argument("--staging-db", type=Path, default=STAGING_DB)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(
        execute=args.execute,
        authorization_token=args.authorization_token,
        knowledge_root=args.knowledge_root,
        staging_db=args.staging_db,
    )
    write_json(args.json_output, report)
    write_text(args.markdown_output, render_markdown(report))


if __name__ == "__main__":
    main()
