#!/usr/bin/env python3
"""Promote the force-approved 8105 CNBE32 copy into runtime data.

This is the authorized source-write step. It replaces `data/cnbe32.json` with
the copied dataset, rebuilds both runtime SQLite databases from that source,
and writes a reproducible report.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COPIED_DATASET = Path("evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy.json")
PATCH_CSV = Path("evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy_patch.csv")
BLOCKED_CSV = Path("evidence/agent-standard/copied-datasets/cnbe32_8105_human_force_approved_copy_blocked_queue.csv")
RUNTIME_JSON = Path("data/cnbe32.json")
ROOT_DB = Path("data/cnbe32.db")
PACKAGE_DB = Path("src/cnbe32/data/cnbe32.db")
JSON_REPORT = Path("reports/8105_cnbe32_runtime_promotion.json")
MD_REPORT = Path("reports/8105_CNBE32_RUNTIME_PROMOTION.md")

EXPECTED_ROWS = 20902
EXPECTED_PATCHED_ROWS = 6712
EXPECTED_FORCE_APPROVED_NOT_PATCHED = 1393
HUMAN_DECISION_ID = "HUMAN_REVIEW_2026_07_19_CNBE32_DRY_RUN_FORCE_PASS"

CREATE_SQL = """
CREATE TABLE cnbe32 (
    unicode INTEGER PRIMARY KEY,
    char TEXT,
    cnbe INTEGER,
    radix INTEGER,
    radix_name TEXT,
    strokes INTEGER,
    struct_type INTEGER,
    struct_name TEXT,
    idx INTEGER
);

