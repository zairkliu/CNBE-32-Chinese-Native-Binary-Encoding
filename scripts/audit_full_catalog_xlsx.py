#!/usr/bin/env python3
"""Read-only quality audit for the CNBE-32 full catalog workbook."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_DATA_ROWS = 97_686
EXPECTED_SHEET = "CNBE完整编码表"
REQUIRED_COLUMNS = [
    "序号",
    "汉字",
    "Unicode",
    "CNBE(Hex)",
    "CNBE(Dec)",
    "CNBE(Bin)",
    "部首区",
    "笔画数",
    "结构区",
    "结构名称",
    "字库区索引",
    "扩展区",
]
OPTIONAL_COLUMNS = ["GB 18030-2022兼容性", "备注说明"]

FIELD_LIMITS = {
    "部首区": (0, 255),
    "笔画数": (0, 31),
    "结构区": (0, 15),
    "字库区索引": (0, 2047),
    "扩展区": (0, 15),
}
SHIFTS = {
    "部首区": 24,
    "笔画数": 19,
    "结构区": 15,
    "字库区索引": 4,
    "扩展区": 0,
}
UNICODE_BLOCKS = [
    ("CJK Unified Ideographs Extension A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("CJK Unified Ideographs Extension B", 0x20000, 0x2A6DF),
    ("CJK Unified Ideographs Extension C", 0x2A700, 0x2B73F),
    ("CJK Unified Ideographs Extension D", 0x2B740, 0x2B81F),
    ("CJK Unified Ideographs Extension E", 0x2B820, 0x2CEAF),
    ("CJK Unified Ideographs Extension F", 0x2CEB0, 0x2EBEF),
    ("CJK Unified Ideographs Extension I", 0x2EBF0, 0x2EE5F),
    ("CJK Unified Ideographs Extension G", 0x30000, 0x3134F),
    ("CJK Unified Ideographs Extension H", 0x31350, 0x323AF),
]

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CELL_REF_RE = re.compile(r"([A-Z]+)")
SAMPLE_LIMIT = 20


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def column_number(cell_reference: str) -> int:
    match = CELL_REF_RE.match(cell_reference)
    if not match:
        raise ValueError(f"invalid cell reference: {cell_reference}")
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def cell_value(cell: ET.Element) -> Any:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(cell.itertext())

    value = cell.findtext(f"{{{MAIN_NS}}}v")
    if value is None:
        return None
    if cell_type in {"str", "s"}:
        return value
    if cell_type == "b":
        return value == "1"
    try:
        number = float(value)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number


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
        if not target.startswith("/"):
            target = f"xl/{target}"
        sheets.append({"name": sheet.get("name", ""), "path": target.lstrip("/")})
    return sheets


def iter_sheet_rows(archive: zipfile.ZipFile, sheet_path: str) -> Iterator[tuple[int, list[Any]]]:
    with archive.open(sheet_path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != f"{{{MAIN_NS}}}row":
                continue
            values: list[Any] = []
            for cell in element.findall(f"{{{MAIN_NS}}}c"):
                index = column_number(cell.get("r", ""))
                if index >= len(values):
                    values.extend([None] * (index + 1 - len(values)))
                values[index] = cell_value(cell)
            yield int(element.get("r", "0")), values
            element.clear()


def parse_integer(value: Any, base: int = 10) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not an integer field")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        return int(value.strip(), base)
    raise ValueError(f"cannot parse integer from {value!r}")


def unicode_block(codepoint: int) -> str:
    for name, start, end in UNICODE_BLOCKS:
        if start <= codepoint <= end:
            return name
    return "Other"


class Audit:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}
        self.samples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_sample(self, category: str, row: int, detail: str) -> None:
        if len(self.samples[category]) < SAMPLE_LIMIT:
            self.samples[category].append({"worksheet_row": row, "detail": detail})

    def check(self, name: str, passed: bool, evidence: dict[str, Any], severity: str = "critical") -> None:
        self.checks[name] = {
            "status": "PASS" if passed else "FAIL",
            "severity_if_failed": severity,
            "evidence": evidence,
        }


def inspect_existing_sdk_database(repo_root: Path) -> dict[str, Any]:
    database_path = repo_root / "data" / "cnbe32.db"
    if not database_path.exists():
        return {"status": "NOT_FOUND", "path": "data/cnbe32.db"}
    uri = f"file:{database_path}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM cnbe32").fetchone()[0]
        bounds = connection.execute("SELECT MIN(unicode), MAX(unicode) FROM cnbe32").fetchone()
    return {
        "status": "READ_ONLY_INSPECTED",
        "path": "data/cnbe32.db",
        "row_count": row_count,
        "unicode_min": f"U+{bounds[0]:04X}",
        "unicode_max": f"U+{bounds[1]:04X}",
    }


def audit_catalog(source: Path, repo_root: Path) -> dict[str, Any]:
    audit = Audit()
    with zipfile.ZipFile(source) as archive:
        sheets = workbook_sheets(archive)
        sheet = next((item for item in sheets if item["name"] == EXPECTED_SHEET), None)
        audit.check(
            "required_worksheet",
            sheet is not None,
            {"required": EXPECTED_SHEET, "available": [item["name"] for item in sheets]},
        )
        if sheet is None:
            return finish_report(source, repo_root, audit, {}, 0, 0)

        rows = iter_sheet_rows(archive, sheet["path"])
        header_row_number, headers = next(rows)
        header_positions = {str(name): index for index, name in enumerate(headers) if name is not None}
        missing_columns = [name for name in REQUIRED_COLUMNS if name not in header_positions]
        audit.check(
            "required_columns",
            not missing_columns,
            {
                "header_row": header_row_number,
                "required": REQUIRED_COLUMNS,
                "missing": missing_columns,
                "optional_present": [name for name in OPTIONAL_COLUMNS if name in header_positions],
            },
        )
        if missing_columns:
            return finish_report(source, repo_root, audit, {}, 0, 0)

        counters: Counter[str] = Counter()
        block_counts: Counter[str] = Counter()
        structure_counts: Counter[str] = Counter()
        optional_populated: Counter[str] = Counter()
        range_min: dict[str, int] = {}
        range_max: dict[str, int] = {}
        seen_characters: dict[str, int] = {}
        seen_unicodes: dict[int, int] = {}
        seen_cnbe: dict[int, int] = {}
        structure_code_to_names: dict[int, set[str]] = defaultdict(set)
        structure_name_to_codes: dict[str, set[int]] = defaultdict(set)

        def value(record: list[Any], column: str) -> Any:
            position = header_positions[column]
            return record[position] if position < len(record) else None

        for worksheet_row, record in rows:
            unicode_text = value(record, "Unicode")
            if not isinstance(unicode_text, str) or not unicode_text.startswith("U+"):
                if any(item not in {None, ""} for item in record):
                    counters["non_data_rows"] += 1
                    audit.add_sample("non_data_rows", worksheet_row, str(record[0])[:160])
                continue

            counters["data_rows"] += 1
            row_failed = False
            required_values = {column: value(record, column) for column in REQUIRED_COLUMNS}
            missing = [column for column, item in required_values.items() if item in {None, ""}]
            if missing:
                counters["rows_missing_required_values"] += 1
                audit.add_sample("missing_required_values", worksheet_row, ", ".join(missing))
                continue

            try:
                sequence = parse_integer(required_values["序号"])
                character = str(required_values["汉字"])
                codepoint = int(unicode_text[2:], 16)
                cnbe_hex = parse_integer(required_values["CNBE(Hex)"], 16)
                cnbe_dec = parse_integer(required_values["CNBE(Dec)"])
                cnbe_bin_text = str(required_values["CNBE(Bin)"]).strip()
                cnbe_bin = int(cnbe_bin_text, 2)
                fields = {name: parse_integer(required_values[name]) for name in FIELD_LIMITS}
                structure_name = str(required_values["结构名称"])
            except (TypeError, ValueError) as exc:
                counters["parse_errors"] += 1
                audit.add_sample("parse_errors", worksheet_row, str(exc))
                continue

            if sequence != counters["data_rows"] - 1:
                counters["sequence_errors"] += 1
                audit.add_sample("sequence_errors", worksheet_row, f"expected {counters['data_rows'] - 1}, got {sequence}")

            if len(character) != 1 or ord(character) != codepoint:
                counters["character_unicode_mismatches"] += 1
                audit.add_sample("character_unicode_mismatches", worksheet_row, f"{character!r} vs {unicode_text}")

            for unique_name, unique_value, seen in (
                ("duplicate_characters", character, seen_characters),
                ("duplicate_unicodes", codepoint, seen_unicodes),
                ("duplicate_cnbe_codes", cnbe_dec, seen_cnbe),
            ):
                if unique_value in seen:
                    counters[unique_name] += 1
                    audit.add_sample(unique_name, worksheet_row, f"first seen at row {seen[unique_value]}")
                else:
                    seen[unique_value] = worksheet_row

            if not (cnbe_hex == cnbe_dec == cnbe_bin):
                counters["cnbe_representation_mismatches"] += 1
                audit.add_sample(
                    "cnbe_representation_mismatches",
                    worksheet_row,
                    f"hex={cnbe_hex}, dec={cnbe_dec}, bin={cnbe_bin}",
                )
                row_failed = True
            if len(cnbe_bin_text) != 32 or set(cnbe_bin_text) - {"0", "1"}:
                counters["invalid_binary_width"] += 1
                audit.add_sample("invalid_binary_width", worksheet_row, cnbe_bin_text[:64])
                row_failed = True

            recomputed = sum(fields[name] << SHIFTS[name] for name in FIELD_LIMITS)
            if recomputed != cnbe_dec:
                counters["bitfield_recomputation_mismatches"] += 1
                audit.add_sample(
                    "bitfield_recomputation_mismatches",
                    worksheet_row,
                    f"stored={cnbe_dec}, recomputed={recomputed}",
                )
                row_failed = True

            for name, field_value in fields.items():
                minimum, maximum = FIELD_LIMITS[name]
                range_min[name] = min(range_min.get(name, field_value), field_value)
                range_max[name] = max(range_max.get(name, field_value), field_value)
                if not minimum <= field_value <= maximum:
                    counters["field_range_errors"] += 1
                    audit.add_sample("field_range_errors", worksheet_row, f"{name}={field_value}, allowed={minimum}..{maximum}")
                    row_failed = True

            structure_code = fields["结构区"]
            structure_code_to_names[structure_code].add(structure_name)
            structure_name_to_codes[structure_name].add(structure_code)
            structure_counts[structure_name] += 1
            block_counts[unicode_block(codepoint)] += 1
            for column in OPTIONAL_COLUMNS:
                if column in header_positions and value(record, column) not in {None, ""}:
                    optional_populated[column] += 1
            if row_failed:
                counters["rows_with_encoding_errors"] += 1

    inconsistent_codes = {
        str(code): sorted(names) for code, names in structure_code_to_names.items() if len(names) != 1
    }
    inconsistent_names = {
        name: sorted(codes) for name, codes in structure_name_to_codes.items() if len(codes) != 1
    }
    audit.check(
        "expected_row_count",
        counters["data_rows"] == EXPECTED_DATA_ROWS,
        {"expected": EXPECTED_DATA_ROWS, "actual": counters["data_rows"], "non_data_rows": counters["non_data_rows"]},
    )
    audit.check(
        "required_value_completeness",
        counters["rows_missing_required_values"] == 0,
        {"rows_missing_required_values": counters["rows_missing_required_values"]},
    )
    audit.check(
        "row_parseability",
        counters["parse_errors"] == 0,
        {"parse_errors": counters["parse_errors"]},
    )
    audit.check("sequence_continuity", counters["sequence_errors"] == 0, {"errors": counters["sequence_errors"]})
    audit.check(
        "character_unicode_consistency",
        counters["character_unicode_mismatches"] == 0,
        {"mismatches": counters["character_unicode_mismatches"]},
    )
    audit.check(
        "key_uniqueness",
        not any(counters[name] for name in ("duplicate_characters", "duplicate_unicodes", "duplicate_cnbe_codes")),
        {
            "unique_characters": len(seen_characters),
            "unique_unicodes": len(seen_unicodes),
            "unique_cnbe_codes": len(seen_cnbe),
            "duplicate_characters": counters["duplicate_characters"],
            "duplicate_unicodes": counters["duplicate_unicodes"],
            "duplicate_cnbe_codes": counters["duplicate_cnbe_codes"],
        },
    )
    audit.check(
        "cnbe_representation_consistency",
        counters["cnbe_representation_mismatches"] == 0 and counters["invalid_binary_width"] == 0,
        {
            "representation_mismatches": counters["cnbe_representation_mismatches"],
            "invalid_binary_width": counters["invalid_binary_width"],
        },
    )
    audit.check(
        "cnbe_bitfield_recomputation",
        counters["bitfield_recomputation_mismatches"] == 0,
        {"mismatches": counters["bitfield_recomputation_mismatches"], "formula": "R<<24 | S<<19 | G<<15 | I<<4 | E"},
    )
    audit.check(
        "field_ranges",
        counters["field_range_errors"] == 0,
        {
            "errors": counters["field_range_errors"],
            "observed": {name: {"min": range_min[name], "max": range_max[name]} for name in FIELD_LIMITS},
            "allowed": {name: {"min": limits[0], "max": limits[1]} for name, limits in FIELD_LIMITS.items()},
        },
    )
    audit.check(
        "structure_mapping_consistency",
        not inconsistent_codes and not inconsistent_names,
        {"code_to_multiple_names": inconsistent_codes, "name_to_multiple_codes": inconsistent_names},
        severity="high",
    )

    profile = {
        "data_rows": counters["data_rows"],
        "non_data_rows": counters["non_data_rows"],
        "unicode_block_distribution": dict(block_counts.most_common()),
        "structure_distribution": dict(structure_counts.most_common()),
        "optional_column_population": {
            column: {
                "populated_rows": optional_populated[column],
                "population_rate": optional_populated[column] / counters["data_rows"] if counters["data_rows"] else 0,
            }
            for column in OPTIONAL_COLUMNS
            if column in header_positions
        },
    }
    return finish_report(source, repo_root, audit, profile, counters["data_rows"], block_counts["CJK Unified Ideographs"])


def finish_report(
    source: Path,
    repo_root: Path,
    audit: Audit,
    profile: dict[str, Any],
    catalog_rows: int,
    catalog_basic_rows: int,
) -> dict[str, Any]:
    failed = [name for name, result in audit.checks.items() if result["status"] == "FAIL"]
    sdk_database = inspect_existing_sdk_database(repo_root)
    sdk_rows = sdk_database.get("row_count")
    scope_gap = catalog_basic_rows - sdk_rows if isinstance(sdk_rows, int) else None
    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_mode": "read_only",
        "source": {
            "file_name": source.name,
            "size_bytes": source.stat().st_size,
            "sha256": sha256_file(source),
            "expected_data_rows": EXPECTED_DATA_ROWS,
        },
        "summary": {
            "status": "PASS" if not failed else "FAIL",
            "catalog_rows": catalog_rows,
            "checks_passed": len(audit.checks) - len(failed),
            "checks_failed": len(failed),
            "failed_checks": failed,
            "sqlite_build_gate": "GO" if not failed else "NO_GO",
        },
        "checks": audit.checks,
        "profile": profile,
        "sample_issues": dict(audit.samples),
        "existing_sdk_scope": {
            "database": sdk_database,
            "catalog_basic_cjk_rows": catalog_basic_rows,
            "basic_cjk_row_difference": scope_gap,
            "interpretation": (
                "The full catalog is a separate data product. Do not replace the packaged SDK database until the "
                "Basic CJK scope difference and compatibility contract are resolved."
            ),
        },
        "next_step": (
            "Implement a deterministic full-catalog SQLite builder with a separate output path, transactional writes, "
            "schema/version metadata, indexes, and post-build reconciliation against this report."
            if not failed
            else "Resolve failed audit checks before implementing the full-catalog SQLite builder."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the source .xlsx catalog")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/full_catalog_feasibility.json"),
        help="JSON report path (default: reports/full_catalog_feasibility.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    repo_root = Path(__file__).resolve().parent.parent

    if not source.is_file():
        print(f"AUDIT ERROR: source file not found: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() != ".xlsx":
        print(f"AUDIT ERROR: source must be an .xlsx file: {source}", file=sys.stderr)
        return 2

    try:
        report = audit_catalog(source, repo_root)
    except (ET.ParseError, KeyError, OSError, zipfile.BadZipFile) as exc:
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    status = report["summary"]["status"]
    print(f"FULL CATALOG AUDIT {status}: {report['summary']['catalog_rows']:,} rows")
    print(f"Report: {output}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
