"""Tests for the 8105 radical numeric-code map."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build_cnbe8105_radical_code_map import (
    DEFAULT_CANDIDATE_INPUT,
    build_radical_mapping,
    resolve_radical,
)

RADICAL_MAP_EVIDENCE = Path("evidence/8105/cnbe8105_radical_code_map.json")


def load_radical_map_evidence() -> dict:
    return json.loads(RADICAL_MAP_EVIDENCE.read_text(encoding="utf-8"))


def radical_to_code_from_evidence(model: dict) -> dict[str, int]:
    mapping = {}
    for record in model["direct_radicals"] + model["alias_radicals"]:
        if record["status"] == "DIRECT":
            mapping[record["radical"]] = record["code"]
        if record["canonical_radical"]:
            mapping[record["canonical_radical"]] = record["code"]
    return mapping


def test_radical_source_exposes_214_codes_and_count_mismatch() -> None:
    model = load_radical_map_evidence()
    assert model["summary"]["source_actual_count"] == 214
    assert model["summary"]["source_declared_count"] != model["summary"]["source_actual_count"]
    radical_to_code = radical_to_code_from_evidence(model)
    assert radical_to_code["宀"] == 40
    assert radical_to_code["水"] == 85
    assert radical_to_code["辵"] == 162


def test_resolve_radical_direct_alias_and_blocked() -> None:
    mapping = radical_to_code_from_evidence(load_radical_map_evidence())
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
    evidence_model = load_radical_map_evidence()
    source = {
        "metadata": {
            "actual_count": evidence_model["summary"]["source_actual_count"],
            "declared_count": evidence_model["summary"]["source_declared_count"],
            "source": evidence_model["metadata"]["source"]["source"],
        },
        "radical_to_code": radical_to_code_from_evidence(evidence_model),
    }
    model = build_radical_mapping(candidate_model, source)
    summary = model["summary"]
    assert summary["candidate_rows"] == 6314
    assert summary["ready_candidate_rows"] + summary["blocked_candidate_rows"] == 6314
    assert summary["blocked_radical_names"] > 0
    assert any(record["radical"] == "阝" for record in model["blocked_radicals"])
