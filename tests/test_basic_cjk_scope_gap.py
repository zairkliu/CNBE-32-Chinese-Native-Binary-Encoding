"""Tests for Basic CJK coverage and mapping-lineage comparison."""

from __future__ import annotations

from scripts.analyze_basic_cjk_scope_gap import compare_catalogs, contiguous_ranges


def make_full_row(codepoint: int, cnbe: int, radical: int = 1) -> dict:
    return {
        "unicode": codepoint,
        "char": chr(codepoint),
        "cnbe": cnbe,
        "radical": radical,
        "strokes": 2,
        "struct_type": 0,
        "struct_name": "独体结构",
        "idx": codepoint - 0x4E00,
        "ext": 0,
        "source_sequence": codepoint - 0x4E00,
    }


def make_sdk_row(codepoint: int, cnbe: int, radical: int = 1) -> dict:
    row = make_full_row(codepoint, cnbe, radical)
    row.pop("ext")
    row.pop("source_sequence")
    return row


def test_contiguous_ranges_empty() -> None:
    assert contiguous_ranges([]) == []


def test_contiguous_ranges_combines_runs() -> None:
    assert contiguous_ranges([0x4E00, 0x4E01, 0x4E03, 0x4E04]) == [
        {"start": "U+4E00", "end": "U+4E01", "count": 2},
        {"start": "U+4E03", "end": "U+4E04", "count": 2},
    ]


def test_compare_catalogs_separates_coverage_and_mapping() -> None:
    full = {
        0x4E00: make_full_row(0x4E00, 100),
        0x4E01: make_full_row(0x4E01, 101),
        0x4E02: make_full_row(0x4E02, 102),
    }
    sdk = {
        0x4E00: make_sdk_row(0x4E00, 100),
        0x4E01: make_sdk_row(0x4E01, 999),
    }
    result = compare_catalogs(full, sdk)
    assert result["counts"] == {
        "full_basic_rows": 3,
        "sdk_rows": 2,
        "shared_unicode_rows": 2,
        "missing_from_sdk_rows": 1,
        "sdk_only_rows": 0,
        "exact_all_compared_fields_rows": 1,
        "exact_numeric_mapping_rows": 1,
    }
    assert result["field_mismatch_counts"]["cnbe"] == 1
    assert result["exact_numeric_mapping_codepoints"] == [
        {"unicode": "U+4E00", "char": "一"}
    ]
    assert result["ranges"]["missing_from_sdk"] == [
        {"start": "U+4E02", "end": "U+4E02", "count": 1}
    ]


def test_compare_catalogs_detects_sdk_only_rows() -> None:
    full = {0x4E00: make_full_row(0x4E00, 100)}
    sdk = {
        0x4E00: make_sdk_row(0x4E00, 100),
        0x4E01: make_sdk_row(0x4E01, 101),
    }
    result = compare_catalogs(full, sdk)
    assert result["counts"]["sdk_only_rows"] == 1
    assert result["sdk_only"] == [
        {"unicode": "U+4E01", "codepoint": 0x4E01, "char": "丁"}
    ]


def test_compare_catalogs_reports_field_level_differences() -> None:
    full = {0x4E00: make_full_row(0x4E00, 100, radical=1)}
    sdk = {0x4E00: make_sdk_row(0x4E00, 200, radical=2)}
    result = compare_catalogs(full, sdk)
    sample = result["mismatch_samples"][0]
    assert sample["unicode"] == "U+4E00"
    assert sample["differences"]["cnbe"] == {"sdk": 200, "full_catalog": 100}
    assert sample["differences"]["radical"] == {"sdk": 2, "full_catalog": 1}
