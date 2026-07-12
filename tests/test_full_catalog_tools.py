"""Tests for the isolated full-catalog build and query tools."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.build_full_catalog_db import (
    CREATE_SCHEMA_SQL,
    INSERT_SQL,
    load_audit_report,
    prepare_database,
)
from scripts.query_full_catalog_db import (
    database_stats,
    lookup_by_char,
    lookup_by_cnbe,
    lookup_by_unicode,
    open_read_only,
    parse_cnbe,
    parse_unicode,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def full_catalog_db(tmp_path: Path) -> Path:
    path = tmp_path / "cnbe32_full.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(CREATE_SCHEMA_SQL)
        connection.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            [
                ("schema_version", "1"),
                ("catalog_scope", "full_catalog_experimental"),
            ],
        )
        connection.executemany(
            INSERT_SQL,
            [
                (0x3400, "㐀", 0x01280000, 1, 5, 0, "独体结构", 0, 0, "Extension A", 0),
                (0x4E00, "一", 0x01100000, 1, 2, 0, "独体结构", 0, 0, "Basic", 1),
            ],
        )
    return path


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("U+4E00", 0x4E00),
        ("0x4e00", 0x4E00),
        ("19968", 0x4E00),
    ],
)
def test_parse_unicode(text: str, expected: int) -> None:
    assert parse_unicode(text) == expected


@pytest.mark.parametrize("text", ["-1", "U+110000", "not-a-codepoint"])
def test_parse_unicode_rejects_invalid_values(text: str) -> None:
    with pytest.raises(ValueError):
        parse_unicode(text)


def test_parse_cnbe_supports_decimal_and_hex() -> None:
    assert parse_cnbe("0x01280000") == 0x01280000
    assert parse_cnbe(str(0x01280000)) == 0x01280000


@pytest.mark.parametrize("text", ["-1", str(2**32), "invalid"])
def test_parse_cnbe_rejects_invalid_values(text: str) -> None:
    with pytest.raises(ValueError):
        parse_cnbe(text)


def test_lookup_paths_return_the_same_record(full_catalog_db: Path) -> None:
    with open_read_only(full_catalog_db) as connection:
        by_char = lookup_by_char(connection, "㐀")
        by_unicode = lookup_by_unicode(connection, 0x3400)
        by_cnbe = lookup_by_cnbe(connection, 0x01280000)
    assert by_char == by_unicode == by_cnbe
    assert by_char is not None
    assert by_char["unicode_label"] == "U+3400"
    assert by_char["cnbe_hex"] == "0x01280000"
    assert by_char["cnbe_binary"] == "00000001001010000000000000000000"


def test_lookup_returns_none_for_missing_record(full_catalog_db: Path) -> None:
    with open_read_only(full_catalog_db) as connection:
        assert lookup_by_char(connection, "丁") is None


def test_lookup_rejects_multiple_characters(full_catalog_db: Path) -> None:
    with open_read_only(full_catalog_db) as connection:
        with pytest.raises(ValueError, match="exactly one"):
            lookup_by_char(connection, "一丁")


def test_database_stats_reports_integrity_and_distributions(full_catalog_db: Path) -> None:
    with open_read_only(full_catalog_db) as connection:
        stats = database_stats(connection)
    assert stats["status"] == "PASS"
    assert stats["rows"] == 2
    assert stats["unicode_min"] == "U+3400"
    assert stats["unicode_max"] == "U+4E00"
    assert stats["unicode_block_distribution"] == {"Basic": 1, "Extension A": 1}
    assert stats["structure_distribution"] == {"独体结构": 2}


def test_open_read_only_rejects_wrong_schema(tmp_path: Path) -> None:
    path = tmp_path / "wrong.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (value INTEGER)")
    with pytest.raises(ValueError, match="missing tables"):
        open_read_only(path)


def test_schema_enforces_cnbe_uniqueness(full_catalog_db: Path) -> None:
    with sqlite3.connect(full_catalog_db) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                INSERT_SQL,
                (0x4E01, "丁", 0x01280000, 1, 2, 0, "独体结构", 1, 0, "Basic", 2),
            )


def test_database_metadata_excludes_volatile_audit_file_hash(tmp_path: Path) -> None:
    path = tmp_path / "metadata.db"
    with sqlite3.connect(path) as connection:
        prepare_database(connection, "a" * 64)
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
    assert metadata["source_sha256"] == "a" * 64
    assert metadata["audit_report_schema_version"] == "1"
    assert "audit_report_sha256" not in metadata


def test_audit_gate_accepts_matching_pass_report(tmp_path: Path) -> None:
    source = tmp_path / "catalog.xlsx"
    source.write_bytes(b"test-source")
    report_path = tmp_path / "audit.json"
    report = {
        "summary": {"status": "PASS", "sqlite_build_gate": "GO", "catalog_rows": 97_686},
        "source": {"sha256": sha256(source)},
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    assert load_audit_report(report_path, source) == report


def test_audit_gate_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "catalog.xlsx"
    source.write_bytes(b"changed-source")
    report_path = tmp_path / "audit.json"
    report = {
        "summary": {"status": "PASS", "sqlite_build_gate": "GO", "catalog_rows": 97_686},
        "source": {"sha256": "0" * 64},
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        load_audit_report(report_path, source)
