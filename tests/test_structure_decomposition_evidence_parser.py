"""Tests for the Phase 1 structure/decomposition evidence parser."""

from __future__ import annotations

from scripts.run_structure_decomposition_evidence_parser import (
    ALLOWED_STRUCTURES,
    build_structure_decomposition_report,
    render_markdown,
)


def test_structure_decomposition_parser_covers_outside_8105_rows() -> None:
    report = build_structure_decomposition_report()

    assert report["overall_status"] == "PASS_PHASE_1_STRUCTURE_DECOMPOSITION_EVIDENCE_PARSED"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert len(report["row_records"]) == 89581


def test_structure_decomposition_parser_keeps_scoring_and_writes_blocked() -> None:
    report = build_structure_decomposition_report()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False
    assert report["decision"]["may_modify_source_assets"] is False


def test_structure_decomposition_parser_uses_only_allowed_structure_labels() -> None:
    report = build_structure_decomposition_report()
    labels = set(report["summary"]["structure_label_counts"])

    assert labels <= (ALLOWED_STRUCTURES | {"UNRESOLVED"})


def test_structure_decomposition_parser_has_reviewable_evidence_counts() -> None:
    report = build_structure_decomposition_report()
    counts = report["summary"]["evidence_status_counts"]

    assert sum(counts.values()) == 89581
    assert "STRUCTURE_DECOMPOSITION_EVIDENCE_GAP" in counts
    assert report["summary"]["source_hit_counts"]


def test_structure_decomposition_markdown_states_phase_1_review_next() -> None:
    markdown = render_markdown(build_structure_decomposition_report())

    assert "# Structure/Decomposition Evidence Parser" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Phase 1 evidence review" in markdown
