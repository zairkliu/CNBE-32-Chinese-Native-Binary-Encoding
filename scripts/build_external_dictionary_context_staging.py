#!/usr/bin/env python3
"""Build a staging dictionary-context SQLite database from selected sources."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

IMPORT_PLAN = Path("reports/external_dictionary_context_import_plan.json")
NLP_KANGXI_DB = Path("build/external_dictionary_candidates/nlp-han-dicts/extracted/kangxi.4w.db")
NLP_ZHDZD_DB = Path("build/external_dictionary_candidates/nlp-han-dicts/extracted/zhdzd_simpledict.db")

DEFAULT_DB_OUTPUT = Path("build/dictionary_context_staging/dictionary_context_entries.sqlite")
DEFAULT_MANIFEST_OUTPUT = Path("reports/external_dictionary_context_import_manifest.json")
DEFAULT_MARKDOWN_OUTPUT = Path("reports/EXTERNAL_DICTIONARY_CONTEXT_IMPORT_MANIFEST.md")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unicode_label(char: str) -> str:
    if len(char) != 1:
        raise ValueError(f"expected one character, got {char!r}")
    return f"U+{ord(char):04X}"


def source_meta(plan: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in plan["source_priority"]:
        if source["source_id"] == source_id:
            return source
    raise KeyError(source_id)


def iter_dict_rows(path: Path) -> list[sqlite3.Row]:
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return list(conn.execute("select word, content, word1, word2 from Dict where word is not null order by id"))


def normalize_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [
        ("nlp_han_dicts_kangxi_4w", NLP_KANGXI_DB),
        ("nlp_han_dicts_zhonghua_dazidian", NLP_ZHDZD_DB),
    ]
    normalized: list[dict[str, Any]] = []
    for source_id, db_path in sources:
        meta = source_meta(plan, source_id)
        for row in iter_dict_rows(db_path):
            char = row["word"]
            if len(char) != 1:
                continue
            content = row["content"] or ""
            normalized.append(
                {
                    "source_id": source_id,
                    "source_repo": meta["repo"],
                    "source_commit": meta["commit"],
                    "license": meta["license"],
                    "source_grade": "cross_reference_dictionary_context",
                    "char": char,
                    "unicode": unicode_label(char),
                    "content": content,
                    "content_preview": content[:160],
                    "word1": row["word1"] or "",
                    "word2": row["word2"] or "",
                    "volume": "",
                    "import_status": "STAGED_DICTIONARY_CONTEXT_NOT_KNOWLEDGE_SOURCE",
                    "review_notes": "",
                }
            )
    return normalized


def build_staging_database(db_path: Path = DEFAULT_DB_OUTPUT) -> dict[str, Any]:
    plan = load_json(IMPORT_PLAN)
    if plan["overall_status"] != "PASS_DICTIONARY_CONTEXT_IMPORT_PLAN_READY":
        raise ValueError("dictionary context import plan must pass before staging build")
    rows = normalize_rows(plan)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            create table dictionary_context_entries (
                source_id text not null,
                source_repo text not null,
                source_commit text not null,
                license text not null,
                source_grade text not null,
                char text not null,
                unicode text not null,
                content text not null,
                content_preview text not null,
                word1 text not null,
                word2 text not null,
                volume text not null,
                import_status text not null,
                review_notes text not null,
                primary key (source_id, char)
            )
            """
        )
        conn.executemany(
            """
            insert or replace into dictionary_context_entries (
                source_id, source_repo, source_commit, license, source_grade,
                char, unicode, content, content_preview, word1, word2, volume,
                import_status, review_notes
            ) values (
                :source_id, :source_repo, :source_commit, :license, :source_grade,
                :char, :unicode, :content, :content_preview, :word1, :word2, :volume,
                :import_status, :review_notes
            )
            """,
            rows,
        )
        conn.execute("create index idx_dictionary_context_char on dictionary_context_entries(char)")
        conn.execute("create index idx_dictionary_context_unicode on dictionary_context_entries(unicode)")
        conn.execute("create index idx_dictionary_context_source on dictionary_context_entries(source_id)")
        total_rows = conn.execute("select count(*) from dictionary_context_entries").fetchone()[0]
        unique_chars = conn.execute("select count(distinct char) from dictionary_context_entries").fetchone()[0]
        by_source = dict(conn.execute("select source_id, count(*) from dictionary_context_entries group by source_id").fetchall())
    source_counts = Counter(row["source_id"] for row in rows)
    return {
        "report_schema_version": "1.0",
        "mode": "staging_external_dictionary_context_build",
        "overall_status": "PASS_DICTIONARY_CONTEXT_STAGING_READY",
        "next_workflow_status": "STAGING_READY_KNOWLEDGE_IMPORT_REQUIRES_AUTHORIZATION",
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
            "staging_db": str(db_path),
            "staged_rows": total_rows,
            "unique_chars": unique_chars,
            "source_counts": dict(sorted(by_source.items())),
            "raw_single_character_rows": dict(sorted(source_counts.items())),
            "knowledge_write_allowed": False,
            "formal_gf0017_scoring_allowed": False,
        },
        "checks": {
            "plan_passed": True,
            "staging_db_created": db_path.exists(),
            "staged_rows_positive": total_rows > 0,
            "unique_chars_positive": unique_chars > 0,
            "knowledge_write_blocked": True,
            "formal_scoring_blocked": True,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# External Dictionary Context Import Manifest",
        "",
        "## Purpose",
        "",
        "This manifest records a staging-only dictionary context database built",
        "from selected external Kangxi and Zhonghua Dazidian sources.",
        "",
        "It does not write `cnbe-research/knowledge`, assign GF0017 scores, emit",
        "final structure labels, write CNBE rows, or rebuild CNBE databases.",
        "",
        "## Result",
        "",
        f"- Overall status: `{report['overall_status']}`",
        f"- Next workflow status: `{report['next_workflow_status']}`",
        f"- Staging DB: `{report['summary']['staging_db']}`",
        f"- Staged rows: `{report['summary']['staged_rows']}`",
        f"- Unique chars: `{report['summary']['unique_chars']}`",
        "",
        "## Source Counts",
        "",
    ]
    for source_id, count in report["summary"]["source_counts"].items():
        lines.append(f"- `{source_id}`: {count}")
    lines.extend(["", "## Checks", ""])
    for check, value in report["checks"].items():
        lines.append(f"- `{check}`: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report = build_staging_database()
    write_json(DEFAULT_MANIFEST_OUTPUT, report)
    write_text(DEFAULT_MARKDOWN_OUTPUT, render_markdown(report))


if __name__ == "__main__":
    main()
