"""Tests for applying ZDIC references to the Agent-reviewed packet copy."""

from __future__ import annotations

from scripts.apply_zdic_references_to_agent_review_packet import build_enhancement, render_markdown


def test_zdic_agent_review_enhancement_passes() -> None:
    report = build_enhancement()

    assert report["overall_status"] == "PASS_AGENT_REVIEW_ZDIC_REFERENCES_APPLIED"
    assert report["summary"]["enhanced_rows"] == 212
    assert report["summary"]["snapshot_references_available"] >= 4
    assert report["checks"]["all_rows_have_zdic_url"] is True


def test_zdic_agent_review_enhancement_keeps_boundary() -> None:
    report = build_enhancement()

    assert report["authority_boundary"]["zdic_cross_reference_only"] is True
    assert report["authority_boundary"]["does_not_promote_zdic_to_national_standard"] is True
    assert report["decision"]["may_promote_zdic_to_national_standard"] is False
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0


def test_zdic_agent_review_enhancement_rows_remain_review_notes_only() -> None:
    report = build_enhancement()

    for row in report["enhanced_rows"]:
        assert ";zdic:https://www.zdic.net/hans/" in row["human_source_reference"]
        assert row["human_structure_label"] == ""
        assert row["human_decomposition"] == ""
        assert row["editable_copy_notice"] == "AGENT_REVIEWED_ZDIC_EDITABLE_COPY_NOT_SOURCE_EVIDENCE"


def test_zdic_agent_review_enhancement_markdown_states_boundary() -> None:
    markdown = render_markdown(build_enhancement())

    assert "# Structure/Decomposition Agent Review ZDIC Enhancement" in markdown
    assert "online cross-reference context only" in markdown
    assert "GF0017 points assigned: 0" in markdown
