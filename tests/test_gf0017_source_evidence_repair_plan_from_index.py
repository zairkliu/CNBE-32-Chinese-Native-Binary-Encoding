"""Tests for GF0017 source-evidence repair planning from the existing index."""

from __future__ import annotations

from scripts.plan_gf0017_source_evidence_repair_from_index import build_repair_plan, render_markdown


def test_gf0017_source_evidence_repair_plan_is_ready() -> None:
    report = build_repair_plan()

    assert report["overall_status"] == "PASS_GF0017_SOURCE_EVIDENCE_REPAIR_PLAN_READY"
    assert report["summary"]["total_rows"] == 97686
    assert report["summary"]["rows_fully_scored"] == 0
    assert report["summary"]["highest_priority_item"] == "structure_first_decomposition"
    assert report["decision"]["may_start_structure_decomposition_evidence_repair"] is True


def test_gf0017_source_evidence_repair_plan_preserves_boundaries() -> None:
    report = build_repair_plan()

    assert report["authority_boundary"]["uses_existing_unified_index_only"] is True
    assert report["authority_boundary"]["does_not_regenerate_full_unicode_catalog"] is True
    assert report["authority_boundary"]["does_not_assign_new_gf0017_points"] is True
    assert report["authority_boundary"]["does_not_emit_final_structure_labels"] is True
    assert report["decision"]["may_assign_new_gf0017_points"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_gf0017_source_evidence_repair_plan_prioritizes_point_weight() -> None:
    report = build_repair_plan()
    plans = report["item_repair_plans"]

    assert plans[0]["item"] == "structure_first_decomposition"
    assert plans[0]["points"] == 20
    assert plans[0]["blocked_rows"] == 97686
    assert plans[1]["item"] == "component_name_validity"
    assert plans[2]["item"] == "independent_character_rule"
    assert "character_set_coverage" in report["summary"]["policy_decision_items"]


def test_gf0017_source_evidence_repair_plan_markdown_states_next_gate() -> None:
    markdown = render_markdown(build_repair_plan())

    assert "# GF0017 Source Evidence Repair Plan From Existing Index" in markdown
    assert "not regenerate the full Unicode catalog" in markdown
    assert "structure/decomposition" in markdown
    assert "CNBE row" in markdown
