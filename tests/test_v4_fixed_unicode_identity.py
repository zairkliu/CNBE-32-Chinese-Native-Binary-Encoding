"""Tests for the v4_fixed Unicode identity gate."""

from __future__ import annotations

from scripts.audit_v4_fixed_unicode_identity import inspect_identity_row, parse_unicode_label

HEADERS = {
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
}


def row(char: str = "一", unicode_label: str = "U+4E00") -> list[str]:
    cnbe = (1 << 24) | (2 << 19) | (3 << 15) | (4 << 4) | 5
    return [
        "1",
        char,
        unicode_label,
        f"{cnbe:08X}",
        str(cnbe),
        f"{cnbe:032b}",
        "1",
        "2",
        "3",
        "上下",
        "4",
        "5",
    ]


def test_parse_unicode_label_accepts_wide_codepoints() -> None:
    assert parse_unicode_label("U+20000") == 0x20000


def test_inspect_identity_row_accepts_matching_record() -> None:
    identity, issues = inspect_identity_row(2, row(), HEADERS)
    assert issues == []
    assert identity["char"] == "一"
    assert identity["codepoint"] == 0x4E00


def test_inspect_identity_row_reports_unicode_mismatch() -> None:
    _, issues = inspect_identity_row(2, row(char="丁", unicode_label="U+4E00"), HEADERS)
    assert "unicode_char_mismatch" in issues

