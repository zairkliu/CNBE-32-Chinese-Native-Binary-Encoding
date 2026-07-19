"""Tests for the bounded 300-character 8105 pilot plan."""

from __future__ import annotations

from scripts.plan_300_character_8105_pilot import build_plan, render_markdown


def test_300_character_8105_pilot_plan_is_ready() -> None:
    report = build_plan()

    assert report["overall_status"] == "PASS_300_CHARACTER_8105_PILOT_PLAN_READY"
    assert report["summary"]["source_rows"] == 97686
    assert report["summary"]["pilot_rows"] == 300
    assert report["decision"]["may_run_pilot_evidence_join"] is True


def test_300_character_8105_pilot_plan_has_three_equal_strata() -> None:
    report = build_plan()

    assert report["summary"]["stratum_counts"] == {
        "8105_core_control": 100,
        "outside_8105_extension_or_gap": 100,
        "outside_8105_strong_dictionary_context": 100,
    }
    assert report["summary"]["catalog_scope_counts"]["8105_core"] == 100
    assert report["summary"]["catalog_scope_counts"]["outside_8105_agent_candidate"] == 200


def test_300_character_8105_pilot_plan_keeps_human_fields_blank() -> None:
    report = build_plan()

    assert report["checks"]["human_fields_blank"] is True
    for row in report["pilot_rows"]:
        assert row["human_review_status"] == "待审核"
        assert row["human_structure_label"] == ""
        assert row["human_decomposition"] == ""
        assert row["editable_copy_notice"] == "PILOT_REVIEW_COPY_NOT_SOURCE_EVIDENCE"


def test_300_character_8105_pilot_plan_blocks_scoring_and_writes() -> None:
    report = build_plan()

    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["summary"]["cnbe_rows_written"] == 0
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["xlsx_generated"] is False
    assert report["decision"]["may_start_full_catalog_encoding"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False


def test_300_character_8105_pilot_markdown_states_boundary() -> None:
    markdown = render_markdown(build_plan())

    assert "# 300 Character 8105 Pilot Plan" in markdown
    assert "Pilot rows: 300" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "XLSX generated: `False`" in markdown
