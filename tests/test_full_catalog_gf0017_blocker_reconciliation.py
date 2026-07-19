"""Tests for full-catalog GF0017 blocker reconciliation."""

from __future__ import annotations

from scripts.reconcile_full_catalog_gf0017_blockers import build_reconciliation, render_markdown


def test_blocker_reconciliation_reaches_read_only_decision_point() -> None:
    report = build_reconciliation()

    assert report["overall_status"] == "PASS"
    assert report["next_workflow_status"] == "DECISION_POINT_REACHED_READ_ONLY_DIFF_ALLOWED"
    assert report["decision_point"]["requires_human_decision"] in {False, True}
    assert report["summary"]["batch_scoring_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False


def test_blocker_reconciliation_confirms_no_open_knowledge_blockers() -> None:
    report = build_reconciliation()
    classifications = report["summary"]["classification_counts"]

    assert report["summary"]["blockers"] == 0
    assert classifications == {}
    assert report["blockers"] == []


def test_blocker_reconciliation_forbids_writes_and_scoring() -> None:
    report = build_reconciliation()

    assert report["authority_boundary"]["does_not_modify_knowledge_assets"] is True
    assert report["authority_boundary"]["does_not_score_rows"] is True
    assert "start batch GF0017 scoring" in report["decision_point"]["requires_authorization_before_write"]


def test_blocker_reconciliation_markdown_states_decision_boundary() -> None:
    markdown = render_markdown(build_reconciliation())

    assert "# Full Catalog GF0017 Blocker Reconciliation" in markdown
    assert "It is read-only" in markdown
    assert "Requires authorization before write" in markdown