CREATE INDEX idx_cnbe ON cnbe32(cnbe);
CREATE INDEX idx_radix ON cnbe32(radix);
CREATE INDEX idx_strokes ON cnbe32(strokes);
"""

INSERT_SQL = """
INSERT INTO cnbe32 (
    unicode,
    char,
    cnbe,
    radix,
    radix_name,
    strokes,
    struct_type,
    struct_name,
    idx
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_row_is_valid(row: dict[str, Any]) -> None:
    codepoint = int(row["unicode"])
    if len(row["char"]) != 1 or ord(row["char"]) != codepoint:
        raise ValueError(f"char/unicode mismatch: {row!r}")
    field_limits = {
        "radix": (0, 255),
        "strokes": (0, 31),
        "struct_type": (0, 15),
        "index": (0, 2047),
    }
    for field, (minimum, maximum) in field_limits.items():
        value = int(row[field])
        if not minimum <= value <= maximum:
            raise ValueError(f"{row['char']} has invalid {field}: {value}")
    cnbe = int(row["cnbe"])
    ext = cnbe & 0x0F
    recomputed = (
        (int(row["radix"]) << 24)
        | (int(row["strokes"]) << 19)
        | (int(row["struct_type"]) << 15)
        | (int(row["index"]) << 4)
        | ext
    )
    if recomputed != cnbe:
        raise ValueError(f"{row['char']} failed CNBE bitfield recomputation")


def production_model(copied_model: dict[str, Any]) -> dict[str, Any]:
    rows = copied_model["characters"]
    for row in rows:
        assert_row_is_valid(row)
    metadata = dict(copied_model.get("metadata", {}))
    metadata.pop("copy_kind", None)
    metadata.pop("source_table_write_status", None)
    metadata.pop("database_rebuild_status", None)
    metadata.update(
        {
            "runtime_promotion": "8105_human_force_approved_cnbe32_runtime",
            "runtime_promoted_at": datetime.now(timezone.utc).isoformat(),
            "human_decision_id": HUMAN_DECISION_ID,
            "patched_8105_rows": EXPECTED_PATCHED_ROWS,
            "force_approved_not_patched_rows": EXPECTED_FORCE_APPROVED_NOT_PATCHED,
            "total": len(rows),
        }
    )
    return {"metadata": metadata, "characters": rows}


def rebuild_database(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA encoding = 'UTF-8'")
        connection.executescript(CREATE_SQL)
        connection.executemany(
            INSERT_SQL,
            [
                (
                    int(row["unicode"]),
                    row["char"],
                    int(row["cnbe"]),
                    int(row["radix"]),
                    row["radix_name"],
                    int(row["strokes"]),
                    int(row["struct_type"]),
                    row["struct_name"],
                    int(row["index"]),
                )
                for row in rows
            ],
        )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        count = int(connection.execute("SELECT COUNT(*) FROM cnbe32").fetchone()[0])
        distinct = connection.execute(
            "SELECT COUNT(DISTINCT unicode), COUNT(DISTINCT char) FROM cnbe32"
        ).fetchone()
        sample_rows = {
            char: dict(
                zip(
                    ["unicode", "char", "cnbe", "radix", "radix_name", "strokes", "struct_type", "struct_name", "idx"],
                    connection.execute("SELECT * FROM cnbe32 WHERE char = ?", (char,)).fetchone(),
                )
            )
            for char in ("家", "侵", "偶", "孓")
        }
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sqlite_integrity_check": integrity,
        "row_count": count,
        "distinct_unicode": distinct[0],
        "distinct_char": distinct[1],
        "samples": sample_rows,
    }


def build_report(model: dict[str, Any], db_reports: list[dict[str, Any]]) -> dict[str, Any]:
    rows = model["characters"]
    structure_counts = Counter(row["struct_name"] for row in rows)
    checks = {
        "runtime_json_row_count": len(rows) == EXPECTED_ROWS,
        "runtime_json_unique_unicode": len({row["unicode"] for row in rows}) == EXPECTED_ROWS,
        "runtime_json_unique_char": len({row["char"] for row in rows}) == EXPECTED_ROWS,
        "runtime_json_bitfields_valid": True,
        "root_database_rebuilt": db_reports[0]["row_count"] == EXPECTED_ROWS
        and db_reports[0]["sqlite_integrity_check"] == "ok",
        "package_database_rebuilt": db_reports[1]["row_count"] == EXPECTED_ROWS
        and db_reports[1]["sqlite_integrity_check"] == "ok",
        "known_samples_promoted": all(
            next(row for row in rows if row["char"] == char)["struct_name"] == structure
            for char, structure in {"家": "上下", "侵": "左右", "偶": "左右", "孓": "独体字"}.items()
        ),
    }
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "authorized_8105_cnbe32_runtime_promotion",
            "source_copy": str(COPIED_DATASET),
            "runtime_json": str(RUNTIME_JSON),
            "root_database": str(ROOT_DB),
            "package_database": str(PACKAGE_DB),
            "human_decision_id": HUMAN_DECISION_ID,
        },
        "overall_status": "PASS_8105_CNBE32_RUNTIME_PROMOTED" if all(checks.values()) else "BLOCKED",
        "summary": {
            "runtime_rows": len(rows),
            "patched_8105_rows": EXPECTED_PATCHED_ROWS,
            "force_approved_not_patched_rows": EXPECTED_FORCE_APPROVED_NOT_PATCHED,
            "structure_counts": dict(structure_counts),
            "databases_rebuilt": len(db_reports),
        },
        "checks": checks,
        "databases": db_reports,
        "known_samples": {
            char: next(row for row in rows if row["char"] == char)
            for char in ("家", "侵", "偶", "孓", "冁")
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    sample_lines = []
    for char, row in report["known_samples"].items():
        sample_lines.append(
            f"| {char} | U+{int(row['unicode']):04X} | 0x{int(row['cnbe']):08X} | "
            f"{row['radix_name']} | {row['strokes']} | {row['struct_name']} | {row['struct_type']} |"
        )
    return "\n".join(
        [
            "# CNBE 8105 Runtime Promotion",
            "",
            f"- Overall status: `{report['overall_status']}`",
            f"- Runtime rows: {report['summary']['runtime_rows']}",
            f"- Patched 8105 rows: {report['summary']['patched_8105_rows']}",
            f"- Force-approved not patched rows: {report['summary']['force_approved_not_patched_rows']}",
            f"- Databases rebuilt: {report['summary']['databases_rebuilt']}",
            "",
            "This is the authorized promotion from the force-approved 8105 CNBE32",
            "copy into runtime JSON and packaged SQLite databases.",
            "",
            "## Runtime Files",
            "",
            f"- Runtime JSON: `{report['metadata']['runtime_json']}`",
            f"- Root database: `{report['metadata']['root_database']}`",
            f"- Package database: `{report['metadata']['package_database']}`",
            "",
            "## Known Samples",
            "",
            "| Char | Unicode | CNBE | Radical | Strokes | Structure | Structure Type |",
            "|---|---|---:|---|---:|---|---:|",
            *sample_lines,
            "",
        ]
    )


def run() -> dict[str, Any]:
    copied = read_json(COPIED_DATASET)
    model = production_model(copied)
    write_json(RUNTIME_JSON, model)
    db_reports = [rebuild_database(ROOT_DB, model["characters"]), rebuild_database(PACKAGE_DB, model["characters"])]
    report = build_report(model, db_reports)
    write_json(JSON_REPORT, report)
    write_text(MD_REPORT, render_markdown(report))
    return report


def main() -> None:
    report = run()
    print(report["overall_status"])
    print(f"runtime_rows={report['summary']['runtime_rows']}")
    print(f"databases_rebuilt={report['summary']['databases_rebuilt']}")
    for db in report["databases"]:
        print(f"{db['path']} rows={db['row_count']} integrity={db['sqlite_integrity_check']}")


if __name__ == "__main__":
    main()
