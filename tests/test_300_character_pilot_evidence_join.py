"""Tests for the read-only 300-character pilot evidence join."""

from __future__ import annotations

from scripts.run_300_character_pilot_evidence_join import build_join, render_markdown


def test_300_character_pilot_evidence_join_passes() -> None:
    report = build_join()

    assert report["overall_status"] == "PASS_300_CHARACTER_PILOT_EVIDENCE_JOIN_READY_FOR_REVIEW"
    assert report["summary"]["pilot_rows"] == 300
    assert report["checks"]["pilot_plan_passed"] is True
    assert report["decision"]["may_start_human_review_on_join_csv"] is True


def test_300_character_pilot_evidence_join_preserves_boundaries() -> None:
    report = build_join()

    assert report["authority_boundary"]["8105_core_remains_national_standard_core"] is True
    assert report["authority_boundary"]["outside_8105_remains_agent_candidate"] is True
    assert report["authority_boundary"]["dictionary_context_is_review_context"] is True
    assert report["decision"]["may_assign_gf0017_points"] is False
    assert report["decision"]["may_emit_final_structure_labels"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_300_character_pilot_evidence_join_counts_are_expected() -> None:
    report = build_join()

    assert report["summary"]["stratum_counts"] == {
        "8105_core_control": 100,
        "outside_8105_extension_or_gap": 100,
        "outside_8105_strong_dictionary_context": 100,
    }
    assert report["summary"]["zdic_url_rows"] == 300
    assert report["summary"]["gf0017_points_assigned"] == 0
    assert report["summary"]["final_structure_labels_emitted"] == 0
    assert report["summary"]["cnbe_rows_written"] == 0


def test_300_character_pilot_evidence_join_rows_are_not_final_outputs() -> None:
    report = build_join()

    for row in report["joined_rows"]:
        assert row["unicode_identity_status"] == "PASS_UNICODE_IDENTITY_FROM_EXISTING_INDEX"
        assert row["gf0017_points_assigned"] == 0
        assert row["final_structure_label"] == ""
        assert row["cnbe_write_status"] == "NO_CNBE_WRITE"
        assert row["editable_copy_notice"] == "PILOT_EVIDENCE_JOIN_REVIEW_ONLY_NOT_SOURCE_EVIDENCE"


def test_300_character_pilot_evidence_join_markdown_states_no_write_boundary() -> None:
    markdown = render_markdown(build_join())

    assert "# 300 Character Pilot Evidence Join" in markdown
    assert "GF0017 points assigned: 0" in markdown
    assert "CNBE rows written: 0" in markdown
    assert "XLSX generated: `False`" in markdown
