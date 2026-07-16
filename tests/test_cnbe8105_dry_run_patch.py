"""Tests for the 8105 dry-run patch builder."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_cnbe8105_dry_run_patch import (
    DEFAULT_CANDIDATE_INPUT,
    DEFAULT_RADICAL_MAP_INPUT,
    build_dry_run_patch,
    decode_cnbe_fields,
)


def dry_run_model() -> dict:
    candidate_model = json.loads(Path(DEFAULT_CANDIDATE_INPUT).read_text(encoding="utf-8"))
    radical_model = json.loads(Path(DEFAULT_RADICAL_MAP_INPUT).read_text(encoding="utf-8"))
    return build_dry_run_patch(candidate_model, radical_model)


def test_dry_run_counts_match_radical_gate() -> None:
    model = dry_run_model()
    assert model["summary"]["dry_run_ready_rows"] == 6184
    assert model["summary"]["radix_blocked_rows"] == 130
    assert model["summary"]["all_roundtrips_pass"] is True
    assert model["summary"]["write_gate"] == "NO_WRITE_DRY_RUN_ONLY"


def test_known_ready_samples_have_expected_codes() -> None:
    known = dry_run_model()["samples"]["known_ready"]
    family = known["家"]
    assert family["proposed"]["radix"] == 40
    assert family["proposed"]["strokes"] == 10
    assert family["proposed"]["struct_type"] == 1
    assert family["proposed"]["struct_name"] == "上下"
    assert decode_cnbe_fields(family["proposed"]["cnbe"]) == family["roundtrip"]["decoded"]

    stroll = known["遛"]
    assert stroll["proposed"]["radix"] == 162
    assert stroll["proposed"]["struct_name"] == "左下包"

    whirl = known["涡"]
    assert whirl["proposed"]["radix"] == 85
    assert whirl["proposed"]["struct_name"] == "左右"


def test_blocked_rows_are_not_in_patch() -> None:
    model = dry_run_model()
    patch_chars = {record["char"] for record in model["patch"]}
    blocked_chars = {record["char"] for record in model["blocked"]}
    assert patch_chars.isdisjoint(blocked_chars)
    assert any(record["proposed_radix_name"] == "阝" for record in model["blocked"])
