"""Tests for the full-catalog Agent mapping evidence-status join."""

from __future__ import annotations

from scripts.run_full_catalog_agent_mapping_evidence_join import build_evidence_join, render_markdown


def test_evidence_join_materializes_all_outside_8105_rows() -> None:
    report = build_evidence_join()

    assert report["overall_status"] == "PASS_EVIDENCE_JOIN_STATUS_MATERIALIZED"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert len(report["row_records"]) == 89581
    assert report["summary"]["score_values_assigned"] == 0


def test_evidence_join_preserves_no_write_and_no_score_boundaries() -> None:
    report = build_evidence_join()

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_evidence_join_keeps_expected_row_status_distribution() -> None:
    report = build_evidence_join()

    assert report["summary"]["row_status_counts"] == {
        "ROW_SOURCE_GAP_AND_EVIDENCE_JOIN_PENDING": 89581
    }
    assert report["summary"]["plane_counts"] == {
        "BMP": 19675,
        "SUPPLEMENTARY": 69906,
    }


def test_evidence_join_item_status_counts_are_not_scores() -> None:
    report = build_evidence_join()
    counts = report["summary"]["item_evidence_counts"]

    assert counts["character_set_coverage"] == {"SOURCE_GAP_NOT_SCORABLE": 89581}
    assert counts["stroke_shape"] == {"SOURCE_GAP_NOT_SCORABLE": 89581}
    assert counts["stroke_order"] == {"ROW_LEVEL_EVIDENCE_JOIN_PENDING": 89581}
    assert counts["structure_first_decomposition"] == {
        "ROW_LEVEL_EVIDENCE_JOIN_PENDING": 89581
    }


def test_evidence_join_markdown_states_next_source_resolution_step() -> None:
    markdown = render_markdown(build_evidence_join())

    assert "# Full Catalog Agent Mapping Evidence Join" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "source-resolution plan" in markdown
