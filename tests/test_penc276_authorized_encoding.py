"""Regression checks for the authorized 276-row CNBE encoding batch."""

import csv
import json
import sqlite3
from pathlib import Path


def test_authorized_candidate_batch_roundtrips_and_has_human_basis() -> None:
    path = Path("evidence/8105/pending276/PENC276_AUTHORIZED_ENCODING_CANDIDATES.csv")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 276
    assert len({row["unicode"] for row in rows}) == 276
    assert all(row["authority"] == "HUMAN_AUDIT_PROJECT_BASELINE_USER_AUTHORIZED_2026_07_27" for row in rows)
    for row in rows:
        value = int(row["cnbe"])
        assert ((value >> 24) & 0xFF) == int(row["radix"])
        assert ((value >> 19) & 0x1F) == int(row["strokes"])
        assert ((value >> 15) & 0x0F) == int(row["struct_type"])
        assert ((value >> 4) & 0x7FF) == int(row["idx"])
        assert value & 0x0F == 0


def test_runtime_and_package_databases_include_completed_batch() -> None:
    candidate_path = Path("evidence/8105/pending276/PENC276_AUTHORIZED_ENCODING_CANDIDATES.csv")
    with candidate_path.open(encoding="utf-8", newline="") as stream:
        candidates = list(csv.DictReader(stream))
    expected = {
        int(row["unicode"]): (
            int(row["cnbe"]),
            int(row["radix"]),
            row["radix_name"],
            int(row["strokes"]),
            int(row["struct_type"]),
            row["struct_name"],
            int(row["idx"]),
            "standard",
            0,
        )
        for row in candidates
    }
    for path in (Path("data/cnbe32.db"), Path("src/cnbe32/data/cnbe32.db")):
        with sqlite3.connect(path) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert connection.execute("SELECT COUNT(*) FROM cnbe32").fetchone()[0] == 21178
            assert connection.execute("SELECT COUNT(*) FROM cnbe32 WHERE needs_encoding=1").fetchone()[0] == 0
            actual = {
                row[0]: row[1:]
                for row in connection.execute(
                    "SELECT unicode, cnbe, radix, radix_name, strokes, struct_type, struct_name, idx, track, needs_encoding "
                    "FROM cnbe32 WHERE unicode IN ({})".format(
                        ",".join("?" for _ in expected)
                    ),
                    tuple(expected),
                )
            }
            assert actual == expected
    model = json.loads(Path("data/cnbe32.json").read_text(encoding="utf-8"))
    assert model["metadata"]["penc276_authorized_encoding_rows"] == 276
    assert len(model["characters"]) == 21178
    runtime = {row["unicode"]: row for row in model["characters"]}
    for unicode, values in expected.items():
        row = runtime[unicode]
        assert (
            row["cnbe"], row["radix"], row["radix_name"], row["strokes"],
            row["struct_type"], row["struct_name"], row["index"], row["track"],
            row["needs_encoding"],
        ) == values
