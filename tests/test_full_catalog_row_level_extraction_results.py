"""Tests for full-catalog row-level extraction results."""

from __future__ import annotations

from scripts.run_full_catalog_row_level_extraction_specs import build_extraction_results, render_markdown


def test_extraction_results_materialize_all_rows_and_specs() -> None:
    report = build_extraction_results()

    assert report["overall_status"] == "PASS_ROW_LEVEL_EXTRACTION_STATUS_MATERIALIZED"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["spec_count"] == 7
    assert len(report["row_records"]) == 89581


def test_extraction_results_preserve_no_score_and_no_write_boundaries() -> None:
    report = build_extraction_results()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_extraction_results_have_all_sources_available_but_pending() -> None:
    report = build_extraction_results()

    assert report["summary"]["missing_source_paths"] == []
    assert report["summary"]["row_status_counts"] == {
        "ROW_EXTRACTION_SOURCES_AVAILABLE_PENDING": 89581
    }
    for counts in report["summary"]["item_status_counts"].values():
        assert counts == {"SOURCE_PATHS_AVAILABLE_EXTRACTION_PENDING": 89581}


def test_extraction_results_output_table_counts_match_items() -> None:
    report = build_extraction_results()

    assert report["summary"]["output_table_counts"] == {
        "component_evidence": 179162,
        "radical_evidence": 89581,
        "stroke_evidence": 179162,
        "structure_evidence": 179162,
    }


def test_extraction_results_markdown_states_review_next() -> None:
    markdown = render_markdown(build_extraction_results())

    assert "# Full Catalog Row-Level Extraction Results" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "evidence-review plan" in markdown
