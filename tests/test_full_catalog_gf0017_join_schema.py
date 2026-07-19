"""Tests for the full-catalog GF0017 join schema."""

from __future__ import annotations

from scripts.design_full_catalog_gf0017_join_schema import build_join_schema, render_markdown


def test_join_schema_is_ready_but_keeps_scoring_blocked() -> None:
    schema = build_join_schema()

    assert schema["overall_status"] == "PASS"
    assert schema["next_workflow_status"] == "JOIN_SCHEMA_READY_BLOCKER_RECONCILIATION_REQUIRED"
    assert schema["decision"]["may_start_blocker_reconciliation"] is True
    assert schema["decision"]["may_start_batch_gf0017_scoring"] is False
    assert schema["decision"]["may_rebuild_database"] is False


def test_join_schema_preserves_expected_counts() -> None:
    schema = build_join_schema()

    assert schema["summary"]["workbook_columns"] == 17
    assert schema["summary"]["data_rows"] == 97686
    assert schema["summary"]["gf0017_items"] == 8
    assert schema["summary"]["gf0017_total_points"] == 50
    assert schema["summary"]["evidence_tables"] == 5
    assert schema["summary"]["blocker_rules"] == 6


def test_join_schema_defines_required_evidence_tables() -> None:
    schema = build_join_schema()
    table_ids = {table["table_id"] for table in schema["evidence_tables"]}

    assert table_ids == {
        "unicode_identity",
        "gf0017_source_items",
        "agent_structure_localization",
        "standard_hanzi_knowledge",
        "cnbe32_carrier_snapshot",
    }


def test_join_schema_forbids_scores_before_batch_phase() -> None:
    schema = build_join_schema()
    policy = schema["row_schema"]["score_policy"]

    assert policy["score_values_allowed"] is False
    assert policy["numeric_score_before_batch_phase"] == "FORBIDDEN"
    assert policy["source_gap_as_pass"] == "FORBIDDEN"


def test_join_schema_markdown_states_boundaries() -> None:
    markdown = render_markdown(build_join_schema())

    assert "# Full Catalog GF0017 Join Schema" in markdown
    assert "It is read-only" in markdown
    assert "Batch GF0017 scoring remains blocked" in markdown
