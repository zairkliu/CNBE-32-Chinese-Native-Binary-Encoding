#!/usr/bin/env python3
"""Query an independently built CNBE-32 full-catalog SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

DEFAULT_DATABASE = Path("build/full_catalog/cnbe32_full.db")
REQUIRED_TABLES = {"metadata", "cnbe32_full"}
RESULT_COLUMNS = (
    "unicode",
    "char",
    "cnbe",
    "radical",
    "strokes",
    "struct_type",
    "struct_name",
    "idx",
    "ext",
    "unicode_block",
    "source_sequence",
)


def parse_unicode(value: str) -> int:
    text = value.strip().upper()
    if text.startswith("U+"):
        text = text[2:]
        base = 16
    elif text.startswith("0X"):
        base = 16
    else:
        base = 10
    codepoint = int(text, base)
    if not 0 <= codepoint <= 0x10FFFF:
        raise ValueError(f"Unicode code point out of range: {value}")
    return codepoint


def parse_cnbe(value: str) -> int:
    text = value.strip().lower()
    code = int(text, 16 if text.startswith("0x") else 10)
    if not 0 <= code <= 0xFFFFFFFF:
        raise ValueError(f"CNBE value out of range: {value}")
    return code


def open_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise ValueError(f"database not found: {path}")
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    missing = REQUIRED_TABLES - tables
    if missing:
        connection.close()
        raise ValueError(f"not a full-catalog database; missing tables: {', '.join(sorted(missing))}")
    return connection


def format_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = {column: row[column] for column in RESULT_COLUMNS}
    result["unicode_label"] = f"U+{result['unicode']:04X}"
    result["cnbe_hex"] = f"0x{result['cnbe']:08X}"
    result["cnbe_binary"] = f"{result['cnbe']:032b}"
    return result


def lookup_by_char(connection: sqlite3.Connection, character: str) -> dict[str, Any] | None:
    if len(character) != 1:
        raise ValueError("--char expects exactly one Unicode character")
    row = connection.execute("SELECT * FROM cnbe32_full WHERE char = ?", (character,)).fetchone()
    return format_row(row)


def lookup_by_unicode(connection: sqlite3.Connection, codepoint: int) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM cnbe32_full WHERE unicode = ?", (codepoint,)).fetchone()
    return format_row(row)


def lookup_by_cnbe(connection: sqlite3.Connection, code: int) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM cnbe32_full WHERE cnbe = ?", (code,)).fetchone()
    return format_row(row)


def database_stats(connection: sqlite3.Connection) -> dict[str, Any]:
    metadata = {
        row["key"]: row["value"]
        for row in connection.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
    }
    totals = connection.execute(
        "SELECT COUNT(*) AS rows, MIN(unicode) AS unicode_min, MAX(unicode) AS unicode_max, "
        "MIN(cnbe) AS cnbe_min, MAX(cnbe) AS cnbe_max FROM cnbe32_full"
    ).fetchone()
    blocks = {
        row["unicode_block"]: row["rows"]
        for row in connection.execute(
            "SELECT unicode_block, COUNT(*) AS rows FROM cnbe32_full "
            "GROUP BY unicode_block ORDER BY rows DESC, unicode_block"
        ).fetchall()
    }
    structures = {
        row["struct_name"]: row["rows"]
        for row in connection.execute(
            "SELECT struct_name, COUNT(*) AS rows FROM cnbe32_full "
            "GROUP BY struct_name ORDER BY rows DESC, struct_name"
        ).fetchall()
    }
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    return {
        "status": "PASS" if integrity == "ok" else "FAIL",
        "sqlite_integrity_check": integrity,
        "rows": totals["rows"],
        "unicode_min": f"U+{totals['unicode_min']:04X}" if totals["unicode_min"] is not None else None,
        "unicode_max": f"U+{totals['unicode_max']:04X}" if totals["unicode_max"] is not None else None,
        "cnbe_min": totals["cnbe_min"],
        "cnbe_max": totals["cnbe_max"],
        "metadata": metadata,
        "unicode_block_distribution": blocks,
        "structure_distribution": structures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE, help="full-catalog SQLite database")
    selectors = parser.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--char", help="look up exactly one character")
    selectors.add_argument("--unicode", dest="unicode_value", help="look up U+XXXX, 0xXXXX, or decimal")
    selectors.add_argument("--cnbe", help="look up a decimal or 0x-prefixed CNBE value")
    selectors.add_argument("--stats", action="store_true", help="show database metadata and distributions")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with open_read_only(args.db.expanduser()) as connection:
            if args.char is not None:
                result = lookup_by_char(connection, args.char)
            elif args.unicode_value is not None:
                result = lookup_by_unicode(connection, parse_unicode(args.unicode_value))
            elif args.cnbe is not None:
                result = lookup_by_cnbe(connection, parse_cnbe(args.cnbe))
            else:
                result = database_stats(connection)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"FULL CATALOG QUERY ERROR: {exc}", file=sys.stderr)
        return 2

    if result is None:
        print(json.dumps({"status": "NOT_FOUND"}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
