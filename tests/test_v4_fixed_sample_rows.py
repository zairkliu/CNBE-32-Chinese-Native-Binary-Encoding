"""Tests for v4_fixed sample-row inspection helpers."""

from __future__ import annotations

from scripts.inspect_v4_fixed_sample_rows import inspect_record, sample_row_numbers


def test_sample_row_numbers_cover_first_middle_and_tail() -> None:
    assert sample_row_numbers(100) == [2, 3, 4, 5, 6, 48, 49, 50, 51, 52, 96, 97, 98, 99, 100]


def test_inspect_record_checks_unicode_and_cnbe_consistency() -> None:
    headers = {
        "序号": 0,
        "汉字": 1,
        "Unicode": 2,
        "CNBE(Hex)": 3,
        "CNBE(Dec)": 4,
        "CNBE(Bin)": 5,
        "部首区": 6,
        "笔画数": 7,
        "结构区(v4)": 8,
        "结构名称(v4)": 9,
        "字库索引": 10,
        "扩展区": 11,
        "是否现代": 12,
        "Space_Label": 13,
        "Category_Label": 14,
        "Time_Label": 15,
        "备注(v3原结构)": 16,
    }
    cnbe = (1 << 24) | (2 << 19) | (3 << 15) | (4 << 4) | 5
    values = [
        "1",
        "一",
        "U+4E00",
        f"{cnbe:08X}",
        str(cnbe),
        f"{cnbe:032b}",
        "1",
        "2",
        "3",
        "上下",
        "4",
        "5",
        "是",
        "Basic",
        "CJK",
        "modern",
        "v3",
    ]
    inspected = inspect_record(2, values, headers)
    assert inspected["checks"] == {
        "unicode_matches_char": True,
        "cnbe_forms_match": True,
        "cnbe_bitfields_recompute": True,
    }
