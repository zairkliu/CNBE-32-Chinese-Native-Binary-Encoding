"""Tests for external dictionary context staging database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.build_external_dictionary_context_staging import (
    DEFAULT_DB_OUTPUT,
    build_staging_database,
    render_markdown,
)


def test_dictionary_context_staging_is_ready() -> None:
    report = build_staging_database()

    assert report["overall_status"] == "PASS_DICTIONARY_CONTEXT_STAGING_READY"
    assert report["summary"]["staged_rows"] > 60000
    assert report["summary"]["unique_chars"] > 49000


def test_dictionary_context_staging_contains_expected_sources() -> None:
    report = build_staging_database()

    assert set(report["summary"]["source_counts"]) == {
        "nlp_han_dicts_kangxi_4w",
        "nlp_han_dicts_zhonghua_dazidian",
    }


def test_dictionary_context_staging_schema_and_lookup() -> None:
    build_staging_database()

    assert DEFAULT_DB_OUTPUT.exists()
    with sqlite3.connect(DEFAULT_DB_OUTPUT) as conn:
        cols = [row[1] for row in conn.execute("pragma table_info(dictionary_context_entries)")]
        assert {"source_id", "char", "unicode", "content", "source_grade", "license"} <= set(cols)
        rows = conn.execute(
            "select source_id, unicode, source_grade from dictionary_context_entries where char = ?",
            ("㐁",),
        ).fetchall()
    assert rows
    assert all(row[2] == "cross_reference_dictionary_context" for row in rows)


def test_dictionary_context_staging_keeps_writes_and_scores_blocked() -> None:
    report = build_staging_database()

    assert all(report["checks"].values())
    assert report["authority_boundary"]["does_not_modify_cnbe_research_knowledge"] is True
    assert report["authority_boundary"]["does_not_assign_gf0017_scores"] is True
    assert report["summary"]["knowledge_write_allowed"] is False
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False


def test_dictionary_context_staging_markdown_states_scope() -> None:
    markdown = render_markdown(build_staging_database())

    assert "# External Dictionary Context Import Manifest" in markdown
    assert "does not write `cnbe-research/knowledge`" in markdown
    assert "Staging DB" in markdown
