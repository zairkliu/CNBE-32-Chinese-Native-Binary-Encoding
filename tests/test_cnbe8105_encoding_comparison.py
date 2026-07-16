"""Tests for the 8105 CNBE encoding comparison audit."""

from __future__ import annotations

from scripts.audit_cnbe8105_encoding_comparison import (
    ALLOWED_STRUCTURE_SET,
    RESEARCH_ROOT,
    build_outputs,
    normalize_structure,
)


def test_structure_policy_excludes_right_bottom_label() -> None:
    assert "右下包" not in ALLOWED_STRUCTURE_SET
    assert normalize_structure("右下包", "⿺辶留") == ("左下包", "normalized_right_bottom_to_left_bottom")
    assert normalize_structure("右下包", None) == (None, "invalid_standard_structure")


def test_build_outputs_contains_expected_8105_scope() -> None:
    baseline, snapshot, comparison, markdown = build_outputs(RESEARCH_ROOT)
    assert baseline["summary"]["row_count"] == 8105
    assert baseline["summary"]["row_count_matches_expected"] is True
    assert snapshot["summary"]["baseline_rows"] == 8105
    assert comparison["summary"]["total_standard_rows"] == 8105
    assert "# CNBE-32 8105 Encoding Comparison Report" in markdown


def test_known_high_confidence_failures_are_detected() -> None:
    _, _, comparison, _ = build_outputs(RESEARCH_ROOT)
    characters = comparison["characters"]

    assert characters["家"]["status"] == "FAIL_FIXABLE"
    assert characters["家"]["field_results"]["radical"]["standard"] == "宀"
    assert characters["家"]["field_results"]["stroke_count"]["standard"] == 10
    assert characters["家"]["field_results"]["structure"]["standard"] == "上下"

    assert characters["涡"]["status"] == "FAIL_FIXABLE"
    assert characters["涡"]["field_results"]["radical"]["standard"] == "氵"
    assert characters["涡"]["field_results"]["structure"]["standard"] == "左右"


def test_review_required_and_normalized_structure_samples() -> None:
    _, _, comparison, _ = build_outputs(RESEARCH_ROOT)
    characters = comparison["characters"]

    assert characters["与"]["status"] == "FAIL_REVIEW_REQUIRED"
    assert "ambiguous_decomposition" in characters["与"]["issues"]

    assert characters["遛"]["status"] == "FAIL_FIXABLE"
    assert characters["遛"]["standard"]["raw_structure"] == "右下包"
    assert characters["遛"]["standard"]["structure"] == "左下包"
