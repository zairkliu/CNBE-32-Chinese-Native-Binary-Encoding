"""Tests for the unified Hanzi evidence index audit."""

from __future__ import annotations

from scripts.audit_unified_hanzi_evidence_index import audit_index, render_markdown


def test_unified_hanzi_evidence_index_audit_passes() -> None:
    report = audit_index()

    assert report["overall_status"] == "PASS_UNIFIED_EVIDENCE_INDEX_AUDITED"
    assert report["summary"]["total_entries"] == 97686
    assert report["summary"]["catalog_scope_counts"]["8105_core"] == 8105
    assert report["summary"]["catalog_scope_counts"]["outside_8105_agent_candidate"] == 89581
    assert all(report["checks"].values())


def test_unified_hanzi_evidence_index_audit_keeps_stop_gates() -> None:
    report = audit_index()

    assert report["decision"]["may_start_human_review"] is True
    assert report["decision"]["may_start_formal_gf0017_scoring"] is False
    assert report["decision"]["may_write_cnbe_rows"] is False
    assert report["decision"]["may_rebuild_database"] is False
    assert report["summary"]["formal_gf0017_scoring_allowed"] is False
    assert report["summary"]["cnbe_row_write_allowed"] is False
    assert report["summary"]["database_rebuild_allowed"] is False


def test_unified_hanzi_evidence_index_audit_markdown_is_human_readable() -> None:
    markdown = render_markdown(audit_index())

    assert "# Unified Hanzi Evidence Index Audit" in markdown
    assert "PASS_UNIFIED_EVIDENCE_INDEX_AUDITED" in markdown
    assert "May start formal GF0017 scoring: `False`" in markdown
