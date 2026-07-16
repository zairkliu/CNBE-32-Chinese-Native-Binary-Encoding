"""Tests for the 8105 radical numeric-code map."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_cnbe8105_radical_code_map import (
    DEFAULT_CANDIDATE_INPUT,
    KNOWLEDGE_BASE,
    build_radical_mapping,
    load_radical_code_source,
    resolve_radical,
)


def test_radical_source_exposes_214_codes_and_count_mismatch() -> None:
    source = load_radical_code_source(KNOWLEDGE_BASE)
    assert source["metadata"]["actual_count"] == 214
    assert source["metadata"]["declared_count"] != source["metadata"]["actual_count"]
    assert source["radical_to_code"]["宀"] == 40
    assert source["radical_to_code"]["水"] == 85
    assert source["radical_to_code"]["辵"] == 162


def test_resolve_radical_direct_alias_and_blocked() -> None:
    source = load_radical_code_source(KNOWLEDGE_BASE)
    mapping = source["radical_to_code"]
    assert resolve_radical("宀", mapping)["status"] == "DIRECT"

    water = resolve_radical("氵", mapping)
    assert water["status"] == "ALIAS"
    assert water["canonical_radical"] == "水"
    assert water["code"] == 85

    walk = resolve_radical("辶", mapping)
    assert walk["status"] == "ALIAS"
    assert walk["canonical_radical"] == "辵"
    assert walk["code"] == 162

    side = resolve_radical("阝", mapping)
    assert side["status"] == "BLOCKED"
    assert side["code"] is None


def test_build_radical_mapping_keeps_blocked_rows_out_of_ready_pool() -> None:
    candidate_model = json.loads(Path(DEFAULT_CANDIDATE_INPUT).read_text(encoding="utf-8"))
    source = load_radical_code_source(KNOWLEDGE_BASE)
    model = build_radical_mapping(candidate_model, source)
    summary = model["summary"]
    assert summary["candidate_rows"] == 6314
    assert summary["ready_candidate_rows"] + summary["blocked_candidate_rows"] == 6314
    assert summary["blocked_radical_names"] > 0
    assert any(record["radical"] == "阝" for record in model["blocked_radicals"])
