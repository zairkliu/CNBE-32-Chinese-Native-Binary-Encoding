"""Tests for the 8105 CNBE auto-fix candidate builder."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_cnbe8105_auto_fix_candidates import (
    BLOCKED_FIELDS,
    build_candidates,
)

COMPARISON_EVIDENCE = Path("evidence/8105/cnbe8105_encoding_comparison.json")


def comparison_model() -> dict:
    return json.loads(COMPARISON_EVIDENCE.read_text(encoding="utf-8"))


def test_candidate_pool_uses_only_fail_fixable_rows() -> None:
    model = build_candidates(comparison_model())
    assert model["summary"]["candidate_rows"] == 6314
    assert model["summary"]["apply_gate"] == "NO_APPLY_IN_THIS_PHASE"
    assert set(BLOCKED_FIELDS) == {"cnbe", "radix"}
    for record in model["candidates"][:100]:
        assert record["source_status"] == "FAIL_FIXABLE"
        assert record["status"] == "AUTO_FIX_CANDIDATE"
        assert record["apply_gate"] == "NO_APPLY_IN_THIS_PHASE"


def test_known_samples_are_candidates_with_standard_fields() -> None:
    model = build_candidates(comparison_model())
    known = model["samples"]["known_samples"]

    assert known["家"]["proposed"]["radix_name"] == "宀"
    assert known["家"]["proposed"]["strokes"] == 10
    assert known["家"]["proposed"]["struct_name"] == "上下"

    assert known["遛"]["proposed"]["radix_name"] == "辶"
    assert known["遛"]["proposed"]["struct_name"] == "左下包"

    assert known["涡"]["proposed"]["radix_name"] == "氵"
    assert known["涡"]["proposed"]["struct_name"] == "左右"


def test_review_required_rows_are_excluded() -> None:
    model = build_candidates(comparison_model())
    chars = {record["char"] for record in model["candidates"]}
    assert "与" not in chars
    assert "鼻" not in chars
    assert model["summary"]["exclusion_counts"]["status_FAIL_REVIEW_REQUIRED"] == 547
    assert model["summary"]["exclusion_counts"]["status_EVIDENCE_GAP"] == 1244
