"""Tests for dictionary-context official knowledge merge planning."""

from __future__ import annotations

from scripts.plan_dictionary_context_knowledge_merge import (
    build_merge_plan,
    render_markdown,
)


def test_dictionary_context_merge_plan_is_ready() -> None:
    report = build_merge_plan()

    assert report["overall_status"] in {
        "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_PLAN_READY",
        "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_ALREADY_EXECUTED",
    }
    assert report["summary"]["recommended_strategy"] == "create_separate_dictionary_context_index"
    assert report["staging_summary"]["staged_rows"] == 68395
    assert report["staging_summary"]["unique_chars"] == 49085


def test_dictionary_context_merge_plan_keeps_core_8105_files_unchanged() -> None:
    report = build_merge_plan()

    blocked = set(report["blocked_actions"])
    assert "modify base_character_data.json" in blocked
    assert "modify cnbe_character_knowledge.json" in blocked
    assert report["checks"]["core_8105_files_not_modified"] is True


def test_dictionary_context_merge_plan_declares_schema_and_write_set() -> None:
    report = build_merge_plan()

    fields = set(report["planned_index_schema"]["entry_fields"])
    assert {"char", "unicode", "source_grade", "dictionary_context_entries"} <= fields
    write_paths = [item["path"] for item in report["planned_write_set"]]
    assert any(path.endswith("dictionary_context_index.json") for path in write_paths)
    assert any(path.endswith("references.json") for path in write_paths)


def test_dictionary_context_merge_plan_requires_authorization() -> None:
    report = build_merge_plan()

    assert all(value for key, value in report["checks"].items() if key != "knowledge_write_blocked_pending_authorization")
    assert report["decision"]["may_execute_official_knowledge_merge_now"] is False
    assert report["authority_boundary"]["does_not_modify_cnbe_research_knowledge"] is True
    assert report["summary"]["knowledge_write_allowed"] is False


def test_dictionary_context_merge_plan_markdown_states_scope() -> None:
    markdown = render_markdown(build_merge_plan())

    assert "# Dictionary Context Knowledge Merge Plan" in markdown
    assert "does not write `cnbe-research/knowledge`" in markdown
    assert "Planned Write Set" in markdown
