"""Tests for bounded 8105 core pilot GF0017 partial scoring."""

from __future__ import annotations

from scripts.score_8105_core_pilot_gf0017_partial import build_scoring_report, render_markdown


def test_8105_core_pilot_gf0017_partial_scoring_passes() -> None:
    report = build_scoring_report()

    assert report["overall_status"] == "PASS_8105_CORE_PILOT_GF0017_PARTIAL_SCORING_READY"
    assert report["summary"]["rows_evaluated"] == 100
    assert report["summary"]["rows_partially_scored"] == 100
    assert report["summary"]["rows_fully_scored"] == 0


def test_8105_core_pilot_gf0017_partial_scoring_scores_only_supported_items() -> None:
    report = build_scoring_report()

    assert report["summary"]["assignable_items"] == ["character_set_coverage", "stroke_order"]
    assert report["summary"]["assigned_max_per_row"] == 6
    assert report["summary"]["assigned_score_total"] == 600
    assert report["item_score_totals"]["character_set_coverage"] == 300
    assert report["item_score_totals"]["stroke_order"] == 300
    assert report["item_score_totals"]["structure_first_decomposition"] == 0


def test_8105_core_pilot_gf0017_partial_scoring_keeps_missing_evidence_unscored() -> None:
    report = build_scoring_report()

    blocked = set(report["summary"]["blocked_items"])
    assert "structure_first_decomposition" in blocked
    assert "component_validity" in blocked
    assert "component_name_validity" in blocked
    assert "radical_validity" in blocked
    for row in report["scored_rows"]:
        assert row["items"]["structure_first_decomposition"]["score"] is None
        assert row["items"]["component_validity"]["score"] is None
        assert row["items"]["radical_validity"]["score"] is None


def test_8105_core_pilot_gf0017_partial_scoring_keeps_writes_blocked() -> None:
    report = build_scoring_report()

    assert report["decision"]["may_continue_bounded_standardizer_extraction"] is True
    assert report["decision"]["may_assign_more_points_without_extraction"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["authority_boundary"]["does_not_score_missing_evidence_as_zero"] is True


def test_8105_core_pilot_gf0017_partial_scoring_markdown_states_boundary() -> None:
    markdown = render_markdown(build_scoring_report())

    assert "# 8105 Core Pilot GF0017 Partial Scoring" in markdown
    assert "Assigned max per row: 6 / 50" in markdown
    assert "Missing evidence is not scored as zero" in markdown
