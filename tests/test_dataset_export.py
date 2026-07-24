"""Tests for scripts/export_dataset.py (PDR WS1-R1/R4)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_dataset.py"
_spec = importlib.util.spec_from_file_location("export_dataset", _SCRIPT)
export_dataset = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export_dataset)


@pytest.fixture()
def fixture_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "cnbe32.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        'CREATE TABLE cnbe32 (char TEXT, code INTEGER, radix INTEGER, stroke INTEGER, '
        'struct INTEGER, "index" INTEGER, ext INTEGER)'
    )
    rows = [
        ("一", (1 << 24) | (1 << 19) | (0 << 15) | (0 << 4), 1, 1, 0, 0, 0),
        ("汉", (9 << 24) | (5 << 19) | (1 << 15) | (7 << 4), 9, 5, 1, 7, 0),
        ("国", (31 << 24) | (8 << 19) | (11 << 15) | (12 << 4), 31, 8, 11, 12, 0),
    ]
    conn.executemany('INSERT INTO cnbe32 VALUES (?,?,?,?,?,?,?)', rows)
    conn.commit()
    conn.close()
    return db_path


def test_export_rows_and_schema(fixture_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    manifest = export_dataset.export_dataset(fixture_db, out)
    assert manifest["row_count"] == 3

    lines = (out / "cnbe32_annotations.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    rec = json.loads(lines[1])  # ORDER BY char: 一(U+4E00) 国(U+56FD) 汉(U+6C49)
    assert rec["char"] == "国"
    assert rec["unicode_cp"] == "U+56FD"
    assert rec["radical_id"] == 31
    assert rec["stroke_count"] == 8
    assert rec["structure_id"] == 11
    assert rec["glyph_index"] == 12
    assert rec["cnbe32_hex"].startswith("0x")
    # fixture has no tier column -> honest default, never fabricated
    assert rec["evidence_tier"] == "unresolved"
    assert rec["tier_source"] == "default_no_source"
    assert rec["in_8105"] is None


def test_scope_file_marks_8105(fixture_db: Path, tmp_path: Path) -> None:
    scope = tmp_path / "scope.txt"
    scope.write_text("一\n国\n", encoding="utf-8")
    out = tmp_path / "out"
    export_dataset.export_dataset(fixture_db, out, scope_file=scope)
    recs = [
        json.loads(x)
        for x in (out / "cnbe32_annotations.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [r["in_8105"] for r in recs] == [True, True, False]


def test_export_is_deterministic(fixture_db: Path, tmp_path: Path) -> None:
    out1, out2 = tmp_path / "o1", tmp_path / "o2"
    export_dataset.export_dataset(fixture_db, out1)
    export_dataset.export_dataset(fixture_db, out2)

    def digest(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    assert digest(out1 / "cnbe32_annotations.jsonl") == digest(out2 / "cnbe32_annotations.jsonl")
    m1 = json.loads((out1 / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert m1["outputs"]["jsonl"]["sha256"] == digest(out1 / "cnbe32_annotations.jsonl")
