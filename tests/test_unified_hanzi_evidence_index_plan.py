"""Tests for the unified Hanzi evidence index plan."""

from __future__ import annotations

from scripts.plan_unified_hanzi_evidence_index import build_plan, render_markdown


def test_unified_hanzi_evidence_index_plan_is_ready() -> None:
    report = build_plan()

    assert report["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_PLAN_READY"
    assert report["decision"]["may_build_unified_evidence_index"] is True
    assert report["input_summaries"]["full_catalog_rows"] == 97686
    assert report["input_summaries"]["unique_unicode"] == 97686


def test_unified_hanzi_evidence_index_plan_keeps_layer_boundaries() -> None:
    report = build_plan()

    assert report["authority_boundary"]["national_standard_core_separate"] is True
    assert report["authority_boundary"]["dictionary_context_cross_reference_only"] is True
    assert report["authority_boundary"]["wikipedia_lowest_tier_cross_reference_only"] is True
    assert report["layer_contract"]["dictionary_cross_reference_context"]["must_not_use_as"] == (
        "national-standard structure authority"
    )


def test_unified_hanzi_evidence_index_plan_counts_core_inputs() -> None:
    report = build_plan()

    assert report["input_summaries"]["base_character_data"]["count"] == 8105
    assert report["input_summaries"]["cnbe_character_knowledge"]["count"] == 8105
    assert report["input_summaries"]["dictionary_context_index"]["count"] == 49085
    assert report["input_summaries"]["yuanliu_index"]["count"] == 9574
    assert report["input_summaries"]["cihai_index"]["count"] == 5423


def test_unified_hanzi_evidence_index_plan_blocks_scoring_and_writes() -> None:
    report = build_plan()

    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    forbidden = set(report["planned_index_schema"]["forbidden_fields_before_later_gates"])
    assert {"gf0017_score", "final_structure_label", "cnbe32_repair_value"} <= forbidden


def test_unified_hanzi_evidence_index_plan_markdown_states_scope() -> None:
    markdown = render_markdown(build_plan())

    assert "# Unified Hanzi Evidence Index Plan" in markdown
    assert "does not assign" in markdown
    assert "Forbidden Before Later Gates" in markdown
