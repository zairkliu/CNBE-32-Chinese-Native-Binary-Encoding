"""Tests for validating the ZDIC-enhanced Agent review packet."""

from __future__ import annotations

from scripts.validate_zdic_enhanced_agent_review_packet import render_markdown, validate_packet


def test_zdic_enhanced_agent_review_packet_validation_passes() -> None:
    report = validate_packet()

    assert report["overall_status"] == "PASS_ZDIC_ENHANCED_AGENT_REVIEW_PACKET_VALIDATED"
    assert report["summary"]["enhanced_packet_rows"] == 212
    assert report["summary"]["snapshot_records"] >= 5
    assert report["summary"]["snapshot_files_verified"] >= 5
    assert report["decision"]["may_use_zdic_enhanced_packet_for_human_review"] is True


def test_zdic_enhanced_agent_review_packet_validation_keeps_boundaries() -> None:
    report = validate_packet()

    assert report["checks"]["does_not_duplicate_full_97686_table"] is True
    assert report["checks"]["zdic_remains_cross_reference_only"] is True
    assert report["checks"]["does_not_assign_gf0017_points"] is True
    assert report["checks"]["does_not_emit_final_structure_labels"] is True
    assert report["checks"]["does_not_create_database_or_xlsx"] is True
    assert report["decision"]["may_promote_zdic_to_national_standard"] is False
    assert report["decision"]["may_assign_gf0017_points"] is False


def test_zdic_enhanced_agent_review_packet_rows_are_review_only() -> None:
    report = validate_packet()

    assert report["checks"]["all_rows_have_zdic_url"] is True
    assert report["checks"]["all_rows_keep_blank_structure_label"] is True
    assert report["checks"]["all_rows_keep_blank_decomposition"] is True
    assert report["checks"]["all_rows_marked_editable_not_source_evidence"] is True


def test_zdic_enhanced_agent_review_packet_markdown_states_boundary() -> None:
    markdown = render_markdown(validate_packet())

    assert "# ZDIC Enhanced Agent Review Packet Validation" in markdown
    assert "online cross-reference and reviewer navigation layer" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "XLSX generation allowed: `False`" in markdown
