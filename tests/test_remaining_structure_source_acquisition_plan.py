"""Tests for remaining structure source acquisition planning."""

from __future__ import annotations

from scripts.plan_remaining_structure_source_acquisition import build_source_acquisition_plan, render_markdown


def test_remaining_source_acquisition_plan_is_ready() -> None:
    report = build_source_acquisition_plan()

    assert report["overall_status"] == "PASS_REMAINING_STRUCTURE_SOURCE_ACQUISITION_PLAN_READY"
    assert report["summary"]["remaining_rows_without_wiki_dictionary_or_source_hit"] == 73831
    assert report["summary"]["stronger_authoritative_source_available"] is False


def test_remaining_source_acquisition_plan_classifies_candidate_resources() -> None:
    report = build_source_acquisition_plan()
    resources = {resource["id"]: resource for resource in report["candidate_resources"]}

    assert resources["gf_gb_component_standards"]["source_grade"] == "direct_standard_for_rules_not_row_level_ids"
    assert resources["unihan2"]["source_grade"] == "unicode_cross_reference_not_structure_authority"
    assert resources["kangxi_4w"]["source_grade"] == "dictionary_cross_reference"
    assert resources["cjk_decomp"]["source_grade"] == "third_party_ids_cross_reference"
    assert resources["decomp_data"]["remaining_row_hits"] == 0
    for resource in resources.values():
        assert resource["can_close_remaining_gap_as_authority"] is False


def test_remaining_source_acquisition_plan_keeps_scoring_and_writes_blocked() -> None:
    report = build_source_acquisition_plan()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_remaining_source_acquisition_markdown_states_agent_standard_next() -> None:
    markdown = render_markdown(build_source_acquisition_plan())

    assert "# Remaining Structure Source Acquisition Plan" in markdown
    assert "Stronger authoritative source available: `False`" in markdown
    assert "Proceed with an Agent-standard plan" in markdown
