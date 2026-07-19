"""Tests for offline-Wikipedia cross-reference index planning."""

from __future__ import annotations

from scripts.plan_wikipedia_structure_cross_reference_index import build_wikipedia_index_plan, render_markdown


def test_wikipedia_index_plan_is_ready() -> None:
    report = build_wikipedia_index_plan()

    assert report["overall_status"] == "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_PLAN_READY"
    assert report["summary"]["wiki_file_exists"] is True
    assert report["summary"]["rows_without_dictionary_review_hit"] == 84939


def test_wikipedia_index_plan_uses_lowest_tier_evidence() -> None:
    report = build_wikipedia_index_plan()

    assert report["index_design"]["evidence_grade"] == "lowest_tier_cross_reference"
    assert "do_not_assign_gf0017_points_from_wiki" in report["index_design"]["forbidden_uses"]
    assert "do_not_claim_national_standard_evidence_from_wiki" in report["index_design"]["forbidden_uses"]


def test_wikipedia_index_plan_keeps_all_write_gates_blocked() -> None:
    report = build_wikipedia_index_plan()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_source_assets"] is False


def test_wikipedia_index_markdown_states_lowest_tier() -> None:
    markdown = render_markdown(build_wikipedia_index_plan())

    assert "# Wikipedia Structure Cross-Reference Index Plan" in markdown
    assert "lowest-tier cross-reference only" in markdown
    assert "must not assign" in markdown
