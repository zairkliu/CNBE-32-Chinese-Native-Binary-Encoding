"""Tests for the lightweight CNBE 8105 core confirmation."""

from __future__ import annotations

from scripts.confirm_cnbe8105_core import build_confirmation, render_markdown


def test_cnbe8105_core_confirmation_passes() -> None:
    report = build_confirmation()

    assert report["overall_status"] == "PASS_CNBE8105_CORE_CONFIRMATION_READY_TO_PUSH"
    assert report["summary"]["baseline_rows"] == 8105
    assert report["checks"]["baseline_row_count_is_8105"] is True
    assert report["checks"]["gf0017_score_rows_are_8105"] is True


def test_cnbe8105_core_confirmation_preserves_boundaries() -> None:
    report = build_confirmation()

    assert report["confirmation"]["8105_is_controlling_core"] is True
    assert report["confirmation"]["current_cnbe_requires_repair_or_review"] is True
    assert report["confirmation"]["gf0017_full_scoring_not_complete"] is True
    assert report["confirmation"]["cnbe32_write_allowed"] is False
    assert report["confirmation"]["database_rebuild_allowed"] is False
    assert report["confirmation"]["release_or_pypi_allowed"] is False


def test_cnbe8105_core_confirmation_markdown_states_no_write_boundary() -> None:
    markdown = render_markdown(build_confirmation())

    assert "# CNBE 8105 Core Confirmation" in markdown
    assert "CNBE32 writes are not allowed" in markdown
    assert "Full GF0017 scoring remains incomplete" in markdown
