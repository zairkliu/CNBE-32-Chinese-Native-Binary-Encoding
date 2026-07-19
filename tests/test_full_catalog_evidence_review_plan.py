"""Tests for the full-catalog evidence-review plan."""

from __future__ import annotations

from scripts.plan_full_catalog_evidence_review import build_evidence_review_plan, render_markdown


def test_evidence_review_plan_is_ready_without_scoring() -> None:
    report = build_evidence_review_plan()

    assert report["overall_status"] == "PASS_EVIDENCE_REVIEW_PLAN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["review_items"] == 7
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False


def test_evidence_review_prioritizes_highest_value_items() -> None:
    report = build_evidence_review_plan()
    ordered = [item["gf0017_item"] for item in report["review_items"]]

    assert ordered[:3] == [
        "structure_first_decomposition",
        "component_name_validity",
        "independent_character_rule",
    ]
    assert report["summary"]["highest_priority_item"] == "structure_first_decomposition"


def test_evidence_review_keeps_policy_item_outside_automation() -> None:
    report = build_evidence_review_plan()
    policy_package = next(pkg for pkg in report["work_packages"] if pkg["id"] == "ERP4_policy_review")

    assert report["summary"]["policy_decision_items"] == ["character_set_coverage"]
    assert policy_package["automation_allowed"] is False
    assert policy_package["items"] == ["character_set_coverage"]


def test_evidence_review_preserves_no_write_boundaries() -> None:
    report = build_evidence_review_plan()

    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_evidence_review_markdown_states_next_parser_plan() -> None:
    markdown = render_markdown(build_evidence_review_plan())

    assert "# Full Catalog Evidence Review Plan" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "parser implementation" in markdown
