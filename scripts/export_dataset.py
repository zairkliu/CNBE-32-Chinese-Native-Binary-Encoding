#!/usr/bin/env python3
"""Export CNBE-32 runtime annotations to ML-consumable JSONL (+ optional Parquet).

PDR reference: WS-1 (dataset release), requirements WS1-R1 .. WS1-R4.

Design rules:
- Reads from the repository SQLite runtime database (data/cnbe32.db) by default.
- Schema-tolerant: column names are resolved by candidate lists so the script
  keeps working if the runtime schema evolves.
- Honest evidence tiers: if the source carries no evidence-tier column, the
  tier is emitted as "unresolved" with tier_source="default_no_source".
  Never fabricate a tier the source does not carry.
- Deterministic: rows are ordered by Unicode code point; the manifest records
  SHA256 of every output. Re-running on the same input yields identical bytes.
- Stdlib only. Parquet output is optional and requires pandas+pyarrow.

Usage:
    python scripts/export_dataset.py \
        --db data/cnbe32.db \
        --out datasets/8105 \
        [--scope-file path/to/8105_chars.txt]   # one character per line
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

SCRIPT_VERSION = "0.1.0"

EVIDENCE_TIERS = (
    "national_standard",
    "standard_derived",
    "agent_standard",
    "source_gap",
    "unresolved",
)

# Candidate column names resolved against the live schema, most preferred first.
COL_CANDIDATES = {
    "char": ("char", "hanzi", "character", "glyph"),
    "code": ("code", "cnbe32", "cnbe", "cnbe_code"),
    "radical_id": ("radix", "radical_id", "radical", "radix_id"),
    "stroke_count": ("stroke", "stroke_count", "strokes"),
    "structure_id": ("struct", "struct_id", "structure_id", "structure"),
    "structure_name": ("struct_name", "structure_name"),
    "glyph_index": ("index", "glyph_index", "idx"),
    "ext": ("ext", "extension"),
    "evidence_tier": ("evidence_tier", "tier", "evidence_level"),
    "review_status": ("review_status", "status", "review_state"),
}

RADIX_SHIFT = 24
STROKE_SHIFT = 19
STRUCT_SHIFT = 15
INDEX_SHIFT = 4
EXT_SHIFT = 0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_columns(db_path: Path) -> tuple[sqlite3.Connection, dict[str, str | None]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(cnbe32)")}
    if not cols:
        conn.close()
        raise SystemExit(f"table 'cnbe32' not found or has no columns in {db_path}")
    resolved: dict[str, str | None] = {}
    for field, candidates in COL_CANDIDATES.items():
        resolved[field] = next((c for c in candidates if c in cols), None)
    if resolved["char"] is None:
        conn.close()
        raise SystemExit("no character column found (tried: char/hanzi/character/glyph)")
    return conn, resolved


def _fields_from_code(code: int) -> dict[str, int]:
    return {
        "radical_id": (code >> RADIX_SHIFT) & 0xFF,
        "stroke_count": (code >> STROKE_SHIFT) & 0x1F,
        "structure_id": (code >> STRUCT_SHIFT) & 0x0F,
        "glyph_index": (code >> INDEX_SHIFT) & 0x7FF,
        "ext": (code >> EXT_SHIFT) & 0x0F,
    }


def export_dataset(
    db_path: Path,
    out_dir: Path,
    scope_file: Path | None = None,
    table: str = "cnbe32",
) -> dict:
    """Export the runtime table to JSONL and write a SHA256 manifest."""
    conn, col = _resolve_columns(db_path)

    scope: set[str] | None = None
    if scope_file is not None:
        scope = {
            line.strip()
            for line in scope_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    select_cols = sorted({c for c in col.values() if c})
    quoted = ", ".join(f'"{c}"' for c in select_cols)
    rows = conn.execute(f'SELECT {quoted} FROM "{table}" ORDER BY "{col["char"]}"').fetchall()
    conn.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "cnbe32_annotations.jsonl"

    tier_dist = {t: 0 for t in EVIDENCE_TIERS}
    n_rows = 0
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            char = row[col["char"]]
            if not isinstance(char, str) or len(char) != 1:
                continue
            cp = ord(char)
            if col["code"] is not None and row[col["code"]] is not None:
                code = int(row[col["code"]])
                derived = _fields_from_code(code)
            else:
                code = None
                derived = {}

            def pick(field: str):
                name = col[field]
                if name is not None and row[name] is not None:
                    return row[name]
                return derived.get(field)

            tier = col["evidence_tier"] and row[col["evidence_tier"]]
            if tier in EVIDENCE_TIERS:
                tier_source = "source_column"
            else:
                tier, tier_source = "unresolved", "default_no_source"

            record = {
                "unicode_cp": f"U+{cp:04X}",
                "char": char,
                "radical_id": pick("radical_id"),
                "stroke_count": pick("stroke_count"),
                "structure_id": pick("structure_id"),
                "structure_name": (row[col["structure_name"]] if col["structure_name"] else None),
                "glyph_index": pick("glyph_index"),
                "ext": pick("ext"),
                "cnbe32_hex": (f"0x{code:08X}" if code is not None else None),
                "evidence_tier": tier,
                "tier_source": tier_source,
                "review_status": (row[col["review_status"]] if col["review_status"] else None),
                "source_refs": [],
                "in_8105": (char in scope if scope is not None else None),
            }
            tier_dist[tier] += 1
            n_rows += 1
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    outputs = {"jsonl": str(jsonl_path)}

    parquet_path = out_dir / "cnbe32_annotations.parquet"
    try:
        import pandas as pd  # noqa: PLC0415

        pd.read_json(jsonl_path, lines=True).to_parquet(parquet_path, index=False)
        outputs["parquet"] = str(parquet_path)
    except Exception:
        parquet_path = None  # optional output; absence is not an error

    manifest = {
        "dataset": "cnbe32-annotations",
        "script_version": SCRIPT_VERSION,
        "source_db": str(db_path),
        "source_commit": os.environ.get("GITHUB_SHA", "unknown"),
        "scope_filter": (str(scope_file) if scope_file else None),
        "row_count": n_rows,
        "evidence_tier_distribution": tier_dist,
        "schema": [
            "unicode_cp", "char", "radical_id", "stroke_count", "structure_id",
            "structure_name", "glyph_index", "ext", "cnbe32_hex",
            "evidence_tier", "tier_source", "review_status", "source_refs", "in_8105",
        ],
        "outputs": {
            name: {"path": p, "sha256": _sha256(Path(p))} for name, p in outputs.items()
        },
    }
    manifest_path = out_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=Path("data/cnbe32.db"))
    parser.add_argument("--out", type=Path, default=Path("datasets/8105"))
    parser.add_argument("--scope-file", type=Path, default=None,
                        help="text file with one 8105 character per line")
    args = parser.parse_args(argv)

    if not args.db.exists():
        raise SystemExit(f"database not found: {args.db}")
    manifest = export_dataset(args.db, args.out, args.scope_file)
    print(json.dumps({
        "row_count": manifest["row_count"],
        "evidence_tier_distribution": manifest["evidence_tier_distribution"],
        "outputs": manifest["outputs"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
