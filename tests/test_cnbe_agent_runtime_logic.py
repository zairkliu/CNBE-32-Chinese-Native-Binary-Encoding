"""Tests for the CNBE Agent runtime logic verification report."""

from __future__ import annotations

from scripts.verify_cnbe_agent_runtime_logic import build_verification, render_markdown


def test_agent_runtime_logic_verification_passes_without_enabling_batch_scoring() -> None:
    report = build_verification()

    assert report["overall_status"] == "PASS"
    assert report["next_workflow_status"] == "PREFLIGHT_ALLOWED_BATCH_SCORING_BLOCKED"
    assert report["decision"]["may_start_gf0017_preflight_plan"] is True
    assert report["decision"]["may_start_batch_gf0017_scoring"] is False
    assert report["decision"]["may_rebuild_database"] is False


def test_agent_runtime_logic_preserves_expected_no_go_gate() -> None:
    report = build_verification()

    assert report["gates"]["knowledge_asset_stop_gate"]["status"] == "PASS"
    assert report["key_counts"]["knowledge_blockers"] == len(report["expected_no_go_reasons"])
    assert report["key_counts"]["knowledge_blockers"] >= 0
    assert report["decision"]["may_start_batch_gf0017_scoring"] is False


def test_agent_runtime_logic_counts_core_inputs() -> None:
    report = build_verification()

    assert report["key_counts"]["agent_rows"] == 20902
    assert report["key_counts"]["agent_unicode_pass"] == 20902
    assert report["key_counts"]["full_catalog_rows"] == 97686
    assert report["key_counts"]["gf0017_rows"] == 8105


def test_agent_runtime_markdown_states_read_only_boundary() -> None:
    report = build_verification()
    markdown = render_markdown(report)

    assert "# CNBE Agent Runtime Logic Verification" in markdown
    assert "read-only" in markdown
    assert "blocks batch scoring and database reconstruction" in markdown
