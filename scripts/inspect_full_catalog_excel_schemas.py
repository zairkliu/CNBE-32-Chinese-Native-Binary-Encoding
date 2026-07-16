#!/usr/bin/env python3
"""Inspect legacy CNBE catalog workbook schemas without modifying data files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from posixpath import join, normpath
from typing import Any

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")
DIMENSION_RE = re.compile(r"^([A-Z]+)([0-9]+)(?::([A-Z]+)([0-9]+))?$")

DEFAULT_WORKBOOKS = [
    Path("data/CNBE_编码目录_修复版_v3.xlsx"),
    Path("data/CNBE_编码目录_修复版_v4.xlsx"),
    Path("data/CNBE_编码目录_修复版_v4_fixed.xlsx"),
]
DEFAULT_OUTPUT = Path("reports/full_catalog_excel_schema_comparison.json")

UNICODE_TERMS = ("unicode", "统一码", "码位", "codepoint", "code point")
CHARACTER_TERMS = ("汉字", "字符", "char", "character")
CNBE_TERMS = ("cnbe", "编码")
STRUCTURE_TERMS = ("结构", "structure", "struct")
STROKE_TERMS = ("笔画", "stroke")
RADICAL_TERMS = ("部首", "radical", "radix")
EXTENSION_TERMS = ("扩展", "extension", "ext")
INDEX_TERMS = ("索引", "index", "idx")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def column_to_number(column: str) -> int:
    result = 0
    for character in column:
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def parse_dimension(reference: str | None) -> dict[str, Any]:
    if not reference:
        return {
            "raw": None,
            "start_cell": None,
            "end_cell": None,
            "row_count": None,
            "column_count": None,
        }
    match = DIMENSION_RE.match(reference)
    if not match:
        return {
            "raw": reference,
            "start_cell": None,
            "end_cell": None,
            "row_count": None,
            "column_count": None,
            "parse_error": "unsupported_dimension_reference",
        }
    start_column, start_row, end_column, end_row = match.groups()
    end_column = end_column or start_column
    end_row = end_row or start_row
    row_count = int(end_row) - int(start_row) + 1
    column_count = column_to_number(end_column) - column_to_number(start_column) + 1
    return {
        "raw": reference,
        "start_cell": f"{start_column}{start_row}",
        "end_cell": f"{end_column}{end_row}",
        "row_count": row_count,
        "column_count": column_count,
    }


def column_index(cell_reference: str) -> int:
    match = CELL_REF_RE.match(cell_reference)
    if not match:
        raise ValueError(f"invalid cell reference: {cell_reference}")
    return column_to_number(match.group(1)) - 1


def normalize_workbook_target(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return normpath(join("xl", target))


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str | None:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        value = "".join(cell.itertext()).strip()
        return value or None

    value = cell.findtext(f"{{{MAIN_NS}}}v")
    if value is None:
        return None
    if cell_type == "s":
        try:
            return shared_strings[int(value)].strip() or None
        except (ValueError, IndexError):
            return None
    return str(value).strip() or None


def load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall(f"{{{MAIN_NS}}}si"):
        text = "".join(item.itertext()).strip()
        values.append(text)
    return values


def workbook_sheets(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relation.get("Id"): relation.get("Target", "")
        for relation in relationships.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    sheets = []
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        relation_id = sheet.get(f"{{{DOC_REL_NS}}}id", "")
        target = targets.get(relation_id, "")
        sheets.append(
            {
                "name": sheet.get("name", ""),
                "path": normalize_workbook_target(target),
            }
        )
    return sheets


def first_non_empty_row(
    archive: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
    max_scan_rows: int = 20,
) -> dict[str, Any]:
    with archive.open(sheet_path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != f"{{{MAIN_NS}}}row":
                continue
            row_number = int(element.get("r", "0"))
            values: list[str | None] = []
            for cell in element.findall(f"{{{MAIN_NS}}}c"):
                reference = cell.get("r", "")
                index = column_index(reference)
                if index >= len(values):
                    values.extend([None] * (index + 1 - len(values)))
                values[index] = cell_text(cell, shared_strings)
            element.clear()
            if row_number > max_scan_rows:
                break
            compact = [value for value in values if value not in {None, ""}]
            if compact:
                return {"row_number": row_number, "values": values}
    return {"row_number": None, "values": []}


def classify_headers(headers: list[str | None]) -> dict[str, Any]:
    names = [str(value).strip() for value in headers if value not in {None, ""}]
    lowered = {name: name.lower() for name in names}
    counter = Counter(names)
    duplicate_headers = sorted(name for name, count in counter.items() if count > 1)

    def matches(terms: tuple[str, ...]) -> list[str]:
        result = []
        for name, lower in lowered.items():
            if any(term.lower() in lower or term in name for term in terms):
                result.append(name)
        return result

    return {
        "header_count": len(names),
        "headers": names,
        "duplicate_headers": duplicate_headers,
        "unicode_candidates": matches(UNICODE_TERMS),
        "character_candidates": matches(CHARACTER_TERMS),
        "cnbe_candidates": matches(CNBE_TERMS),
        "structure_candidates": matches(STRUCTURE_TERMS),
        "stroke_candidates": matches(STROKE_TERMS),
        "radical_candidates": matches(RADICAL_TERMS),
        "extension_candidates": matches(EXTENSION_TERMS),
        "index_candidates": matches(INDEX_TERMS),
    }


def inspect_sheet(
    archive: zipfile.ZipFile,
    sheet: dict[str, str],
    shared_strings: list[str],
) -> dict[str, Any]:
    root = ET.fromstring(archive.read(sheet["path"]))
    dimension = root.find(f"{{{MAIN_NS}}}dimension")
    dimension_info = parse_dimension(dimension.get("ref") if dimension is not None else None)
    header = first_non_empty_row(archive, sheet["path"], shared_strings)
    header_info = classify_headers(header["values"])
    return {
        "name": sheet["name"],
        "path": sheet["path"],
        "dimension": dimension_info,
        "first_non_empty_row": header["row_number"],
        "header": header_info,
    }


def inspect_workbook(path: Path) -> dict[str, Any]:
    base: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
    }
    if not path.exists():
        return {**base, "status": "MISSING", "sheets": []}
    base["sha256"] = sha256_file(path)
    if not zipfile.is_zipfile(path):
        return {
            **base,
            "status": "INVALID_XLSX",
            "error": "not_a_zip_file",
            "sheets": [],
        }
    with zipfile.ZipFile(path) as archive:
        shared_strings = load_shared_strings(archive)
        sheets = workbook_sheets(archive)
        inspected = [inspect_sheet(archive, sheet, shared_strings) for sheet in sheets]
    return {
        **base,
        "status": "READ_ONLY_SCHEMA_INSPECTED",
        "sheet_count": len(inspected),
        "sheets": inspected,
    }


def compare_workbooks(workbooks: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [item for item in workbooks if item["status"] == "READ_ONLY_SCHEMA_INSPECTED"]
    primary_sheets = [item["sheets"][0] for item in valid if item.get("sheets")]
    row_counts = {
        item["path"]: item["sheets"][0]["dimension"]["row_count"]
        for item in valid
        if item.get("sheets")
    }
    column_counts = {
        item["path"]: item["sheets"][0]["dimension"]["column_count"]
        for item in valid
        if item.get("sheets")
    }
    header_sets = {
        item["path"]: item["sheets"][0]["header"]["headers"]
        for item in valid
        if item.get("sheets")
    }
    required_field_presence = {}
    for item in valid:
        if not item.get("sheets"):
            continue
        header = item["sheets"][0]["header"]
        required_field_presence[item["path"]] = {
            "unicode": bool(header["unicode_candidates"]),
            "character": bool(header["character_candidates"]),
            "cnbe": bool(header["cnbe_candidates"]),
            "structure": bool(header["structure_candidates"]),
            "stroke": bool(header["stroke_candidates"]),
            "radical": bool(header["radical_candidates"]),
        }
    return {
        "valid_workbook_count": len(valid),
        "invalid_workbooks": [
            {"path": item["path"], "status": item["status"], "error": item.get("error")}
            for item in workbooks
            if item["status"] != "READ_ONLY_SCHEMA_INSPECTED"
        ],
        "primary_sheet_row_counts": row_counts,
        "primary_sheet_column_counts": column_counts,
        "primary_sheet_headers": header_sets,
        "required_field_presence": required_field_presence,
        "row_count_range": {
            "min": min(row_counts.values()) if row_counts else None,
            "max": max(row_counts.values()) if row_counts else None,
        },
        "column_count_range": {
            "min": min(column_counts.values()) if column_counts else None,
            "max": max(column_counts.values()) if column_counts else None,
        },
        "primary_sheet_names": [sheet["name"] for sheet in primary_sheets],
    }


def build_report(paths: list[Path]) -> dict[str, Any]:
    workbooks = [inspect_workbook(path) for path in paths]
    comparison = compare_workbooks(workbooks)
    blockers = []
    if comparison["invalid_workbooks"]:
        blockers.append("invalid_or_placeholder_workbooks_present")
    if comparison["valid_workbook_count"] < 3:
        blockers.append("less_than_three_valid_legacy_catalog_workbooks")
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_excel_schema_inspection",
        "source_paths": [str(path) for path in paths],
        "authority_boundary": {
            "scope": "schema_only",
            "does_not_validate_rows": True,
            "does_not_reconstruct_encoding": True,
            "does_not_modify_data_files": True,
            "release_gate": "schema comparison precedes Unicode and GF0017 row gates",
        },
        "summary": {
            "status": "PASS" if not blockers else "REVIEW",
            "workbooks_requested": len(paths),
            "valid_workbooks": comparison["valid_workbook_count"],
            "blockers_or_review_items": blockers,
        },
        "comparison": comparison,
        "workbooks": workbooks,
        "next_gates": [
            "select first release reconstruction input",
            "extract full header-to-field mapping",
            "run Unicode identity sampling",
            "run full Unicode identity gate",
            "run source evidence and GF0017 gates",
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workbooks",
        nargs="*",
        type=Path,
        default=DEFAULT_WORKBOOKS,
        help="Legacy CNBE catalog workbooks to inspect.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSON report path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    report = build_report(args.workbooks)
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

