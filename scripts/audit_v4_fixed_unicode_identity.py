#!/usr/bin/env python3
"""Run a read-only Unicode identity gate over the v4_fixed CNBE workbook."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from inspect_full_catalog_excel_schemas import (
        MAIN_NS,
        cell_text,
        load_shared_strings,
        parse_dimension,
        sha256_file,
        workbook_sheets,
    )
    from inspect_v4_fixed_sample_rows import column_index, map_headers, parse_int, row_value
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.inspect_full_catalog_excel_schemas import (
        MAIN_NS,
        cell_text,
        load_shared_strings,
        parse_dimension,
        sha256_file,
        workbook_sheets,
    )
    from scripts.inspect_v4_fixed_sample_rows import column_index, map_headers, parse_int, row_value

DEFAULT_SOURCE = Path("data/CNBE_编码目录_修复版_v4_fixed.xlsx")
DEFAULT_OUTPUT = Path("reports/full_catalog_v4_fixed_unicode_identity.json")
EXPECTED_SHEET = "CNBE完整编码表v4_fixed"
EXPECTED_DATA_ROWS = 97_686
HEADER_ROW = 1
SAMPLE_LIMIT = 20
CNBE32_MAX = 2**32 - 1
REQUIRED_COLUMNS = [
    "序号",
    "汉字",
    "Unicode",
    "CNBE(Hex)",
    "CNBE(Dec)",
    "CNBE(Bin)",
    "部首区",
    "笔画数",
    "结构区(v4)",
    "结构名称(v4)",
    "字库索引",
    "扩展区",
]
UNICODE_RE = re.compile(r"^U\+[0-9A-Fa-f]{4,6}$")


def row_values(element: ET.Element, shared_strings: list[str]) -> list[str | None]:
    values: list[str | None] = []
    for cell in element.findall(f"{{{MAIN_NS}}}c"):
        index = column_index(cell.get("r", ""))
        if index >= len(values):
            values.extend([None] * (index + 1 - len(values)))
        values[index] = cell_text(cell, shared_strings)
    return values


def append_sample(samples: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if len(samples) < SAMPLE_LIMIT:
        samples.append(item)


def parse_unicode_label(value: str | None) -> int | None:
    if not isinstance(value, str) or not UNICODE_RE.match(value):
        return None
    try:
        return int(value[2:], 16)
    except ValueError:
        return None


def inspect_identity_row(
    worksheet_row: int,
    values: list[str | None],
    positions: dict[str, int],
) -> tuple[dict[str, Any], list[str]]:
    sequence = parse_int(row_value(values, positions, "序号"))
    char = row_value(values, positions, "汉字")
    unicode_label = row_value(values, positions, "Unicode")
    codepoint = parse_unicode_label(unicode_label)
    cnbe_hex = parse_int(row_value(values, positions, "CNBE(Hex)"), 16)
    cnbe_dec = parse_int(row_value(values, positions, "CNBE(Dec)"), 10)
    cnbe_bin = parse_int(row_value(values, positions, "CNBE(Bin)"), 2)
    radical = parse_int(row_value(values, positions, "部首区"))
    strokes = parse_int(row_value(values, positions, "笔画数"))
    structure_code = parse_int(row_value(values, positions, "结构区(v4)"))
    index = parse_int(row_value(values, positions, "字库索引"))
    extension = parse_int(row_value(values, positions, "扩展区"))

    issues: list[str] = []
    if sequence is None:
        issues.append("missing_or_invalid_sequence")
    if not isinstance(char, str) or len(char) != 1:
        issues.append("missing_or_invalid_single_character")
    if codepoint is None:
        issues.append("missing_or_invalid_unicode_label")
    if isinstance(char, str) and len(char) == 1 and codepoint is not None and ord(char) != codepoint:
        issues.append("unicode_char_mismatch")
    if codepoint is not None and not 0 <= codepoint <= 0x10FFFF:
        issues.append("unicode_codepoint_out_of_range")
    if None in {cnbe_hex, cnbe_dec, cnbe_bin}:
        issues.append("missing_or_invalid_cnbe_representation")
    elif not (cnbe_hex == cnbe_dec == cnbe_bin):
        issues.append("cnbe_representation_mismatch")
    if cnbe_dec is not None and not 0 <= cnbe_dec <= CNBE32_MAX:
        issues.append("cnbe32_out_of_range")
    required_bitfields = {
        "radical": radical,
        "strokes": strokes,
        "structure_code": structure_code,
        "index": index,
        "extension": extension,
    }
    if any(value is None for value in required_bitfields.values()):
        issues.append("missing_or_invalid_cnbe_bitfield")
    elif cnbe_dec is not None:
        recomputed = (radical << 24) | (strokes << 19) | (structure_code << 15) | (index << 4) | extension
        if recomputed != cnbe_dec:
            issues.append("cnbe_bitfield_recompute_mismatch")

    identity = {
        "worksheet_row": worksheet_row,
        "sequence": sequence,
        "char": char,
        "unicode": unicode_label,
        "codepoint": codepoint,
        "cnbe_dec": cnbe_dec,
        "issues": issues,
    }
    return identity, issues


def iter_rows(archive: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> Any:
    with archive.open(sheet_path) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag != f"{{{MAIN_NS}}}row":
                continue
            worksheet_row = int(element.get("r", "0"))
            values = row_values(element, shared_strings)
            yield worksheet_row, values
            element.clear()


def inspect_source(source: Path, include_rows: bool = True) -> dict[str, Any]:
    with zipfile.ZipFile(source) as archive:
        shared_strings = load_shared_strings(archive)
        sheet = next((item for item in workbook_sheets(archive) if item["name"] == EXPECTED_SHEET), None)
        if sheet is None:
            raise ValueError(f"required worksheet not found: {EXPECTED_SHEET}")
        root = ET.fromstring(archive.read(sheet["path"]))
        dimension = parse_dimension(root.find(f"{{{MAIN_NS}}}dimension").get("ref"))

        rows = iter_rows(archive, sheet["path"], shared_strings)
        header_row, headers = next(rows)
        if header_row != HEADER_ROW:
            raise ValueError(f"expected header row {HEADER_ROW}, got {header_row}")
        positions = map_headers(headers)
        missing = [name for name in REQUIRED_COLUMNS if name not in positions]
        if missing:
            raise ValueError(f"missing required columns: {', '.join(missing)}")

        identities: list[dict[str, Any]] = []
        issue_counts: Counter[str] = Counter()
        issue_samples: list[dict[str, Any]] = []
        duplicate_unicode_samples: list[dict[str, Any]] = []
        duplicate_char_samples: list[dict[str, Any]] = []
        seen_unicode: dict[int, int] = {}
        seen_char: dict[str, int] = {}
        sequences: list[int] = []
        data_rows = 0

        for worksheet_row, values in rows:
            if not any(value not in {None, ""} for value in values):
                continue
            data_rows += 1
            identity, issues = inspect_identity_row(worksheet_row, values, positions)
            if include_rows:
                identities.append(identity)
            for issue in issues:
                issue_counts[issue] += 1
            if issues:
                append_sample(issue_samples, {"worksheet_row": worksheet_row, "issues": issues, "identity": identity})

            codepoint = identity["codepoint"]
            char = identity["char"]
            sequence = identity["sequence"]
            if isinstance(sequence, int):
                sequences.append(sequence)
            if isinstance(codepoint, int):
                if codepoint in seen_unicode:
                    append_sample(
                        duplicate_unicode_samples,
                        {
                            "codepoint": codepoint,
                            "unicode": f"U+{codepoint:04X}",
                            "first_row": seen_unicode[codepoint],
                            "duplicate_row": worksheet_row,
                        },
                    )
                    issue_counts["duplicate_unicode"] += 1
                else:
                    seen_unicode[codepoint] = worksheet_row
            if isinstance(char, str) and len(char) == 1:
                if char in seen_char:
                    append_sample(
                        duplicate_char_samples,
                        {
                            "char": char,
                            "first_row": seen_char[char],
                            "duplicate_row": worksheet_row,
                        },
                    )
                    issue_counts["duplicate_char"] += 1
                else:
                    seen_char[char] = worksheet_row

    sequence_gaps = []
    if sequences:
        expected = set(range(min(sequences), max(sequences) + 1))
        missing_sequences = sorted(expected - set(sequences))
        sequence_gaps = missing_sequences[:SAMPLE_LIMIT]
    summary = {
        "status": "PASS" if not issue_counts and data_rows == EXPECTED_DATA_ROWS and not sequence_gaps else "REVIEW",
        "data_rows": data_rows,
        "expected_data_rows": EXPECTED_DATA_ROWS,
        "unique_unicode": len(seen_unicode),
        "unique_char": len(seen_char),
        "issue_counts": dict(sorted(issue_counts.items())),
        "sequence_min": min(sequences) if sequences else None,
        "sequence_max": max(sequences) if sequences else None,
        "sequence_gap_sample": sequence_gaps,
        "full_row_identities_included": include_rows,
    }
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
        },
        "summary": summary,
        "issue_samples": issue_samples,
        "duplicate_unicode_samples": duplicate_unicode_samples,
        "duplicate_char_samples": duplicate_char_samples,
        "row_identities": identities,
    }


def build_report(source: Path, include_rows: bool = True) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_v4_fixed_unicode_identity_gate",
        "authority_boundary": {
            "scope": "unicode_identity_and_cnbe_field_consistency",
            "does_not_reconstruct_encoding": True,
            "does_not_modify_data_files": True,
            "does_not_assert_national_standard_alignment": True,
            "next_gate": "source_evidence_and_gf0017_gate",
        },
        **inspect_source(source, include_rows=include_rows),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-only", action="store_true", help="Omit per-row identity records.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    report = build_report(args.source, include_rows=not args.summary_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    print(f"Status: {report['summary']['status']}")
    print(f"Rows: {report['summary']['data_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
