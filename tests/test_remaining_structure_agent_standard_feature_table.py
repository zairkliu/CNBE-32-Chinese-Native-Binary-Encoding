"""Tests for remaining structure Agent-standard feature table runner."""

from __future__ import annotations

from scripts.run_remaining_structure_agent_standard_feature_table import build_feature_table, render_markdown


def test_feature_table_is_ready_and_covers_remaining_rows() -> None:
    report = build_feature_table()

    assert report["overall_status"] == "PASS_AGENT_STANDARD_FEATURE_TABLE_READY"
    assert report["summary"]["feature_rows"] == 73831
    assert len(report["row_records"]) == 73831


def test_feature_table_has_expected_review_queues() -> None:
    report = build_feature_table()

    assert report["summary"]["review_queue_counts"] == {
        "agent_standard_extension_review_candidate": 67946,
        "agent_standard_rule_learning_candidate": 5885,
    }
    assert sum(report["summary"]["review_prior_counts"].values()) == 73831


def test_feature_table_blocks_final_structure_scores_and_writes() -> None:
    report = build_feature_table()

    assert report["summary"]["score_values_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["source_asset_write_allowed"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_modify_cnbe_rows"] is False


def test_feature_table_records_only_allowed_feature_schema() -> None:
    report = build_feature_table()
    row = report["row_records"][0]

    assert "final_structure_label" not in row
    assert "gf0017_score" not in row
    assert "cnbe32_fields" not in row
    assert row["standard_level"] == "agent_standard_candidate_not_national_standard"
    assert row["can_assign_points"] is False
    assert "final_structure_label" in report["feature_schema"]["forbidden_fields"]


def test_feature_table_markdown_states_no_final_labels() -> None:
    markdown = render_markdown(build_feature_table())

    assert "# Remaining Structure Agent-Standard Feature Table" in markdown
    assert "does not assign GF0017 scores" in markdown
    assert "emit final structure labels" in markdown
