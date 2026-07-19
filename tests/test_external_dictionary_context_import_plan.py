"""Tests for external dictionary context import planning."""

from __future__ import annotations

from scripts.plan_external_dictionary_context_import import (
    build_import_plan,
    render_markdown,
)


def test_dictionary_context_import_plan_is_ready() -> None:
    report = build_import_plan()

    assert report["overall_status"] == "PASS_DICTIONARY_CONTEXT_IMPORT_PLAN_READY"
    assert report["next_step"]["allowed"] is True
    assert report["summary"]["recommended_primary_source"] == "leechenhwa2/nlp-han-dicts"


def test_dictionary_context_import_plan_declares_staging_schema() -> None:
    report = build_import_plan()

    fields = {field["name"] for field in report["staging_schema"]["fields"]}
    assert {"source_id", "char", "unicode", "content", "source_grade", "license"} <= fields
    assert report["staging_schema"]["primary_key"] == ["source_id", "char"]


def test_dictionary_context_import_plan_keeps_writes_blocked() -> None:
    report = build_import_plan()

    assert all(report["checks"].values())
    assert report["authority_boundary"]["does_not_modify_cnbe_research_knowledge"] is True
    assert report["authority_boundary"]["does_not_assign_gf0017_scores"] is True
    assert report["summary"]["knowledge_write_allowed"] is False
    assert report["next_step"]["requires_authorization_before_cnbe_research_knowledge_write"] is True


def test_dictionary_context_import_plan_prioritizes_sources() -> None:
    report = build_import_plan()

    source_ids = [source["source_id"] for source in report["source_priority"]]
    assert source_ids[0] == "nlp_han_dicts_kangxi_4w"
    assert source_ids[1] == "nlp_han_dicts_zhonghua_dazidian"
    assert source_ids[-1] == "he426100_kangxi_secondary"


def test_dictionary_context_import_plan_markdown_states_scope() -> None:
    markdown = render_markdown(build_import_plan())

    assert "# External Dictionary Context Import Plan" in markdown
    assert "does not write `cnbe-research/knowledge`" in markdown
    assert "leechenhwa2/nlp-han-dicts" in markdown
