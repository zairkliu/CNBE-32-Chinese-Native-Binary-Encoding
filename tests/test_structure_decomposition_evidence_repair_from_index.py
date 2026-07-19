"""Tests for structure/decomposition evidence repair from the unified index."""

from __future__ import annotations

from scripts.repair_structure_decomposition_evidence_from_index import build_repair_report, render_markdown


def test_structure_decomposition_evidence_repair_materializes_all_rows() -> None:
    report = build_repair_report()

    assert report["overall_status"] == "PASS_STRUCTURE_DECOMPOSITION_EVIDENCE_REPAIR_MATERIALIZED"
    assert report["summary"]["total_rows"] == 97686
    assert len(report["row_records"]) == 97686
    assert report["summary"]["core_8105_standard_join_required_rows"] == 8105
    assert report["summary"]["reviewable_or_partial_rows"] == 4580


def test_structure_decomposition_evidence_repair_keeps_scoring_blocked() -> None:
    report = build_repair_report()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_structure_decomposition_evidence_repair_classifies_samples() -> None:
    report = build_repair_report()

    assert report["samples"]["U+4E00"]["structure_evidence_status"] == (
        "CORE_8105_STRUCTURE_STANDARD_JOIN_REQUIRED"
    )
    assert report["samples"]["U+3400"]["structure_evidence_status"] == (
        "STRUCTURE_DECOMPOSITION_SOURCE_GAP_WITH_REVIEW_CONTEXT"
    )
    assert report["samples"]["U+323AF"]["structure_evidence_status"] in {
        "STRUCTURE_DECOMPOSITION_AGENT_STANDARD_QUEUE_ONLY",
        "STRUCTURE_DECOMPOSITION_SOURCE_GAP_NO_CONTEXT",
    }
    for sample in report["samples"].values():
        assert sample["score"] is None
        assert sample["final_structure_label"] is None
        assert sample["can_assign_points"] is False


def test_structure_decomposition_evidence_repair_markdown_states_boundary() -> None:
    markdown = render_markdown(build_repair_report())

    assert "# GF0017 Structure/Decomposition Evidence Repair From Existing Index" in markdown
    assert "does not regenerate Unicode identity" in markdown
    assert "Scoring and encoding writes remain blocked" in markdown
