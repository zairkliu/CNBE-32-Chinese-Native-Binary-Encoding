"""Tests for the 8105-core to full-catalog encoding plan."""

from __future__ import annotations

from scripts.plan_8105_core_rule_to_full_catalog_encoding import build_plan, render_markdown


def test_8105_core_rule_plan_is_ready() -> None:
    report = build_plan()

    assert report["overall_status"] == "PASS_8105_CORE_RULE_TO_FULL_CATALOG_ENCODING_PLAN_READY"
    assert report["catalog_scope"]["total_rows"] == 97686
    assert report["catalog_scope"]["core_8105_rows"] == 8105
    assert report["catalog_scope"]["outside_8105_rows"] == 89581
    assert report["decision"]["may_create_300_character_pilot_plan"] is True


def test_8105_core_rule_plan_preserves_authority_layers() -> None:
    report = build_plan()

    assert report["core_position"]["status"] == "national_standard_core"
    assert report["evidence_layers"]["national_standard"]["priority"] == 1
    assert report["evidence_layers"]["standard_aligned"]["priority"] == 2
    assert report["evidence_layers"]["cross_reference_only"]["priority"] == 3
    assert report["catalog_scope"]["outside_8105_status"] == "agent_standard_candidate_not_national_standard"


def test_8105_core_rule_plan_blocks_encoding_writes() -> None:
    report = build_plan()

    assert report["decision"]["may_start_full_catalog_encoding"] is False
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert "do not label outside-8105 rows as national-standard outputs" in report["stop_gates"]


def test_8105_core_rule_plan_defines_300_character_pilot() -> None:
    report = build_plan()
    strata = report["pilot_design"]["strata"]

    assert report["pilot_design"]["recommended_size"] == 300
    assert sum(item["rows"] for item in strata) == 300
    assert [item["rows"] for item in strata] == [100, 100, 100]
    assert report["pilot_design"]["write_policy"] == "read_only_reports_only"


def test_8105_core_rule_plan_markdown_states_boundary() -> None:
    markdown = render_markdown(build_plan())

    assert "# 8105 Core Rule To Full Catalog Encoding Plan" in markdown
    assert "8105 national-standard core rows: 8105" in markdown
    assert "May start full-catalog encoding: `False`" in markdown
    assert "do not generate final structure labels from visual intuition" in markdown
