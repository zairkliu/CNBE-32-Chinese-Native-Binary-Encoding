"""Tests for remaining structure Agent-standard rule-learning design."""

from __future__ import annotations

from scripts.design_remaining_structure_agent_standard_rule_learning import (
    build_rule_learning_design,
    render_markdown,
)


def test_rule_learning_design_is_ready() -> None:
    report = build_rule_learning_design()

    assert report["overall_status"] == "PASS_AGENT_STANDARD_RULE_LEARNING_DESIGN_READY"
    assert report["summary"]["rule_learning_candidates"] == 5885
    assert report["summary"]["extension_review_candidates"] == 67946
    assert report["summary"]["standard_level"] == "agent_standard_candidate_not_national_standard"


def test_rule_learning_design_uses_8105_reference_without_scoring() -> None:
    report = build_rule_learning_design()

    assert report["summary"]["baseline_8105_rows"] == 8105
    assert report["summary"]["baseline_structure_distribution"]
    assert report["summary"]["gf0017_8105_status_distribution"]
    for feature in report["learning_features"]:
        assert feature["can_assign_points"] is False


def test_rule_learning_design_blocks_final_outputs_and_writes() -> None:
    report = build_rule_learning_design()

    assert report["review_policy"]["may_emit_final_structure_label"] is False
    assert report["review_policy"]["may_assign_gf0017_score"] is False
    assert report["review_policy"]["may_write_cnbe32_fields"] is False
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False


def test_rule_learning_design_phases_are_read_only() -> None:
    report = build_rule_learning_design()

    assert len(report["design_phases"]) == 4
    for phase in report["design_phases"]:
        assert phase["assigns_points"] is False
        assert phase["writes_cnbe_rows"] is False


def test_rule_learning_markdown_states_no_final_structure() -> None:
    markdown = render_markdown(build_rule_learning_design())

    assert "# Remaining Structure Agent-Standard Rule-Learning Design" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "emit final structure labels" in markdown
