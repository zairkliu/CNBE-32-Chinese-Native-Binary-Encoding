"""Tests for the full-catalog Agent mapping evidence-join design."""

from __future__ import annotations

from scripts.design_full_catalog_agent_mapping_evidence_join import build_join_design, render_markdown


def test_evidence_join_design_is_ready_without_scores() -> None:
    report = build_join_design()

    assert report["overall_status"] == "PASS_EVIDENCE_JOIN_DESIGN_READY"
    assert report["summary"]["outside_8105_rows"] == 89581
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False


def test_evidence_join_design_defines_expected_tables_and_items() -> None:
    report = build_join_design()

    assert report["summary"]["join_output_tables"] == 7
    assert report["summary"]["gf0017_items"] == 8
    assert report["summary"]["missing_source_paths"] == []
    assert {table["name"] for table in report["join_output_tables"]} >= {
        "unicode_identity",
        "stroke_evidence",
        "component_evidence",
        "radical_evidence",
        "structure_evidence",
        "gf0017_item_evidence_status",
    }


def test_evidence_join_design_preserves_source_gap_classes() -> None:
    report = build_join_design()

    assert report["summary"]["source_gap_items"] == ["character_set_coverage", "stroke_shape"]
    assert report["summary"]["source_evidence_required_items"] == [
        "stroke_order",
        "component_validity",
        "component_name_validity",
        "radical_validity",
        "independent_character_rule",
        "structure_first_decomposition",
    ]


def test_evidence_join_design_keeps_dangerous_steps_blocked() -> None:
    report = build_join_design()
    steps = {step["name"]: step["allowed_now"] for step in report["implementation_order"]}

    assert steps["materialize_unicode_identity_view"] is True
    assert steps["join_gf0017_item_evidence_status"] is True
    assert steps["assign_formal_gf0017_scores"] is False
    assert steps["generate_or_repair_cnbe_rows"] is False
    assert report["decision"]["may_implement_row_level_evidence_join"] is True
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_evidence_join_design_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_join_design())

    assert "# Full Catalog Agent Mapping Evidence Join Design" in markdown
    assert "It does not assign GF0017 scores" in markdown
    assert "CNBE row" in markdown
