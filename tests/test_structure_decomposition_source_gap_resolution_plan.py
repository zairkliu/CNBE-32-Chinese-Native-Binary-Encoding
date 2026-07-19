"""Tests for structure/decomposition source-gap resolution planning."""

from __future__ import annotations

from scripts.plan_structure_decomposition_source_gap_resolution import build_resolution_plan, render_markdown


def test_source_gap_resolution_plan_is_ready() -> None:
    report = build_resolution_plan()

    assert report["overall_status"] == "PASS_STRUCTURE_SOURCE_GAP_RESOLUTION_PLAN_READY"
    assert report["summary"]["source_gap_rows"] == 85001
    assert report["summary"]["score_values_assigned"] == 0


def test_source_gap_resolution_plan_records_dictionary_tiers() -> None:
    report = build_resolution_plan()

    assert "hanzi_yuanliu" in report["source_policy"]
    assert "cihai" in report["source_policy"]
    assert "wikipedia_offline" in report["source_policy"]
    assert "not direct national-standard authority" in report["source_policy"]["hanzi_yuanliu"]
    assert "lowest-tier cross-reference" in report["source_policy"]["wikipedia_offline"]


def test_source_gap_resolution_plan_keeps_write_and_score_gates_blocked() -> None:
    report = build_resolution_plan()

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_source_assets"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_source_gap_resolution_plan_has_read_only_extractor_phases() -> None:
    report = build_resolution_plan()

    phase_names = {phase["phase_name"] for phase in report["resolution_phases"]}
    assert "hanzi_yuanliu_structure_clue_extraction" in phase_names
    assert "cihai_definition_review_packet" in phase_names
    assert "offline_wikipedia_lowest_tier_cross_reference" in phase_names
    for phase in report["resolution_phases"]:
        assert phase["can_assign_points"] is False
        assert phase["writes_source_assets"] is False


def test_source_gap_resolution_markdown_states_no_scoring() -> None:
    markdown = render_markdown(build_resolution_plan())

    assert "# Structure/Decomposition Source-Gap Resolution Plan" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "offline Wiki as the lowest-tier" in markdown
