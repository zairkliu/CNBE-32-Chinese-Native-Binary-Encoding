"""Tests for post-merge dictionary context knowledge audit."""

from __future__ import annotations

from scripts.audit_dictionary_context_knowledge_merge import build_audit, render_markdown


def test_dictionary_context_knowledge_merge_audit_passes() -> None:
    report = build_audit()

    assert report["overall_status"] == "PASS_DICTIONARY_CONTEXT_KNOWLEDGE_MERGE_AUDITED"
    assert report["summary"]["target_index_entries"] == 49085
    assert report["summary"]["references_entries"] == 9


def test_dictionary_context_knowledge_merge_audit_preserves_core_files() -> None:
    report = build_audit()

    assert report["checks"]["base_character_data_hash_unchanged"] is True
    assert report["checks"]["cnbe_character_knowledge_hash_unchanged"] is True
    assert report["checks"]["cnbe_rows_written"] is True
    assert report["checks"]["database_rebuilds"] is True


def test_dictionary_context_knowledge_merge_audit_keeps_context_boundary() -> None:
    report = build_audit()

    assert report["authority_boundary"]["dictionary_context_is_cross_reference_only"] is True
    assert report["authority_boundary"]["not_national_standard_structure_authority"] is True
    assert report["checks"]["score_values_assigned"] is True
    assert report["checks"]["final_structure_labels_emitted"] is True


def test_dictionary_context_knowledge_merge_audit_samples_are_present() -> None:
    report = build_audit()

    for char in ["鑫", "家", "㐀", "㐁"]:
        assert report["sample_chars"][char]["exists"] is True
        assert report["sample_chars"][char]["source_grade"] == "cross_reference_dictionary_context"


def test_dictionary_context_knowledge_merge_audit_markdown_states_result() -> None:
    markdown = render_markdown(build_audit())

    assert "# Dictionary Context Knowledge Merge Audit" in markdown
    assert "8,105 core knowledge files were not modified" in markdown
    assert "Target index entries" in markdown
