"""Tests for dictionary review packets over structure/decomposition gaps."""

from __future__ import annotations

from scripts.run_structure_decomposition_dictionary_gap_extractor import (
    build_dictionary_gap_report,
    render_markdown,
)


def test_dictionary_gap_extractor_covers_source_gap_rows() -> None:
    report = build_dictionary_gap_report()

    assert report["overall_status"] == "PASS_DICTIONARY_GAP_REVIEW_PACKET_READY"
    assert report["summary"]["source_gap_rows"] == 85001
    assert len(report["row_records"]) == 85001


def test_dictionary_gap_extractor_records_small_review_hit_subset() -> None:
    report = build_dictionary_gap_report()
    counts = report["summary"]["review_status_counts"]

    assert sum(counts.values()) == 85001
    assert counts["NO_DICTIONARY_REVIEW_HIT"] > 80000
    assert report["summary"]["source_hit_counts"]["yuanliu"] == 32
    assert report["summary"]["source_hit_counts"]["cihai"] == 32


def test_dictionary_gap_extractor_keeps_scoring_and_writes_blocked() -> None:
    report = build_dictionary_gap_report()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_source_assets"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_dictionary_gap_extractor_records_cross_reference_grade() -> None:
    report = build_dictionary_gap_report()
    hit = report["samples"]["review_hits"][0]

    assert hit["source_grade"] == "cross_reference"
    assert hit["score"] is None
    assert hit["can_assign_points"] is False


def test_dictionary_gap_markdown_states_no_scoring() -> None:
    markdown = render_markdown(build_dictionary_gap_report())

    assert "# Structure/Decomposition Dictionary Gap Extractor" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "汉字源流" in markdown
