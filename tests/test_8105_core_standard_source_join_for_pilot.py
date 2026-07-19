"""Tests for the 8105 core standard-source join pilot plan."""

from __future__ import annotations

from scripts.plan_8105_core_standard_source_join_for_pilot import build_plan, render_markdown


def test_8105_core_standard_source_join_plan_passes() -> None:
    report = build_plan()

    assert report["overall_status"] == "PASS_8105_CORE_STANDARD_SOURCE_JOIN_PILOT_PLAN_READY"
    assert report["summary"]["core_pilot_rows"] == 100
    assert report["checks"]["all_core_rows_found_in_base"] is True
    assert report["checks"]["all_core_unicode_values_match"] is True


def test_8105_core_standard_source_join_keeps_scoring_blocked() -> None:
    report = build_plan()

    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["summary"]["cnbe_rows_written"] == 0
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_8105_core_standard_source_join_locks_stroke_fields_only() -> None:
    report = build_plan()

    assert report["summary"]["stroke_join_ready_rows"] == 100
    assert report["summary"]["structure_standard_source_required_rows"] == 100
    assert report["summary"]["decomposition_standard_source_required_rows"] == 100
    for row in report["rows"]:
        assert row["stroke_join_status"] == "STANDARD_DERIVED_STROKE_JOIN_READY"
        assert row["structure_join_status"] == "STRUCTURE_STANDARD_SOURCE_EXTRACTION_REQUIRED"
        assert row["decomposition_join_status"] == "DECOMPOSITION_STANDARD_SOURCE_EXTRACTION_REQUIRED"


def test_8105_core_standard_source_join_markdown_states_boundary() -> None:
    markdown = render_markdown(build_plan())

    assert "# 8105 Core Standard Source Join Pilot Plan" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "CNBE rows written: 0" in markdown
    assert "standard-source extraction plan" in markdown
