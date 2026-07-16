"""Tests for read-only legacy catalog workbook schema inspection."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.inspect_full_catalog_excel_schemas import (
    build_report,
    classify_headers,
    parse_dimension,
)


def write_minimal_xlsx(path: Path, sheet_name: str, headers: list[str], dimension: str) -> None:
    sheet_cells = []
    for index, header in enumerate(headers, start=1):
        column = ""
        value = index
        while value:
            value, remainder = divmod(value - 1, 26)
            column = chr(ord("A") + remainder) + column
        sheet_cells.append(f'<c r="{column}1" t="inlineStr"><is><t>{header}</t></is></c>')
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/>'
        "<sheetData><row r=\"1\">"
        + "".join(sheet_cells)
        + "</row></sheetData></worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    relationships_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def test_parse_dimension_reports_shape() -> None:
    assert parse_dimension("A1:Q97687") == {
        "raw": "A1:Q97687",
        "start_cell": "A1",
        "end_cell": "Q97687",
        "row_count": 97687,
        "column_count": 17,
    }


def test_classify_headers_finds_core_field_candidates() -> None:
    headers = ["汉字", "Unicode", "CNBE(Hex)", "部首区", "笔画数", "结构区", "结构名称"]
    classified = classify_headers(headers)
    assert classified["unicode_candidates"] == ["Unicode"]
    assert classified["character_candidates"] == ["汉字"]
    assert "CNBE(Hex)" in classified["cnbe_candidates"]
    assert "结构区" in classified["structure_candidates"]
    assert "笔画数" in classified["stroke_candidates"]
    assert "部首区" in classified["radical_candidates"]


def test_build_report_marks_invalid_workbook_for_review(tmp_path: Path) -> None:
    valid = tmp_path / "valid.xlsx"
    invalid = tmp_path / "invalid.xlsx"
    write_minimal_xlsx(
        valid,
        "CNBE完整编码表v4_fixed",
        ["序号", "汉字", "Unicode", "CNBE(Hex)", "部首区", "笔画数", "结构区"],
        "A1:G3",
    )
    invalid.write_text("\r\n", encoding="utf-8")

    report = build_report([valid, invalid])
    assert report["summary"]["status"] == "REVIEW"
    assert report["comparison"]["valid_workbook_count"] == 1
    assert report["comparison"]["invalid_workbooks"][0]["path"].endswith("invalid.xlsx")
    assert report["workbooks"][0]["sheets"][0]["dimension"]["column_count"] == 7
    json.dumps(report, ensure_ascii=False)

