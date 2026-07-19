"""Tests for the full-catalog source-resolution plan."""

from __future__ import annotations

from scripts.plan_full_catalog_source_resolution import build_source_resolution_plan, render_markdown


def test_source_resolution_plan_is_ready_without_scoring() -> None:
    report = build_source_resolution_plan()

    assert report["overall_status"] == "PASS_SOURCE_RESOLUTION_PLAN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False


def test_source_resolution_plan_splits_policy_and_automatic_items() -> None:
    report = build_source_resolution_plan()

    assert report["summary"]["policy_decision_items"] == ["character_set_coverage"]
    assert set(report["summary"]["automated_resolution_items"]) == {
        "stroke_shape",
        "stroke_order",
        "component_validity",
        "component_name_validity",
        "radical_validity",
        "independent_character_rule",
        "structure_first_decomposition",
    }
    assert report["summary"]["resolution_class_counts"] == {
        "POLICY_DECISION_REQUIRED": 1,
        "ROW_LEVEL_EXTRACTION_REQUIRED": 6,
        "SOURCE_EXTRACTION_SPEC_REQUIRED": 1,
    }


def test_source_resolution_plan_keeps_every_item_blocked_for_all_rows() -> None:
    report = build_source_resolution_plan()

    assert set(report["summary"]["blocked_rows_by_item"]) == {
        "character_set_coverage",
        "stroke_shape",
        "stroke_order",
        "component_validity",
        "component_name_validity",
        "radical_validity",
        "independent_character_rule",
        "structure_first_decomposition",
    }
    assert all(count == 89581 for count in report["summary"]["blocked_rows_by_item"].values())


def test_source_resolution_plan_agent_model_stage_has_invariants() -> None:
    report = build_source_resolution_plan()
    stage = report["agent_model_stage"]

    assert stage["stage_id"] == "source_resolution"
    assert stage["automatic_until"] == "row_level_extraction_specs"
    assert "source_gap_is_not_success" in stage["invariants"]
    assert "row_level_pending_evidence_is_not_a_score" in stage["invariants"]
    assert "formal_gf0017_scoring_authorization" in stage["human_decision_required_for"]


def test_source_resolution_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_source_resolution_plan())

    assert "# Full Catalog Source Resolution Plan" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Formal scoring" in markdown
