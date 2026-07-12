"""Tests for the recovered full-catalog structure classifier."""

from __future__ import annotations

import pytest

from scripts.audit_full_catalog_structure import (
    SPECIAL_RADICAL_STRUCTURES,
    STRUCTURE_NAMES,
    audit_records,
    classify_structure,
)


def record(radical: int, structure: int, name: str) -> tuple[object, ...]:
    return (0x4E00, "一", 0, radical, 1, structure, name, 0)


@pytest.mark.parametrize(
    ("radical", "expected"),
    [
        (1, 0),
        (9, 1),
        (14, 3),
        (20, 5),
        (62, 6),
        (162, 7),
        (169, 8),
        (22, 9),
        (31, 10),
        (10, 1),
    ],
)
def test_classify_structure(radical: int, expected: int) -> None:
    assert classify_structure(radical) == expected


def test_exactly_nineteen_special_overrides() -> None:
    assert len(SPECIAL_RADICAL_STRUCTURES) == 19


def test_rejects_out_of_range_radical() -> None:
    with pytest.raises(ValueError, match="1..214"):
        classify_structure(0)


def test_audit_records_accepts_matching_values() -> None:
    rows = [
        record(radical, structure, STRUCTURE_NAMES[structure])
        for radical, structure in [(1, 0), (9, 1), (14, 3), (31, 10)]
    ]
    audit = audit_records(rows)
    assert audit["structure_code_mismatches"] == 0
    assert audit["structure_name_mismatches"] == 0
    assert audit["radicals_with_multiple_observed_structures"] == {}


def test_audit_records_reports_code_and_name_mismatches() -> None:
    rows = [record(1, 1, "左右结构")]
    audit = audit_records(rows)
    assert audit["structure_code_mismatches"] == 1
    assert audit["structure_name_mismatches"] == 1
    assert audit["mismatch_samples"][0]["expected_structure"] == 0


def test_audit_records_detects_conflicting_radical_labels() -> None:
    rows = [record(9, 1, "左右结构"), record(9, 3, "上下结构")]
    audit = audit_records(rows)
    assert audit["radicals_with_multiple_observed_structures"] == {"9": [1, 3]}
