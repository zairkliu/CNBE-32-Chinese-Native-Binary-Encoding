"""Tests for the read-only unified Hanzi evidence index."""

from __future__ import annotations

import pytest

from scripts.build_unified_hanzi_evidence_index import build_unified_index, render_markdown


@pytest.fixture(scope="module")
def unified_report() -> dict:
    return build_unified_index()


def test_unified_hanzi_evidence_index_builds_full_catalog(unified_report: dict) -> None:
    report = unified_report
    assert report["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_BUILT"
    assert report["summary"]["total_entries"] == 97686
    assert len(report["index"]) == 97686
    assert report["index_schema"][0:6] == [
        "char",
        "codepoint",
        "catalog_offset",
        "worksheet_row",
        "catalog_scope",
        "review_status",
    ]
    assert report["summary"]["catalog_scope_counts"]["8105_core"] == 8105
    assert report["summary"]["catalog_scope_counts"]["outside_8105_agent_candidate"] == 89581


def test_unified_hanzi_evidence_index_blocks_scoring_and_writes(unified_report: dict) -> None:
    report = unified_report

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    for entry in report["samples"].values():
        assert entry["score"] is None
        assert entry["score_status"] == "NOT_SCORED_UNIFIED_EVIDENCE_INDEX_ONLY"
        forbidden_profile = report["profiles"]["forbidden_outputs"][entry["forbidden_outputs_profile_id"]]
        assert "gf0017_score" in forbidden_profile
        assert "final_structure_label" in forbidden_profile
        assert "cnbe32_repair_value" in forbidden_profile
        assert "database_write_record" in forbidden_profile
        assert "final_structure_label" not in entry
        assert "database_write_record" not in entry


def test_unified_hanzi_evidence_index_preserves_authority_boundaries(unified_report: dict) -> None:
    report = unified_report

    assert report["authority_boundary"]["national_standard_core_separate"] is True
    assert report["authority_boundary"]["dictionary_context_cross_reference_only"] is True
    assert report["authority_boundary"]["wikipedia_lowest_tier_cross_reference_only"] is True
    assert report["authority_boundary"]["agent_standard_not_national_standard"] is True

    core = report["samples"]["U+4E00"]
    assert core["char"] == "一"
    assert core["catalog_scope"] == "8105_core"
    assert core["national_standard_core"]["status"] == "JOINED_8105_NATIONAL_STANDARD_CORE"
    assert core["national_standard_core"]["can_assign_points"] is False

    outside = report["samples"]["U+3400"]
    assert outside["char"] == "㐀"
    assert outside["catalog_scope"] == "outside_8105_agent_candidate"
    assert outside["national_standard_core"]["status"] == "OUTSIDE_8105_NO_DIRECT_NATIONAL_STANDARD_CORE_ROW"
    assert outside["agent_standard_context"]["can_emit_final_structure_label"] is False
    assert outside["gf0017_item_statuses"]["source_join_profile_id"] in report["profiles"]["source_join_item_statuses"]
    assert outside["evidence_gaps"]["profile_id"] in report["profiles"]["evidence_gaps"]


def test_unified_hanzi_evidence_index_keeps_review_context_bounded(unified_report: dict) -> None:
    report = unified_report

    xin = report["samples"]["U+946B"]
    assert xin["char"] == "鑫"
    assert xin["dictionary_context"]["has_context"] is True
    assert xin["dictionary_context"]["preview_count"] <= 2
    assert xin["dictionary_context"]["detail_ref"] == "dictionary_context:U+946B"
    assert xin["cihai_context"]["hit_count"] >= 0

    extension_sample = report["samples"]["U+3400"]
    assert extension_sample["wiki_context"]["source_grade"] == "lowest_tier_cross_reference"
    assert extension_sample["wiki_context"]["hit_count"] >= 1
    assert extension_sample["wiki_context"]["detail_ref"] == "wiki_context:U+3400"


def test_unified_hanzi_evidence_index_markdown_states_no_write_scope(unified_report: dict) -> None:
    markdown = render_markdown(unified_report)

    assert "# Unified Hanzi Evidence Index" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "May start formal GF0017 scoring: `False`" in markdown
    assert "May write CNBE rows: `False`" in markdown
