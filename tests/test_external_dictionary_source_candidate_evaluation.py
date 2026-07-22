"""Tests for external dictionary source candidate evaluation."""

from __future__ import annotations

import pytest

from scripts.evaluate_external_dictionary_source_candidates import (
    NLP_KANGXI_DB,
    NLP_ZHDZD_DB,
    build_evaluation,
    render_markdown,
)


def require_external_dictionary_assets() -> None:
    missing = [path for path in (NLP_KANGXI_DB, NLP_ZHDZD_DB) if not path.exists()]
    if missing:
        pytest.skip(
            "external dictionary candidate databases are local integration assets: "
            + ", ".join(str(path) for path in missing)
        )


def test_external_dictionary_evaluation_is_ready() -> None:
    require_external_dictionary_assets()
    report = build_evaluation()

    assert report["overall_status"] == "PASS_EXTERNAL_DICTIONARY_SOURCE_EVALUATION_READY"
    assert report["summary"]["human_review_packet_rows"] == 150
    assert report["summary"]["remaining_agent_standard_rows"] == 73831


def test_external_dictionary_evaluation_recommends_structured_primary_source() -> None:
    require_external_dictionary_assets()
    report = build_evaluation()

    assert report["summary"]["recommended_primary_source"] == "leechenhwa2/nlp-han-dicts"
    nlp = report["candidates"]["leechenhwa2_nlp_han_dicts"]
    assert nlp["license"] == "BSD-2-Clause"
    assert nlp["kangxi_db"]["dict_count"] > 40000
    assert nlp["zhonghua_dazidian_db"]["dict_count"] > 19000


def test_external_dictionary_evaluation_keeps_authority_boundaries() -> None:
    require_external_dictionary_assets()
    report = build_evaluation()

    assert all(report["checks"].values())
    assert report["authority_boundary"]["dictionary_sources_are_cross_reference_context"] is True
    assert report["authority_boundary"]["not_national_standard_structure_authority"] is True
    assert report["decision"]["may_modify_cnbe_research_knowledge"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False


def test_external_dictionary_evaluation_marks_secondary_sources() -> None:
    require_external_dictionary_assets()
    report = build_evaluation()

    he = report["candidates"]["he426100_kangxi"]
    kr = report["candidates"]["kanripo_KR1j0048"]
    assert he["recommended_role"].startswith("secondary_comparison")
    assert kr["recommended_role"].startswith("primary_text_witness")


def test_external_dictionary_evaluation_markdown_states_scope() -> None:
    require_external_dictionary_assets()
    markdown = render_markdown(build_evaluation())

    assert "# External Dictionary Source Candidate Evaluation" in markdown
    assert "does not write `cnbe-research/knowledge`" in markdown
    assert "leechenhwa2/nlp-han-dicts" in markdown
