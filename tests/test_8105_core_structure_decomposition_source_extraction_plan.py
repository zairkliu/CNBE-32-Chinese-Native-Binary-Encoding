"""Tests for the 8105 core structure/decomposition extraction plan."""

from __future__ import annotations

from scripts.plan_8105_core_structure_decomposition_source_extraction import build_plan, render_markdown


def test_8105_core_structure_decomposition_source_extraction_plan_passes() -> None:
    report = build_plan()

    assert report["overall_status"] == "PASS_8105_CORE_STRUCTURE_DECOMPOSITION_SOURCE_EXTRACTION_PLAN_READY"
    assert report["summary"]["input_rows"] == 100
    assert report["summary"]["handoff_rows"] == 100
    assert report["checks"]["all_standard_sources_available"] is True


def test_8105_core_structure_decomposition_source_extraction_uses_standardizer_contract() -> None:
    report = build_plan()
    handoff = report["skill_handoff"]

    assert handoff["skill"] == "cnbe-hanzi-decomposition-standardizer"
    assert handoff["task_type"] == "batch"
    assert handoff["mode"] == "evidence_only_no_score"
    assert "gf0017_points" in handoff["forbidden_outputs"]
    assert "database" in handoff["forbidden_outputs"]


def test_8105_core_structure_decomposition_source_extraction_keeps_rows_pending() -> None:
    report = build_plan()

    assert report["summary"]["structure_source_required_rows"] == 100
    assert report["summary"]["decomposition_source_required_rows"] == 100
    assert report["summary"]["component_name_source_required_rows"] == 100
    for row in report["handoff_rows"]:
        assert row["unicode_identity_status"] == "PASS_UNICODE_IDENTITY"
        assert row["structure_join_status"] == "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        assert row["decomposition_join_status"] == "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        assert row["gf0017_points_assigned"] == 0
        assert row["cnbe_write_status"] == "NO_CNBE_WRITE"
        assert row["database_rebuild_status"] == "NO_DATABASE_REBUILD"


def test_8105_core_structure_decomposition_source_extraction_blocks_scoring_and_writes() -> None:
    report = build_plan()

    assert report["decision"]["may_run_bounded_standardizer_extraction"] is True
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["decision"]["may_modify_cnbe_research_knowledge"] is False


def test_8105_core_structure_decomposition_source_extraction_markdown_records_boundaries() -> None:
    markdown = render_markdown(build_plan())

    assert "# 8105 Core Structure Decomposition Source Extraction Plan" in markdown
    assert "cnbe-hanzi-decomposition-standardizer" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "CNBE rows written: 0" in markdown
