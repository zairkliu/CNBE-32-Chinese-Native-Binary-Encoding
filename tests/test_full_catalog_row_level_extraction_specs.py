"""Tests for full-catalog row-level extraction specifications."""

from __future__ import annotations

from scripts.design_full_catalog_row_level_extraction_specs import build_specs, render_markdown


def test_extraction_specs_are_ready_for_seven_automatable_items() -> None:
    report = build_specs()

    assert report["overall_status"] == "PASS_ROW_LEVEL_EXTRACTION_SPECS_READY"
    assert report["summary"]["spec_count"] == 7
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["policy_decision_items"] == ["character_set_coverage"]


def test_extraction_specs_keep_scoring_and_writes_blocked() -> None:
    report = build_specs()

    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_extraction_specs_define_expected_output_tables() -> None:
    report = build_specs()
    specs = {spec["gf0017_item"]: spec for spec in report["extraction_specs"]}

    assert specs["stroke_shape"]["output_table"] == "stroke_evidence"
    assert specs["stroke_order"]["output_table"] == "stroke_evidence"
    assert specs["component_validity"]["output_table"] == "component_evidence"
    assert specs["component_name_validity"]["output_table"] == "component_evidence"
    assert specs["radical_validity"]["output_table"] == "radical_evidence"
    assert specs["independent_character_rule"]["output_table"] == "structure_evidence"
    assert specs["structure_first_decomposition"]["output_table"] == "structure_evidence"


def test_extraction_specs_have_failure_codes_and_validation_rules() -> None:
    report = build_specs()

    for spec in report["extraction_specs"]:
        assert spec["join_key"] == "unicode"
        assert spec["failure_codes"]
        assert spec["validation_rules"]
        assert spec["can_assign_points_after_extraction"] is False


def test_extraction_specs_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_specs())

    assert "# Full Catalog Row-Level Extraction Specs" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "Formal scoring" in markdown
