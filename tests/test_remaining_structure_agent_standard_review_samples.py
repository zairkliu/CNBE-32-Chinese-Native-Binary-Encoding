"""Tests for deterministic Agent-standard review sample planning."""

from __future__ import annotations

from scripts.plan_remaining_structure_agent_standard_review_samples import (
    EXPECTED_TOTAL_SAMPLES,
    SAMPLE_QUOTAS,
    build_review_sample_plan,
    render_markdown,
)


def test_review_sample_plan_is_ready() -> None:
    report = build_review_sample_plan()

    assert report["overall_status"] == "PASS_AGENT_STANDARD_REVIEW_SAMPLE_PLAN_READY"
    assert report["summary"]["feature_rows"] == 73831
    assert report["summary"]["sample_rows"] == EXPECTED_TOTAL_SAMPLES


def test_review_sample_plan_uses_expected_prior_quotas() -> None:
    report = build_review_sample_plan()

    assert report["sampling_method"]["method"] == "deterministic_even_spread_by_review_prior"
    assert report["sampling_method"]["random_seed"] is None
    assert report["summary"]["sample_prior_counts"] == SAMPLE_QUOTAS


def test_review_sample_plan_keeps_no_write_boundaries() -> None:
    report = build_review_sample_plan()

    assert all(report["checks"].values())
    assert report["summary"]["duplicate_sample_key_count"] == 0
    assert report["summary"]["forbidden_field_leak_count"] == 0
    assert report["summary"]["point_assignment_leak_count"] == 0
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0


def test_review_sample_plan_blocks_formal_scoring_and_writes() -> None:
    report = build_review_sample_plan()

    assert report["decision"]["may_start_human_review_packet"] is True
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_modify_source_assets"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_review_sample_markdown_states_scope() -> None:
    markdown = render_markdown(build_review_sample_plan())

    assert "# Remaining Structure Agent-Standard Review Samples" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "Sample Prior Counts" in markdown
