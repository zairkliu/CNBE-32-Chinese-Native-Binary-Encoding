"""Tests for Agent review of the bounded structure/decomposition packet."""

from __future__ import annotations

from pathlib import Path

from scripts.run_structure_decomposition_agent_review_packet import (
    AGENT_REVIEWED_EDITABLE,
    ORIGINAL_EDITABLE,
    render_markdown,
    run_agent_review,
)


def test_structure_decomposition_agent_review_completes_without_full_duplication() -> None:
    report = run_agent_review()

    assert report["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_AGENT_REVIEW_COMPLETED_NO_SCORING"
    assert report["summary"]["reviewed_rows"] == 212
    assert report["summary"]["source_total_rows"] == 97686
    assert report["checks"]["uses_bounded_packet_only"] is True
    assert report["checks"]["does_not_read_or_duplicate_full_97686_table"] is True
    assert report["summary"]["full_table_duplicate_allowed"] is False


def test_structure_decomposition_agent_review_writes_only_separate_copy() -> None:
    report = run_agent_review()

    assert report["checks"]["agent_reviewed_copy_is_separate"] is True
    assert Path(report["outputs"]["agent_reviewed_editable_csv"]) == AGENT_REVIEWED_EDITABLE
    assert AGENT_REVIEWED_EDITABLE != ORIGINAL_EDITABLE
    assert report["decision"]["may_modify_agent_reviewed_editable_copy"] is True
    assert report["decision"]["may_modify_source_report"] is False


def test_structure_decomposition_agent_review_does_not_score_or_label() -> None:
    report = run_agent_review()

    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["final_structure_labels_written"] == 0
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    for row in report["reviewed_rows"]:
        assert row["human_structure_label"] == ""
        assert row["human_decomposition"] == ""
        assert "No GF0017 points" in row["human_review_notes"]
        assert row["editable_copy_notice"] == "AGENT_REVIEWED_EDITABLE_COPY_NOT_SOURCE_EVIDENCE"


def test_structure_decomposition_agent_review_markdown_states_boundary() -> None:
    markdown = render_markdown(run_agent_review())

    assert "# Structure/Decomposition Agent Review Result" in markdown
    assert "bounded packet only" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "Final structure labels written: 0" in markdown
