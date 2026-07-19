"""Tests for authorized dictionary-context knowledge merge script."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.merge_dictionary_context_into_cnbe_research_knowledge import (
    AUTHORIZATION_TOKEN,
    build_report,
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_staging_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
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
            insert into dictionary_context_entries values (
                :source_id, :source_repo, :source_commit, :license, :source_grade,
                :char, :unicode, :content, :content_preview, :word1, :word2, :volume,
                :import_status, :review_notes
            )
            """,
            [
                {
                    "source_id": "nlp_han_dicts_kangxi_4w",
                    "source_repo": "https://github.com/leechenhwa2/nlp-han-dicts",
                    "source_commit": "test",
                    "license": "BSD-2-Clause",
                    "source_grade": "cross_reference_dictionary_context",
                    "char": "鑫",
                    "unicode": "U+946B",
                    "content": "test kangxi context",
                    "content_preview": "test kangxi context",
                    "word1": "",
                    "word2": "",
                    "volume": "",
                    "import_status": "STAGED_DICTIONARY_CONTEXT_NOT_KNOWLEDGE_SOURCE",
                    "review_notes": "",
                },
                {
                    "source_id": "nlp_han_dicts_zhonghua_dazidian",
                    "source_repo": "https://github.com/leechenhwa2/nlp-han-dicts",
                    "source_commit": "test",
                    "license": "BSD-2-Clause",
                    "source_grade": "cross_reference_dictionary_context",
                    "char": "鑫",
                    "unicode": "U+946B",
                    "content": "test zhdzd context",
                    "content_preview": "test zhdzd context",
                    "word1": "",
                    "word2": "",
                    "volume": "",
                    "import_status": "STAGED_DICTIONARY_CONTEXT_NOT_KNOWLEDGE_SOURCE",
                    "review_notes": "",
                },
            ],
        )


def make_knowledge_root(path: Path) -> None:
    write_json(path / "structured" / "base_character_data.json", {"鑫": {"unicode": "U+946B"}})
    write_json(path / "structured" / "cnbe_character_knowledge.json", [{"char": "鑫", "unicode": "U+946B"}])
    write_json(path / "references.json", {"reference_1": {"name": "existing", "source": "test"}})


def test_dictionary_context_merge_dry_run_does_not_write(tmp_path: Path) -> None:
    knowledge_root = tmp_path / "knowledge"
    staging_db = tmp_path / "staging.sqlite"
    make_knowledge_root(knowledge_root)
    make_staging_db(staging_db)

    report = build_report(
        execute=False,
        authorization_token="",
        knowledge_root=knowledge_root,
        staging_db=staging_db,
    )

    assert report["overall_status"] == "PASS_DRY_RUN_READY"
    assert report["summary"]["authorized"] is False
    assert not (knowledge_root / "structured" / "dictionary_context_index.json").exists()


def test_dictionary_context_merge_rejects_execute_without_exact_token(tmp_path: Path) -> None:
    knowledge_root = tmp_path / "knowledge"
    staging_db = tmp_path / "staging.sqlite"
    make_knowledge_root(knowledge_root)
    make_staging_db(staging_db)

    with pytest.raises(PermissionError):
        build_report(
            execute=True,
            authorization_token="wrong",
            knowledge_root=knowledge_root,
            staging_db=staging_db,
        )


def test_dictionary_context_merge_executes_with_token_and_preserves_core_files(tmp_path: Path) -> None:
    knowledge_root = tmp_path / "knowledge"
    staging_db = tmp_path / "staging.sqlite"
    make_knowledge_root(knowledge_root)
    make_staging_db(staging_db)
    base_before = (knowledge_root / "structured" / "base_character_data.json").read_text(encoding="utf-8")
    cnbe_before = (knowledge_root / "structured" / "cnbe_character_knowledge.json").read_text(encoding="utf-8")

    report = build_report(
        execute=True,
        authorization_token=AUTHORIZATION_TOKEN,
        knowledge_root=knowledge_root,
        staging_db=staging_db,
    )

    index_path = knowledge_root / "structured" / "dictionary_context_index.json"
    assert report["overall_status"] == "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_EXECUTED"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["鑫"]["source_count"] == 2
    assert index["鑫"]["standard_level"] == "cross_reference_context_not_national_standard"
    assert (knowledge_root / "structured" / "base_character_data.json").read_text(encoding="utf-8") == base_before
    assert (knowledge_root / "structured" / "cnbe_character_knowledge.json").read_text(encoding="utf-8") == cnbe_before


def test_dictionary_context_merge_updates_references_with_boundary(tmp_path: Path) -> None:
    knowledge_root = tmp_path / "knowledge"
    staging_db = tmp_path / "staging.sqlite"
    make_knowledge_root(knowledge_root)
    make_staging_db(staging_db)

    build_report(
        execute=True,
        authorization_token=AUTHORIZATION_TOKEN,
        knowledge_root=knowledge_root,
        staging_db=staging_db,
    )

    references = json.loads((knowledge_root / "references.json").read_text(encoding="utf-8"))
    merged = references["reference_2"]
    assert merged["source_grade"] == "cross_reference_dictionary_context"
    assert "not national-standard structure authority" in merged["standard_boundary"]
