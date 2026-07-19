"""Tests for GF0017 scoring from the existing unified evidence index."""

from __future__ import annotations

from scripts.score_unified_hanzi_gf0017_from_index import build_scoring_report, render_markdown


def test_gf0017_scoring_from_index_uses_existing_index_only() -> None:
    report = build_scoring_report()

    assert report["overall_status"] == "PASS_GF0017_SCORING_FROM_EXISTING_INDEX_WITH_SOURCE_GAPS"
    assert report["summary"]["total_rows_evaluated"] == 97686
    assert report["checks"]["uses_existing_unified_index_only"] is True
    assert report["checks"]["does_not_regenerate_unicode_identity"] is True
    assert report["authority_boundary"]["does_not_regenerate_full_unicode_catalog"] is True


def test_gf0017_scoring_from_index_keeps_writes_blocked() -> None:
    report = build_scoring_report()

    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["decision"]["may_claim_full_gf0017_scores"] is False
    assert report["checks"]["no_cnbe_row_writes"] is True
    assert report["checks"]["no_database_rebuild"] is True
    assert report["checks"]["no_final_structure_labels"] is True


def test_gf0017_scoring_from_index_assigns_only_supported_coverage_points() -> None:
    report = build_scoring_report()

    assert report["summary"]["rows_with_any_assigned_points"] == 8105
    assert report["summary"]["rows_fully_scored"] == 0
    assert report["summary"]["rows_not_scorable_from_current_index"] == 89581
    assert report["item_status_counts"]["character_set_coverage"]["PASS_8105_CORE_COVERAGE"] == 8105
    assert (
        report["item_status_counts"]["structure_first_decomposition"]["NOT_SCORABLE_EVIDENCE_REQUIRED"]
        == 97686
    )


def test_gf0017_scoring_from_index_sample_rows_are_partial_or_blocked() -> None:
    report = build_scoring_report()

    assert report["samples"]["U+4E00"]["score_status"] == "PARTIALLY_SCORED_REMAINING_ITEMS_NOT_SCORABLE"
    assert report["samples"]["U+4E00"]["assigned_score"] == 3
    assert report["samples"]["U+3400"]["score_status"] == "NOT_SCORABLE_FROM_CURRENT_INDEX"
    assert report["samples"]["U+3400"]["assigned_score"] == 0


def test_gf0017_scoring_from_index_markdown_states_boundary() -> None:
    markdown = render_markdown(build_scoring_report())

    assert "# GF0017 Scoring From Existing Unified Index" in markdown
    assert "did not regenerate the full Unicode catalog" in markdown
    assert "CNBE rows were not written" in markdown
