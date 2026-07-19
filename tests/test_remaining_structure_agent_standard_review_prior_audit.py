"""Tests for Agent-standard review-prior auditing."""

from __future__ import annotations

from scripts.audit_remaining_structure_agent_standard_review_priors import (
    build_review_prior_audit,
    render_markdown,
)


def test_review_prior_audit_is_ready() -> None:
    report = build_review_prior_audit()

    assert report["overall_status"] == "PASS_AGENT_STANDARD_REVIEW_PRIOR_AUDIT_READY"
    assert report["summary"]["feature_rows"] == 73831
    assert report["summary"]["prior_mismatch_count"] == 0


def test_review_prior_audit_counts_expected_buckets() -> None:
    report = build_review_prior_audit()

    assert report["summary"]["review_queue_counts"] == {
        "agent_standard_extension_review_candidate": 67946,
        "agent_standard_rule_learning_candidate": 5885,
    }
    assert report["summary"]["review_prior_counts"] == {
        "review_prior_low": 67946,
        "review_prior_low_medium": 4805,
        "review_prior_medium": 1080,
    }


def test_review_prior_audit_checks_all_boundaries() -> None:
    report = build_review_prior_audit()

    assert all(report["checks"].values())
    assert report["summary"]["forbidden_field_row_count"] == 0
    assert report["summary"]["point_assignment_row_count"] == 0
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0


def test_review_prior_audit_keeps_scoring_and_writes_blocked() -> None:
    report = build_review_prior_audit()

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False


def test_review_prior_audit_markdown_states_no_scores() -> None:
    markdown = render_markdown(build_review_prior_audit())

    assert "# Remaining Structure Agent-Standard Review-Prior Audit" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "Final structure labels emitted" in markdown
