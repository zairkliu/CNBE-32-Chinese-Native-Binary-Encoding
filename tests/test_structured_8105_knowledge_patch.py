"""Tests for authorized structured 8105 knowledge patch planning."""

from __future__ import annotations

from scripts.patch_structured_8105_knowledge import build_patch, render_markdown


def test_patch_dry_run_keeps_batch_scoring_blocked() -> None:
    report = build_patch(apply=False)

    assert report["overall_status"] == "PASS"
    assert report["mode"] == "dry_run"
    assert report["summary"]["baseline_rows"] == 8105
    assert report["summary"]["source_write_applied"] is False
    assert report["summary"]["batch_scoring_allowed"] is False


def test_patch_dry_run_repairs_known_structured_diffs() -> None:
    report = build_patch(apply=False)

    for key in ["base_character_data", "cnbe_character_knowledge"]:
        summary = report["summary"][key]
        assert len(summary["missing_before"]) in {0, 3}
        assert len(summary["extra_before"]) in {0, 2}
        assert summary["rows_after"] == 8105


def test_patch_markdown_states_write_boundary() -> None:
    markdown = render_markdown(build_patch(apply=False))

    assert "# Structured 8105 Knowledge Patch Report" in markdown
    assert "does not modify CNBE encoding tables" in markdown
    assert "Batch scoring allowed by this patch" in markdown
