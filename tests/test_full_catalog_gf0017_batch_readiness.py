"""Tests for full-catalog GF0017 batch readiness assessment."""

from __future__ import annotations

from scripts.evaluate_full_catalog_gf0017_batch_readiness import build_batch_readiness, render_markdown


def test_batch_readiness_allows_source_join_but_not_formal_scoring() -> None:
    report = build_batch_readiness()

    assert report["overall_status"] == "PASS_READY_FOR_SOURCE_JOIN_BATCH"
    assert report["decision"]["may_start_source_join_batch"] is True
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_batch_readiness_splits_full_catalog_by_8105_scope() -> None:
    report = build_batch_readiness()
    counts = report["summary"]["status_counts"]

    assert report["summary"]["total_rows"] == 97686
    assert counts["READY_8105_DIRECT_BASELINE_ASSESSMENT"] == 8105
    assert counts["AGENT_STANDARD_MAPPING_REQUIRED"] == 89581
    assert "BLOCKER_UNICODE_IDENTITY" not in counts


def test_batch_readiness_preserves_source_gap_items() -> None:
    report = build_batch_readiness()

    assert report["summary"]["source_gap_items"] == ["character_set_coverage", "stroke_shape"]
    assert len(report["summary"]["source_evidence_required_items"]) == 6
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False


def test_batch_readiness_markdown_states_boundary() -> None:
    markdown = render_markdown(build_batch_readiness())

    assert "# Full Catalog GF0017 Batch Readiness" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Formal scoring" in markdown
