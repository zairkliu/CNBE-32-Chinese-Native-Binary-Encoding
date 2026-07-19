"""Tests for remaining structure Agent-standard planning."""

from __future__ import annotations

from scripts.plan_remaining_structure_agent_standard import build_agent_standard_plan, render_markdown


def test_remaining_agent_standard_plan_is_ready() -> None:
    report = build_agent_standard_plan()

    assert report["overall_status"] == "PASS_REMAINING_STRUCTURE_AGENT_STANDARD_PLAN_READY"
    assert report["summary"]["remaining_rows"] == 73831
    assert report["summary"]["standard_level"] == "agent_standard_candidate_not_national_standard"


def test_remaining_agent_standard_plan_has_expected_queues() -> None:
    report = build_agent_standard_plan()
    queues = {queue["queue"]: queue for queue in report["queues"]}

    assert "agent_standard_rule_learning_candidate" in queues
    assert "agent_standard_extension_review_candidate" in queues
    assert sum(queue["row_count"] for queue in queues.values()) == 73831
    for queue in queues.values():
        assert queue["can_assign_points"] is False


def test_remaining_agent_standard_plan_keeps_claims_and_writes_blocked() -> None:
    report = build_agent_standard_plan()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert "national_standard" in report["agent_standard_policy"]["forbidden_claims"]
    assert "formal_gf0017_score" in report["agent_standard_policy"]["forbidden_claims"]


def test_remaining_agent_standard_markdown_states_not_national_standard() -> None:
    markdown = render_markdown(build_agent_standard_plan())

    assert "# Remaining Structure Agent-Standard Plan" in markdown
    assert "agent_standard_candidate_not_national_standard" in markdown
    assert "no national-standard claim" in markdown
