#!/usr/bin/env python3
"""Build an isolated, verified SQLite database from the audited CNBE catalog."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

try:
    from audit_full_catalog_xlsx import (
        EXPECTED_DATA_ROWS,
        EXPECTED_SHEET,
        FIELD_LIMITS,
        iter_sheet_rows,
        parse_integer,
        sha256_file,
        unicode_block,
        workbook_sheets,
    )
except ModuleNotFoundError:  # pragma: no cover - import path used by tests
    from scripts.audit_full_catalog_xlsx import (
        EXPECTED_DATA_ROWS,
        EXPECTED_SHEET,
        FIELD_LIMITS,
        iter_sheet_rows,
        parse_integer,
        sha256_file,
        unicode_block,
        workbook_sheets,
    )

SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path("build/full_catalog/cnbe32_full.db")
DEFAULT_MANIFEST = Path("reports/full_catalog_build.json")
DEFAULT_AUDIT = Path("reports/full_catalog_feasibility.json")
INSERT_BATCH_SIZE = 2_000

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

CREATE_SCHEMA_SQL = """
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE cnbe32_full (
    unicode INTEGER PRIMARY KEY,
    char TEXT NOT NULL UNIQUE,
    cnbe INTEGER NOT NULL UNIQUE,
    radical INTEGER NOT NULL CHECK (radical BETWEEN 0 AND 255),
    strokes INTEGER NOT NULL CHECK (strokes BETWEEN 0 AND 31),
    struct_type INTEGER NOT NULL CHECK (struct_type BETWEEN 0 AND 15),
    struct_name TEXT NOT NULL,
    idx INTEGER NOT NULL CHECK (idx BETWEEN 0 AND 2047),
    ext INTEGER NOT NULL CHECK (ext BETWEEN 0 AND 15),
    unicode_block TEXT NOT NULL,
    source_sequence INTEGER NOT NULL UNIQUE
);

