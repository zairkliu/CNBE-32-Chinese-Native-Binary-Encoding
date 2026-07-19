"""Tests for bounded structure/decomposition review packets."""

from __future__ import annotations

from scripts.audit_structure_decomposition_evidence_repair_from_index import audit_repair_report
from scripts.build_structure_decomposition_review_packet_from_index import (
    build_review_packet,
    render_markdown,
)


def test_structure_decomposition_agent_audit_passes() -> None:
    report = audit_repair_report()

    assert report["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_AGENT_AUDIT_READY_FOR_REVIEW_PACKET"
    assert report["summary"]["total_rows"] == 97686
    assert report["summary"]["may_generate_review_packet"] is True
    assert report["summary"]["may_duplicate_full_97686_table"] is False
    assert report["summary"]["may_generate_database"] is False


def test_structure_decomposition_review_packet_is_bounded() -> None:
    packet = build_review_packet()

    assert packet["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_REVIEW_PACKET_READY"
    assert packet["summary"]["source_total_rows"] == 97686
    assert packet["summary"]["packet_rows"] < 97686
    assert packet["summary"]["packet_rows"] <= 240
    assert packet["checks"]["does_not_duplicate_97686_rows"] is True
    assert packet["checks"]["does_not_generate_xlsx"] is True
    assert packet["checks"]["does_not_generate_database"] is True


def test_structure_decomposition_review_packet_has_editable_copy_only_rule() -> None:
    packet = build_review_packet()

    assert packet["decision"]["may_modify_editable_copy_only"] is True
    assert packet["decision"]["may_modify_source_report"] is False
    assert packet["decision"]["may_assign_gf0017_points"] is False
    assert packet["decision"]["may_emit_final_structure_labels"] is False
    assert "EDITABLE" in packet["outputs"]["editable_copy_csv"]
    for row in packet["packet_rows"]:
        assert row["editable_copy_notice"] == "EDITABLE_COPY_ONLY_DO_NOT_TREAT_AS_SOURCE_EVIDENCE"
        assert row["human_structure_label"] == ""
        assert row["human_decomposition"] == ""


def test_structure_decomposition_review_packet_markdown_states_no_duplication() -> None:
    markdown = render_markdown(build_review_packet())

    assert "# Structure/Decomposition Review Packet" in markdown
    assert "does not duplicate the full" in markdown
    assert "Editable copy" in markdown
    assert "Database generation allowed: `False`" in markdown
