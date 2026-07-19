"""Tests for the full-catalog Agent-standard mapping plan."""

from __future__ import annotations

from scripts.plan_full_catalog_agent_standard_mapping import build_mapping_plan, render_markdown


def test_mapping_plan_covers_all_outside_8105_rows() -> None:
    report = build_mapping_plan()

    assert report["overall_status"] == "PASS_AGENT_STANDARD_MAPPING_PLAN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["unicode_identity_gap_count"] == 0
    assert report["summary"]["agent_standard_mapping_design_allowed"] is True


def test_mapping_plan_preserves_scoring_and_database_blocks() -> None:
    report = build_mapping_plan()

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_mapping_plan_stratifies_unicode_planes_and_blocks() -> None:
    report = build_mapping_plan()
    plane_counts = report["strata"]["plane_counts"]
    block_counts = report["strata"]["unicode_block_counts"]

    assert plane_counts["BMP"] == 19675
    assert plane_counts["SUPPLEMENTARY"] == 69906
    assert block_counts["CJK Unified Ideographs Extension B"] == 42684
    assert sum(block_counts.values()) == 89581


def test_mapping_plan_keeps_all_gf0017_items_blocked() -> None:
    report = build_mapping_plan()
    gate_statuses = {
        item["item"]: item["current_source_status"]
        for item in report["gf0017_gate_plan"]
    }

    assert gate_statuses["character_set_coverage"] == "SOURCE_GAP"
    assert gate_statuses["stroke_shape"] == "SOURCE_GAP"
    assert gate_statuses["stroke_order"] == "SOURCE_EVIDENCE_REQUIRED"
    assert len(report["summary"]["blocked_gf0017_items"]) == 8


def test_mapping_plan_markdown_states_no_write_boundary() -> None:
    markdown = render_markdown(build_mapping_plan())

    assert "# Full Catalog Agent-Standard Mapping Plan" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "CNBE row writes" in markdown