CREATE INDEX idx_full_radical ON cnbe32_full(radical);
CREATE INDEX idx_full_strokes ON cnbe32_full(strokes);
CREATE INDEX idx_full_struct_type ON cnbe32_full(struct_type);
CREATE INDEX idx_full_unicode_block ON cnbe32_full(unicode_block);
"""

INSERT_SQL = """
INSERT INTO cnbe32_full (
    unicode,
    char,
    cnbe,
    radical,
    strokes,
    struct_type,
    struct_name,
    idx,
    ext,
    unicode_block,
    source_sequence
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def load_audit_report(path: Path, source: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read audit report {path}: {exc}") from exc

    if report.get("summary", {}).get("status") != "PASS":
        raise ValueError("audit report is not PASS")
    if report.get("summary", {}).get("sqlite_build_gate") != "GO":
        raise ValueError("audit report has not opened the SQLite build gate")
    if report.get("summary", {}).get("catalog_rows") != EXPECTED_DATA_ROWS:
        raise ValueError("audit report row count does not match the expected catalog size")

    expected_hash = report.get("source", {}).get("sha256")
    actual_hash = sha256_file(source)
    if expected_hash != actual_hash:
        raise ValueError(f"source SHA-256 differs from audit report: expected {expected_hash}, got {actual_hash}")
    return report


def workbook_records(source: Path) -> Any:
    with zipfile.ZipFile(source) as archive:
        sheets = workbook_sheets(archive)
        sheet = next((item for item in sheets if item["name"] == EXPECTED_SHEET), None)
        if sheet is None:
            raise ValueError(f"required worksheet not found: {EXPECTED_SHEET}")

        rows = iter_sheet_rows(archive, sheet["path"])
        _, headers = next(rows)
        positions = {str(name): index for index, name in enumerate(headers) if name is not None}
        missing = [name for name in REQUIRED_COLUMNS if name not in positions]
        if missing:
            raise ValueError(f"required columns missing: {', '.join(missing)}")

        def value(record: list[Any], column: str) -> Any:
            position = positions[column]
            return record[position] if position < len(record) else None

        for worksheet_row, record in rows:
            unicode_text = value(record, "Unicode")
            if not isinstance(unicode_text, str) or not unicode_text.startswith("U+"):
                continue

            try:
                sequence = parse_integer(value(record, "序号"))
                character = str(value(record, "汉字"))
                codepoint = int(unicode_text[2:], 16)
                cnbe_hex = parse_integer(value(record, "CNBE(Hex)"), 16)
                cnbe_dec = parse_integer(value(record, "CNBE(Dec)"))
                cnbe_bin = int(str(value(record, "CNBE(Bin)")), 2)
                radical = parse_integer(value(record, "部首区"))
                strokes = parse_integer(value(record, "笔画数"))
                struct_type = parse_integer(value(record, "结构区"))
                struct_name = str(value(record, "结构名称"))
                index = parse_integer(value(record, "字库区索引"))
                extension = parse_integer(value(record, "扩展区"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"worksheet row {worksheet_row} cannot be parsed: {exc}") from exc

            if len(character) != 1 or ord(character) != codepoint:
                raise ValueError(f"worksheet row {worksheet_row} character does not match Unicode")
            if not (cnbe_hex == cnbe_dec == cnbe_bin):
                raise ValueError(f"worksheet row {worksheet_row} has inconsistent CNBE representations")
            fields = {
                "部首区": radical,
                "笔画数": strokes,
                "结构区": struct_type,
                "字库区索引": index,
                "扩展区": extension,
            }
            for name, field_value in fields.items():
                minimum, maximum = FIELD_LIMITS[name]
                if not minimum <= field_value <= maximum:
                    raise ValueError(f"worksheet row {worksheet_row} has out-of-range {name}={field_value}")

            recomputed = (radical << 24) | (strokes << 19) | (struct_type << 15) | (index << 4) | extension
            if recomputed != cnbe_dec:
                raise ValueError(f"worksheet row {worksheet_row} failed CNBE bitfield recomputation")

            yield (
                codepoint,
                character,
                cnbe_dec,
                radical,
                strokes,
                struct_type,
                struct_name,
                index,
                extension,
                unicode_block(codepoint),
                sequence,
            )


def prepare_database(connection: sqlite3.Connection, source_hash: str) -> None:
    connection.execute("PRAGMA page_size = 4096")
    connection.execute("PRAGMA journal_mode = DELETE")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA encoding = 'UTF-8'")
    connection.executescript(CREATE_SCHEMA_SQL)
    metadata = {
        "schema_version": str(SCHEMA_VERSION),
        "catalog_scope": "full_catalog_experimental",
        "source_sha256": source_hash,
        "audit_report_schema_version": "1",
        "expected_rows": str(EXPECTED_DATA_ROWS),
        "cnbe_formula": "R<<24 | S<<19 | G<<15 | I<<4 | E",
    }
    connection.executemany("INSERT INTO metadata (key, value) VALUES (?, ?)", sorted(metadata.items()))


def insert_records(connection: sqlite3.Connection, source: Path) -> int:
    count = 0
    batch = []
    for row in workbook_records(source):
        batch.append(row)
        if len(batch) >= INSERT_BATCH_SIZE:
            connection.executemany(INSERT_SQL, batch)
            count += len(batch)
            batch.clear()
    if batch:
        connection.executemany(INSERT_SQL, batch)
        count += len(batch)
    return count


def query_distribution(connection: sqlite3.Connection, column: str) -> dict[str, int]:
    allowed = {"unicode_block", "struct_name"}
    if column not in allowed:
        raise ValueError(f"unsupported distribution column: {column}")
    rows = connection.execute(
        f"SELECT {column}, COUNT(*) FROM cnbe32_full GROUP BY {column} ORDER BY COUNT(*) DESC, {column}"
    ).fetchall()
    return {str(name): int(count) for name, count in rows}


def verify_database(connection: sqlite3.Connection, audit: dict[str, Any]) -> dict[str, Any]:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    row_count = int(connection.execute("SELECT COUNT(*) FROM cnbe32_full").fetchone()[0])
    distinct = connection.execute(
        "SELECT COUNT(DISTINCT unicode), COUNT(DISTINCT char), COUNT(DISTINCT cnbe), "
        "COUNT(DISTINCT source_sequence) FROM cnbe32_full"
    ).fetchone()
    min_max = connection.execute(
        "SELECT MIN(unicode), MAX(unicode), MIN(cnbe), MAX(cnbe), MIN(source_sequence), MAX(source_sequence) "
        "FROM cnbe32_full"
    ).fetchone()
    encoding_mismatches = int(
        connection.execute(
            "SELECT COUNT(*) FROM cnbe32_full WHERE cnbe != "
            "((radical << 24) | (strokes << 19) | (struct_type << 15) | (idx << 4) | ext)"
        ).fetchone()[0]
    )
    database_blocks = query_distribution(connection, "unicode_block")
    database_structures = query_distribution(connection, "struct_name")
    expected_blocks = audit["profile"]["unicode_block_distribution"]
    expected_structures = audit["profile"]["structure_distribution"]

    checks = {
        "sqlite_integrity": integrity == "ok",
        "row_count": row_count == EXPECTED_DATA_ROWS,
        "unicode_uniqueness": distinct[0] == row_count,
        "character_uniqueness": distinct[1] == row_count,
        "cnbe_uniqueness": distinct[2] == row_count,
        "source_sequence_uniqueness": distinct[3] == row_count,
        "source_sequence_bounds": min_max[4] == 0 and min_max[5] == EXPECTED_DATA_ROWS - 1,
        "bitfield_recomputation": encoding_mismatches == 0,
        "unicode_block_reconciliation": database_blocks == expected_blocks,
        "structure_reconciliation": database_structures == expected_structures,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": {name: "PASS" if passed else "FAIL" for name, passed in checks.items()},
        "sqlite_integrity_check": integrity,
        "row_count": row_count,
        "distinct_counts": {
            "unicode": distinct[0],
            "character": distinct[1],
            "cnbe": distinct[2],
            "source_sequence": distinct[3],
        },
        "bounds": {
            "unicode_min": f"U+{min_max[0]:04X}",
            "unicode_max": f"U+{min_max[1]:04X}",
            "cnbe_min": min_max[2],
            "cnbe_max": min_max[3],
            "source_sequence_min": min_max[4],
            "source_sequence_max": min_max[5],
        },
        "bitfield_recomputation_mismatches": encoding_mismatches,
        "unicode_block_distribution": database_blocks,
        "structure_distribution": database_structures,
    }


def build_database(source: Path, audit_path: Path, output: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    audit = load_audit_report(audit_path, source)
    source_hash = audit["source"]["sha256"]
    output.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        with sqlite3.connect(temporary_path) as connection:
            prepare_database(connection, source_hash)
            inserted = insert_records(connection, source)
            if inserted != EXPECTED_DATA_ROWS:
                raise ValueError(f"inserted {inserted} rows, expected {EXPECTED_DATA_ROWS}")
            connection.commit()
            verification = verify_database(connection, audit)
            if verification["status"] != "PASS":
                failed = [name for name, status in verification["checks"].items() if status == "FAIL"]
                raise ValueError(f"post-build verification failed: {', '.join(failed)}")
            connection.execute("VACUUM")
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return audit, verification


def build_manifest(
    source: Path,
    audit_path: Path,
    output: Path,
    audit: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parent.parent

    def display_path(path: Path) -> str:
        try:
            return path.relative_to(repo_root).as_posix()
        except ValueError:
            return path.name

    return {
        "manifest_schema_version": 1,
        "status": verification["status"],
        "artifact": {
            "path": display_path(output),
            "size_bytes": output.stat().st_size,
            "sha256": sha256_file(output),
            "sqlite_schema_version": SCHEMA_VERSION,
            "scope": "full_catalog_experimental",
        },
        "source": {
            "file_name": source.name,
            "sha256": audit["source"]["sha256"],
            "audit_report": display_path(audit_path),
            "audit_report_sha256": sha256_file(audit_path),
        },
        "verification": verification,
        "release_boundary": {
            "packaged_sdk_database_replaced": False,
            "public_api_changed": False,
            "version_changed": False,
            "publishing_authorized": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the audited source .xlsx catalog")
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT, help="PASS audit report path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="SQLite artifact output path")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="build manifest output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    audit_path = args.audit.expanduser().resolve()
    output = args.output.expanduser().resolve()
    manifest_path = args.manifest.expanduser().resolve()

    try:
        audit, verification = build_database(source, audit_path, output)
        manifest = build_manifest(source, audit_path, output, audit, verification)
    except (OSError, sqlite3.Error, ValueError, zipfile.BadZipFile) as exc:
        print(f"FULL CATALOG BUILD FAIL: {exc}", file=sys.stderr)
        return 1

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"FULL CATALOG BUILD PASS: {verification['row_count']:,} rows")
    print(f"Database: {output}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
