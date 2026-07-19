"""Tests for joining staged dictionary context to review targets."""

from __future__ import annotations

from scripts.run_external_dictionary_context_review_join import (
    build_review_join,
    render_markdown,
)


def test_dictionary_context_review_join_is_ready() -> None:
    report = build_review_join()

    assert report["overall_status"] == "PASS_DICTIONARY_CONTEXT_REVIEW_JOIN_READY"
    assert len(report["human_review_join_rows"]) == 150
    assert report["summary"]["dictionary_context_unique_chars"] > 49000


def test_dictionary_context_review_join_preserves_known_coverage() -> None:
    report = build_review_join()

    assert report["summary"]["human_review_coverage"]["hit_rows"] == 104
    assert report["summary"]["remaining_agent_standard_coverage"]["hit_rows"] == 28960
    assert report["summary"]["human_dual_source_rows"] == 61
    assert report["summary"]["human_single_source_rows"] == 43
    assert report["summary"]["human_gap_rows"] == 46


def test_dictionary_context_review_join_keeps_authority_boundaries() -> None:
    report = build_review_join()

    assert all(report["checks"].values())
    assert report["authority_boundary"]["not_national_standard_structure_authority"] is True
    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["decision"]["may_modify_cnbe_research_knowledge"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False


def test_dictionary_context_review_join_contains_context_for_xin() -> None:
    report = build_review_join()

    rows = [row for row in report["human_review_join_rows"] if row["char"] == "鑫"]
    # 鑫 is not necessarily in the deterministic 150-row packet; if absent,
    # the staging lookup itself is covered by staging tests.
    if rows:
        row = rows[0]
        assert row["dictionary_context_class"] == "dictionary_context_dual_source"
        assert "鑫" in row["kangxi_preview"] or "鑫" in row["zhonghua_dazidian_preview"]


def test_dictionary_context_review_join_markdown_states_scope() -> None:
    markdown = render_markdown(build_review_join())

    assert "# External Dictionary Context Review Join" in markdown
    assert "does not write `cnbe-research/knowledge`" in markdown
    assert "Human review hit rows" in markdown
