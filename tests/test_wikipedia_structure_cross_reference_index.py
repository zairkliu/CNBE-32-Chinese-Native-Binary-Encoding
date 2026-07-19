"""Tests for the read-only offline-Wikipedia cross-reference index."""

from __future__ import annotations

from scripts.run_wikipedia_structure_cross_reference_index import build_wikipedia_index, render_markdown


def test_wikipedia_cross_reference_index_sample_is_ready() -> None:
    report = build_wikipedia_index(max_articles=25)

    assert report["overall_status"] == "PASS_WIKIPEDIA_CROSS_REFERENCE_INDEX_SAMPLE_READY"
    assert report["summary"]["target_rows"] == 84939
    assert report["summary"]["max_articles"] == 25
    assert report["summary"]["score_values_assigned"] == 0


def test_wikipedia_cross_reference_index_keeps_lowest_tier_no_write_boundary() -> None:
    report = build_wikipedia_index(max_articles=25)

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_source_assets"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_wikipedia_cross_reference_index_records_all_target_rows() -> None:
    report = build_wikipedia_index(max_articles=25)
    counts = report["summary"]["wiki_review_status_counts"]

    assert sum(counts.values()) == 84939
    assert "NO_WIKI_CROSS_REFERENCE_HIT" in counts
    for sample in report["samples"]["no_wiki_cross_reference_hit"][:5]:
        assert "unicode" in sample
        assert "char" in sample


def test_wikipedia_cross_reference_markdown_states_no_scoring() -> None:
    markdown = render_markdown(build_wikipedia_index(max_articles=25))

    assert "# Wikipedia Structure Cross-Reference Index" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "lowest-tier" in markdown
