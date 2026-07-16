"""Tests for the 8105 CNBE encoding comparison audit."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_cnbe8105_encoding_comparison import (
    ALLOWED_STRUCTURE_SET,
    normalize_structure,
)

BASELINE_EVIDENCE = Path("evidence/8105/cnbe8105_standard_baseline.json")
SNAPSHOT_EVIDENCE = Path("evidence/8105/cnbe8105_current_cnbe_snapshot.json")
COMPARISON_EVIDENCE = Path("evidence/8105/cnbe8105_encoding_comparison.json")
MARKDOWN_EVIDENCE = Path("evidence/8105/CNBE8105_ENCODING_COMPARISON_REPORT.md")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_structure_policy_excludes_right_bottom_label() -> None:
    assert "右下包" not in ALLOWED_STRUCTURE_SET
    assert normalize_structure("右下包", "⿺辶留") == ("左下包", "normalized_right_bottom_to_left_bottom")
    assert normalize_structure("右下包", None) == (None, "invalid_standard_structure")


def test_build_outputs_contains_expected_8105_scope() -> None:
    baseline = load_json(BASELINE_EVIDENCE)
    snapshot = load_json(SNAPSHOT_EVIDENCE)
    comparison = load_json(COMPARISON_EVIDENCE)
    markdown = MARKDOWN_EVIDENCE.read_text(encoding="utf-8")
    assert baseline["summary"]["row_count"] == 8105
    assert baseline["summary"]["row_count_matches_expected"] is True
    assert snapshot["summary"]["baseline_rows"] == 8105
    assert comparison["summary"]["total_standard_rows"] == 8105
    assert "# CNBE-32 8105 Encoding Comparison Report" in markdown


def test_known_high_confidence_failures_are_detected() -> None:
    comparison = load_json(COMPARISON_EVIDENCE)
    characters = comparison["characters"]

    assert characters["家"]["status"] == "FAIL_FIXABLE"
    assert characters["家"]["field_results"]["radical"]["standard"] == "宀"
    assert characters["家"]["field_results"]["stroke_count"]["standard"] == 10
    assert characters["家"]["field_results"]["structure"]["standard"] == "上下"

    assert characters["涡"]["status"] == "FAIL_FIXABLE"
    assert characters["涡"]["field_results"]["radical"]["standard"] == "氵"
    assert characters["涡"]["field_results"]["structure"]["standard"] == "左右"


def test_review_required_and_normalized_structure_samples() -> None:
    comparison = load_json(COMPARISON_EVIDENCE)
    characters = comparison["characters"]

    assert characters["与"]["status"] == "FAIL_REVIEW_REQUIRED"
    assert "ambiguous_decomposition" in characters["与"]["issues"]

    assert characters["遛"]["status"] == "FAIL_FIXABLE"
    assert characters["遛"]["standard"]["raw_structure"] == "右下包"
    assert characters["遛"]["standard"]["structure"] == "左下包"
