#!/usr/bin/env python3
"""Compare the full catalog Basic CJK rows with the packaged SDK database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from audit_full_catalog_xlsx import sha256_file
    from build_full_catalog_db import workbook_records
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_full_catalog_xlsx import sha256_file
    from scripts.build_full_catalog_db import workbook_records

BASIC_START = 0x4E00
BASIC_END = 0x9FFF
EXPECTED_FULL_BASIC_ROWS = BASIC_END - BASIC_START + 1
EXPECTED_SDK_ROWS = 20_902
EXPECTED_GAP_ROWS = 90
DEFAULT_SDK_DATABASE = Path("data/cnbe32.db")
DEFAULT_OUTPUT = Path("reports/basic_cjk_scope_gap.json")
SAMPLE_LIMIT = 20

COMPARISON_FIELDS = (
    "char",
    "cnbe",
    "radical",
    "strokes",
    "struct_type",
    "struct_name",
    "idx",
)


def format_codepoint(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def contiguous_ranges(codepoints: list[int]) -> list[dict[str, Any]]:
    if not codepoints:
        return []
    values = sorted(set(codepoints))
    ranges = []
    start = previous = values[0]
    for codepoint in values[1:]:
        if codepoint != previous + 1:
            ranges.append(
                {
                    "start": format_codepoint(start),
                    "end": format_codepoint(previous),
                    "count": previous - start + 1,
                }
            )
            start = codepoint
        previous = codepoint
    ranges.append(
        {
            "start": format_codepoint(start),
            "end": format_codepoint(previous),
            "count": previous - start + 1,
        }
    )
    return ranges


def load_full_basic_catalog(source: Path) -> dict[int, dict[str, Any]]:
    catalog = {}
    for row in workbook_records(source):
        codepoint = row[0]
        if BASIC_START <= codepoint <= BASIC_END:
            catalog[codepoint] = {
                "unicode": codepoint,
                "char": row[1],
                "cnbe": row[2],
                "radical": row[3],
                "strokes": row[4],
                "struct_type": row[5],
                "struct_name": row[6],
                "idx": row[7],
                "ext": row[8],
                "source_sequence": row[10],
            }
    return catalog


def load_sdk_catalog(database: Path) -> tuple[dict[int, dict[str, Any]], str]:
    if not database.is_file():
        raise ValueError(f"SDK database not found: {database}")
    with sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        rows = connection.execute(
            "SELECT unicode, char, cnbe, radix, strokes, struct_type, struct_name, idx FROM cnbe32"
        ).fetchall()
    catalog = {
        int(row["unicode"]): {
            "unicode": int(row["unicode"]),
            "char": row["char"],
            "cnbe": int(row["cnbe"]),
            "radical": int(row["radix"]),
            "strokes": int(row["strokes"]),
            "struct_type": int(row["struct_type"]),
            "struct_name": row["struct_name"],
            "idx": int(row["idx"]),
        }
        for row in rows
    }
    return catalog, integrity


def gap_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "unicode": format_codepoint(row["unicode"]),
        "codepoint": row["unicode"],
        "char": row["char"],
        "cnbe": row["cnbe"],
        "cnbe_hex": f"0x{row['cnbe']:08X}",
        "radical": row["radical"],
        "strokes": row["strokes"],
        "struct_type": row["struct_type"],
        "struct_name": row["struct_name"],
        "idx": row["idx"],
        "ext": row["ext"],
        "source_sequence": row["source_sequence"],
    }


def compare_catalogs(full: dict[int, dict[str, Any]], sdk: dict[int, dict[str, Any]]) -> dict[str, Any]:
    full_keys = set(full)
    sdk_keys = set(sdk)
    shared = sorted(full_keys & sdk_keys)
    missing_from_sdk = sorted(full_keys - sdk_keys)
    sdk_only = sorted(sdk_keys - full_keys)
    mismatches: Counter[str] = Counter()
    exact_all_fields = 0
    exact_numeric_mapping = 0
    exact_numeric_codepoints = []
    mismatch_samples = []

    numeric_fields = ("cnbe", "radical", "strokes", "struct_type", "idx")
    for codepoint in shared:
        full_row = full[codepoint]
        sdk_row = sdk[codepoint]
        differences = {}
        for field in COMPARISON_FIELDS:
            if full_row[field] != sdk_row[field]:
                mismatches[field] += 1
                differences[field] = {"sdk": sdk_row[field], "full_catalog": full_row[field]}
        if not differences:
            exact_all_fields += 1
        if all(full_row[field] == sdk_row[field] for field in numeric_fields):
            exact_numeric_mapping += 1
            exact_numeric_codepoints.append(codepoint)
        if differences and len(mismatch_samples) < SAMPLE_LIMIT:
            mismatch_samples.append(
                {
                    "unicode": format_codepoint(codepoint),
                    "char": full_row["char"],
                    "differences": differences,
                }
            )

    return {
        "counts": {
            "full_basic_rows": len(full),
            "sdk_rows": len(sdk),
            "shared_unicode_rows": len(shared),
            "missing_from_sdk_rows": len(missing_from_sdk),
            "sdk_only_rows": len(sdk_only),
            "exact_all_compared_fields_rows": exact_all_fields,
            "exact_numeric_mapping_rows": exact_numeric_mapping,
        },
        "rates": {
            "sdk_unicode_coverage_of_full_basic": len(shared) / len(full) if full else 0,
            "exact_all_fields_among_shared": exact_all_fields / len(shared) if shared else 0,
            "exact_numeric_mapping_among_shared": exact_numeric_mapping / len(shared) if shared else 0,
        },
        "ranges": {
            "full_basic": contiguous_ranges(sorted(full_keys)),
            "sdk": contiguous_ranges(sorted(sdk_keys)),
            "missing_from_sdk": contiguous_ranges(missing_from_sdk),
            "sdk_only": contiguous_ranges(sdk_only),
        },
        "field_mismatch_counts": {field: mismatches[field] for field in COMPARISON_FIELDS},
        "exact_numeric_mapping_codepoints": [
            {"unicode": format_codepoint(codepoint), "char": full[codepoint]["char"]}
            for codepoint in exact_numeric_codepoints
        ],
        "mismatch_samples": mismatch_samples,
        "missing_from_sdk": [gap_record(full[codepoint]) for codepoint in missing_from_sdk],
        "sdk_only": [
            {
                "unicode": format_codepoint(codepoint),
                "codepoint": codepoint,
                "char": sdk[codepoint]["char"],
            }
            for codepoint in sdk_only
        ],
    }


def build_report(source: Path, sdk_database: Path) -> dict[str, Any]:
    full = load_full_basic_catalog(source)
    sdk, sdk_integrity = load_sdk_catalog(sdk_database)
    comparison = compare_catalogs(full, sdk)
    counts = comparison["counts"]

    coverage_boundary_confirmed = (
        counts["full_basic_rows"] == EXPECTED_FULL_BASIC_ROWS
        and counts["sdk_rows"] == EXPECTED_SDK_ROWS
        and counts["missing_from_sdk_rows"] == EXPECTED_GAP_ROWS
        and counts["sdk_only_rows"] == 0
        and comparison["ranges"]["missing_from_sdk"]
        == [{"start": "U+9FA6", "end": "U+9FFF", "count": EXPECTED_GAP_ROWS}]
    )
    mapping_compatible = counts["exact_numeric_mapping_rows"] == counts["shared_unicode_rows"]

    return {
        "report_schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_scope": "Basic CJK U+4E00..U+9FFF",
        "sources": {
            "full_catalog": {
                "file_name": source.name,
                "sha256": sha256_file(source),
            },
            "sdk_database": {
                "path": "data/cnbe32.db",
                "sha256": sha256_file(sdk_database),
                "sqlite_integrity_check": sdk_integrity,
            },
        },
        "summary": {
            "status": "COMPLETE",
            "coverage_boundary_status": "CONFIRMED" if coverage_boundary_confirmed else "UNEXPECTED",
            "mapping_compatibility": "COMPATIBLE" if mapping_compatible else "INCOMPATIBLE",
            "sdk_replacement_gate": "GO" if coverage_boundary_confirmed and mapping_compatible else "NO_GO",
            "severity": "critical" if not mapping_compatible else "medium",
        },
        "comparison": comparison,
        "findings": [
            {
                "id": "BASIC-COVERAGE-BOUNDARY",
                "severity": "medium",
                "confidence": "high",
                "finding": (
                    "The 90-row coverage difference is one contiguous tail: the SDK ends at U+9FA5 while the full "
                    "catalog continues through U+9FFF."
                ),
                "likely_cause": (
                    "A historical Basic CJK cutoff is strongly indicated by the exact contiguous boundary, but the "
                    "repository does not yet contain provenance establishing why that cutoff was selected."
                ),
            },
            {
                "id": "ENCODING-LINEAGE-MISMATCH",
                "severity": "critical",
                "confidence": "high",
                "finding": (
                    f"Only {counts['exact_numeric_mapping_rows']} of {counts['shared_unicode_rows']} shared Unicode "
                    "rows have the same numeric CNBE mapping fields."
                ),
                "impact": (
                    "The full catalog cannot be appended to or substituted for the SDK database without changing "
                    "existing encoded values and lookup behavior."
                ),
            },
        ],
        "decision": {
            "direct_append_allowed": False,
            "direct_sdk_replacement_allowed": False,
            "publish_as_sdk_compatible_allowed": False,
            "full_catalog_may_remain_separate_experimental_artifact": True,
            "next_required_work": (
                "Establish the provenance and intended authority of both encoding mappings, select a canonical "
                "mapping contract, and define an explicit migration/versioning policy before integration."
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the full-catalog .xlsx file")
    parser.add_argument("--sdk-db", type=Path, default=DEFAULT_SDK_DATABASE, help="packaged SDK SQLite database")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON report output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    sdk_database = args.sdk_db.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        print(f"BASIC CJK GAP ANALYSIS ERROR: source not found: {source}", file=sys.stderr)
        return 2

    try:
        report = build_report(source, sdk_database)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"BASIC CJK GAP ANALYSIS ERROR: {exc}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    counts = report["comparison"]["counts"]
    print(
        "BASIC CJK GAP ANALYSIS COMPLETE: "
        f"{counts['missing_from_sdk_rows']} coverage rows, "
        f"{counts['exact_numeric_mapping_rows']}/{counts['shared_unicode_rows']} shared numeric mappings exact"
    )
    print(f"SDK replacement gate: {report['summary']['sdk_replacement_gate']}")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
