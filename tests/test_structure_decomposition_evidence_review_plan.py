"""Tests for Phase 1 structure/decomposition evidence review planning."""

from __future__ import annotations

from scripts.plan_structure_decomposition_evidence_review import build_review_plan, render_markdown


def test_structure_decomposition_review_plan_is_ready() -> None:
    report = build_review_plan()

    assert report["overall_status"] == "PASS_PHASE_1_EVIDENCE_REVIEW_PLAN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["dominant_blocker"] == "MISSING_STRUCTURE"


def test_structure_decomposition_review_plan_counts_all_queues() -> None:
    report = build_review_plan()

    assert report["summary"]["review_queue_counts"] == {
        "human_review_ready": 2551,
        "partial_evidence_review": 2029,
        "source_gap_resolution_required": 85001,
    }


def test_structure_decomposition_review_plan_keeps_scoring_blocked() -> None:
    report = build_review_plan()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_source_assets"] is False


def test_structure_decomposition_review_markdown_states_source_gap_next() -> None:
    markdown = render_markdown(build_review_plan())

    assert "# Structure/Decomposition Evidence Review Plan" in markdown
    assert "It does not" in markdown
    assert "source gap" in markdown
