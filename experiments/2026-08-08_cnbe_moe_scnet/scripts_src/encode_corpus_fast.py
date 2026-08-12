#!/usr/bin/env python3
"""Fast CNBE-32 encoding using a Unicode-codepoint lookup table."""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np


def load_lookup(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT char, cnbe FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
    conn.close()
    return {ch: int(code) for ch, code in rows if ch and code is not None}


def encode_fast(text_path: Path, out_path: Path, db_path: str, limit: int) -> dict:
    lookup = load_lookup(db_path)
    table = np.zeros(0x110000, dtype=np.uint32)
    for ch, code in lookup.items():
        cp = ord(ch)
        if cp < len(table):
            table[cp] = code

    text = text_path.read_text(encoding="utf-8")
    if limit and limit > 0:
        text = text[:limit]
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    codes = table[cps].astype(">u4")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(codes.tobytes())
    unknown = int((codes == 0).sum())
    return {
        "total_chars": len(codes),
        "unknown": unknown,
        "coverage": 1 - unknown / len(codes) if len(codes) else 1.0,
        "bytes": out_path.stat().st_size,
        "seconds": 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fast CNBE-32 encoder")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--db", required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    t0 = time.perf_counter()
    stats = encode_fast(args.input, args.output, args.db, args.limit)
    stats["seconds"] = round(time.perf_counter() - t0, 2)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
