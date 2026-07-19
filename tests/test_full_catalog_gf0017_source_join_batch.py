"""Tests for the full-catalog GF0017 source-join batch assessment."""

from __future__ import annotations

from scripts.run_full_catalog_gf0017_source_join_batch import build_source_join_batch, render_markdown


def test_source_join_batch_assesses_all_rows_without_scores() -> None:
    report = build_source_join_batch()

    assert report["overall_status"] == "PASS_SOURCE_JOIN_BATCH_ASSESSED"
    assert report["summary"]["total_rows"] == 97686
    assert report["summary"]["score_values_assigned"] == 0
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_source_join_batch_splits_8105_and_agent_standard_rows() -> None:
    report = build_source_join_batch()
    counts = report["summary"]["status_counts"]

    assert counts["JOINED_8105_STANDARD_DERIVED_KNOWLEDGE"] == 8105
    assert counts["OUTSIDE_8105_AGENT_STANDARD_MAPPING_REQUIRED"] == 89581
    assert report["summary"]["blocker_count"] == 0


def test_source_join_batch_preserves_item_statuses() -> None:
    report = build_source_join_batch()
    item_statuses = report["summary"]["gf0017_source_item_statuses"]

    assert item_statuses["character_set_coverage"] == "SOURCE_GAP"
    assert item_statuses["stroke_shape"] == "SOURCE_GAP"
    assert item_statuses["structure_first_decomposition"] == "SOURCE_EVIDENCE_REQUIRED"


def test_source_join_batch_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_source_join_batch())

    assert "# Full Catalog GF0017 Source-Join Batch" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Formal scoring and database reconstruction" in markdown
