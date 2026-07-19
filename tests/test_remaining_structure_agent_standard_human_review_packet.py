"""Tests for Agent-standard human-review packet generation."""

from __future__ import annotations

from scripts.build_remaining_structure_agent_standard_human_review_packet import (
    ALLOWED_STRUCTURE_LABELS,
    EXPECTED_SAMPLE_ROWS,
    REVIEW_STATUS_VALUES,
    build_human_review_packet,
    render_markdown,
)


def test_human_review_packet_is_ready() -> None:
    report = build_human_review_packet()

    assert report["overall_status"] == "PASS_HUMAN_REVIEW_PACKET_READY"
    assert report["summary"]["packet_rows"] == EXPECTED_SAMPLE_ROWS
    assert report["decision"]["may_start_human_review"] is True


def test_human_review_packet_preserves_sample_distribution() -> None:
    report = build_human_review_packet()

    assert report["summary"]["review_prior_counts"] == {
        "review_prior_low": 50,
        "review_prior_low_medium": 50,
        "review_prior_medium": 50,
    }
    assert report["summary"]["review_queue_counts"] == {
        "agent_standard_extension_review_candidate": 50,
        "agent_standard_rule_learning_candidate": 100,
    }


def test_human_review_packet_keeps_authority_boundaries() -> None:
    report = build_human_review_packet()

    assert all(report["checks"].values())
    assert report["summary"]["forbidden_field_row_count"] == 0
    assert report["summary"]["human_label_prefill_count"] == 0
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_human_review_packet_declares_allowed_values() -> None:
    report = build_human_review_packet()

    assert report["review_instructions"]["review_status_values"] == REVIEW_STATUS_VALUES
    assert report["review_instructions"]["allowed_structure_labels"] == ALLOWED_STRUCTURE_LABELS
    assert len(ALLOWED_STRUCTURE_LABELS) == 13


def test_human_review_packet_markdown_states_scope() -> None:
    markdown = render_markdown(build_human_review_packet())

    assert "# Remaining Structure Agent-Standard Human Review Packet" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "Review Prior Counts" in markdown
