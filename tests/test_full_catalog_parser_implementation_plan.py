"""Tests for the full-catalog parser implementation plan."""

from __future__ import annotations

from scripts.plan_full_catalog_parser_implementation import build_parser_implementation_plan, render_markdown


def test_parser_implementation_plan_is_ready_without_execution() -> None:
    report = build_parser_implementation_plan()

    assert report["overall_status"] == "PASS_PARSER_IMPLEMENTATION_PLAN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["phases"] == 7
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False


def test_parser_implementation_plan_prioritizes_structure_first() -> None:
    report = build_parser_implementation_plan()
    phases = report["implementation_phases"]

    assert phases[0]["phase"] == 1
    assert phases[0]["gf0017_item"] == "structure_first_decomposition"
    assert phases[0]["runner_name"] == "run_structure_decomposition_evidence_parser"
    assert report["summary"]["phase_1_item"] == "structure_first_decomposition"


def test_parser_implementation_plan_keeps_writes_blocked() -> None:
    report = build_parser_implementation_plan()

    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["decision"]["may_modify_source_assets"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_parser_implementation_plan_has_stop_conditions() -> None:
    report = build_parser_implementation_plan()

    for phase in report["implementation_phases"]:
        assert "unicode_join_mismatch" in phase["stop_conditions"]
        assert "attempted_point_assignment" in phase["stop_conditions"]
        assert phase["assigns_points"] is False
        assert phase["writes_source_assets"] is False


def test_parser_implementation_markdown_states_decision_point() -> None:
    markdown = render_markdown(build_parser_implementation_plan())

    assert "# Full Catalog Parser Implementation Plan" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Phase 1 implementation is the next decision point" in markdown
