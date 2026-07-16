#!/usr/bin/env python3
"""Read fixed sample rows from the v4_fixed legacy CNBE workbook."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from inspect_full_catalog_excel_schemas import (
        MAIN_NS,
        cell_text,
        classify_headers,
        load_shared_strings,
        parse_dimension,
        sha256_file,
        workbook_sheets,
    )
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.inspect_full_catalog_excel_schemas import (
        MAIN_NS,
        cell_text,
        classify_headers,
        load_shared_strings,
        parse_dimension,
        sha256_file,
        workbook_sheets,
    )

DEFAULT_SOURCE = Path("data/CNBE_编码目录_修复版_v4_fixed.xlsx")
DEFAULT_OUTPUT = Path("reports/full_catalog_v4_fixed_sample_rows.json")
EXPECTED_SHEET = "CNBE完整编码表v4_fixed"
HEADER_ROW = 1
SAMPLE_WINDOW = 5
CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


def column_to_number(column: str) -> int:
    result = 0
    for character in column:
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def column_index(cell_reference: str) -> int:
    match = CELL_REF_RE.match(cell_reference)
    if not match:
        raise ValueError(f"invalid cell reference: {cell_reference}")
    return column_to_number(match.group(1)) - 1


def parse_int(value: Any, base: int = 10) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, base)
    except ValueError:
        try:
            number = float(text)
        except ValueError:
            return None
        return int(number) if number.is_integer() else None


def read_row_values(
    archive: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
    target_rows: set[int],
) -> dict[int, list[str | None]]:
    rows: dict[int, list[str | None]] = {}
    max_target = max(target_rows)
    with archive.open(sheet_path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != f"{{{MAIN_NS}}}row":
                continue
            row_number = int(element.get("r", "0"))
            if row_number > max_target:
                break
            if row_number not in target_rows:
                element.clear()
                continue
            values: list[str | None] = []
            for cell in element.findall(f"{{{MAIN_NS}}}c"):
                index = column_index(cell.get("r", ""))
                if index >= len(values):
                    values.extend([None] * (index + 1 - len(values)))
                values[index] = cell_text(cell, shared_strings)
            rows[row_number] = values
            element.clear()
    return rows


def sample_row_numbers(last_row: int) -> list[int]:
    first = list(range(2, 2 + SAMPLE_WINDOW))
    middle_start = max(2, (last_row // 2) - (SAMPLE_WINDOW // 2))
    middle = list(range(middle_start, middle_start + SAMPLE_WINDOW))
    tail_start = max(2, last_row - SAMPLE_WINDOW + 1)
    tail = list(range(tail_start, last_row + 1))
    return sorted(set(first + middle + tail))


def map_headers(headers: list[str | None]) -> dict[str, int]:
    return {
        str(header): index
        for index, header in enumerate(headers)
        if header not in {None, ""}
    }


def row_value(values: list[str | None], positions: dict[str, int], name: str) -> str | None:
    index = positions[name]
    return values[index] if index < len(values) else None


def inspect_record(worksheet_row: int, values: list[str | None], positions: dict[str, int]) -> dict[str, Any]:
    record = {
        "worksheet_row": worksheet_row,
        "sequence": row_value(values, positions, "序号"),
        "char": row_value(values, positions, "汉字"),
        "unicode": row_value(values, positions, "Unicode"),
        "cnbe_hex": row_value(values, positions, "CNBE(Hex)"),
        "cnbe_dec": row_value(values, positions, "CNBE(Dec)"),
        "cnbe_bin": row_value(values, positions, "CNBE(Bin)"),
        "radical": row_value(values, positions, "部首区"),
        "strokes": row_value(values, positions, "笔画数"),
        "structure_code": row_value(values, positions, "结构区(v4)"),
        "structure_name": row_value(values, positions, "结构名称(v4)"),
        "index": row_value(values, positions, "字库索引"),
        "extension": row_value(values, positions, "扩展区"),
        "is_modern": row_value(values, positions, "是否现代"),
        "space_label": row_value(values, positions, "Space_Label"),
        "category_label": row_value(values, positions, "Category_Label"),
        "time_label": row_value(values, positions, "Time_Label"),
        "v3_structure_note": row_value(values, positions, "备注(v3原结构)"),
    }
    char = record["char"]
    unicode_text = record["unicode"]
    codepoint = None
    unicode_matches_char = False
    if isinstance(unicode_text, str) and unicode_text.startswith("U+"):
        try:
            codepoint = int(unicode_text[2:], 16)
        except ValueError:
            codepoint = None
    if isinstance(char, str) and len(char) == 1 and codepoint is not None:
        unicode_matches_char = ord(char) == codepoint

    cnbe_hex = parse_int(record["cnbe_hex"], 16)
    cnbe_dec = parse_int(record["cnbe_dec"], 10)
    cnbe_bin = parse_int(record["cnbe_bin"], 2)
    cnbe_forms_match = cnbe_hex is not None and cnbe_hex == cnbe_dec == cnbe_bin

    field_numbers = {
        "radical": parse_int(record["radical"]),
        "strokes": parse_int(record["strokes"]),
        "structure_code": parse_int(record["structure_code"]),
        "index": parse_int(record["index"]),
        "extension": parse_int(record["extension"]),
    }
    if all(value is not None for value in field_numbers.values()):
        recomputed = (
            (field_numbers["radical"] << 24)
            | (field_numbers["strokes"] << 19)
            | (field_numbers["structure_code"] << 15)
            | (field_numbers["index"] << 4)
            | field_numbers["extension"]
        )
    else:
        recomputed = None

    record["checks"] = {
        "unicode_matches_char": unicode_matches_char,
        "cnbe_forms_match": cnbe_forms_match,
        "cnbe_bitfields_recompute": recomputed == cnbe_dec if recomputed is not None else False,
    }
    return record


def inspect_source(source: Path) -> dict[str, Any]:
    with zipfile.ZipFile(source) as archive:
        shared_strings = load_shared_strings(archive)
        sheet = next((item for item in workbook_sheets(archive) if item["name"] == EXPECTED_SHEET), None)
        if sheet is None:
            raise ValueError(f"required worksheet not found: {EXPECTED_SHEET}")
        root = ET.fromstring(archive.read(sheet["path"]))
        dimension = parse_dimension(root.find(f"{{{MAIN_NS}}}dimension").get("ref"))
        last_row = int(dimension["row_count"] or 0)
        targets = set(sample_row_numbers(last_row))
        targets.add(HEADER_ROW)
        rows = read_row_values(archive, sheet["path"], shared_strings, targets)

    headers = rows[HEADER_ROW]
    header_map = map_headers(headers)
    sample_rows = [
        inspect_record(row_number, rows[row_number], header_map)
        for row_number in sorted(targets - {HEADER_ROW})
        if row_number in rows
    ]
    failed = [
        {
            "worksheet_row": row["worksheet_row"],
            "checks": row["checks"],
        }
        for row in sample_rows
        if not all(row["checks"].values())
    ]
    return {
        "source": {
            "path": str(source),
            "sha256": sha256_file(source),
            "worksheet": EXPECTED_SHEET,
            "dimension": dimension,
        },
        "header": {
            "row_number": HEADER_ROW,
            "columns": headers,
            "field_candidates": classify_headers(headers),
        },
        "sample_plan": {
            "strategy": "first_middle_last_fixed_windows",
            "window_size": SAMPLE_WINDOW,
            "worksheet_rows": [row for row in sorted(targets) if row != HEADER_ROW],
        },
        "sample_rows": sample_rows,
        "summary": {
            "status": "PASS" if not failed else "REVIEW",
            "sample_count": len(sample_rows),
            "unicode_match_failures": sum(not row["checks"]["unicode_matches_char"] for row in sample_rows),
            "cnbe_form_failures": sum(not row["checks"]["cnbe_forms_match"] for row in sample_rows),
            "cnbe_bitfield_failures": sum(
                not row["checks"]["cnbe_bitfields_recompute"] for row in sample_rows
            ),
            "failed_samples": failed,
        },
    }


def build_report(source: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_v4_fixed_sample_rows",
        "authority_boundary": {
            "scope": "fixed_sample_rows_only",
            "does_not_validate_full_workbook": True,
            "does_not_reconstruct_encoding": True,
            "does_not_modify_data_files": True,
            "next_gate": "full_unicode_identity_gate",
        },
        **inspect_source(source),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    report = build_report(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    print(f"Status: {report['summary']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

