# -*- coding: utf-8 -*-
"""纯文本 -> CNBE-32 二进制流（4B/字，大端）。"""

from __future__ import annotations

import argparse
import sqlite3
import struct
import sys
import time
from pathlib import Path

DEFAULT_DBS = [
    Path(__file__).resolve().parents[1] / "guji-ocr-corrector" / "data" / "cnbe32.db",
    Path(__file__).resolve().parents[1] / "repo" / "data" / "cnbe32.db",
]


def load_lookup(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT char, cnbe FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
    conn.close()
    lookup = {}
    for ch, code in rows:
        if ch and code is not None and ch not in lookup:
            lookup[ch] = int(code)
    return lookup


def encode(text_path: Path, out_path: Path, db_path: str, limit: int) -> dict:
    lookup = load_lookup(db_path)
    text = text_path.read_text(encoding="utf-8")
    if limit and limit > 0:
        text = text[:limit]
    unknown = 0
    t0 = time.perf_counter()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        for ch in text:
            code = lookup.get(ch)
            if code is None:
                code = 0
                unknown += 1
            fh.write(struct.pack(">I", code))
    stats = {
        "total_chars": len(text),
        "unknown": unknown,
        "coverage": 1 - unknown / len(text) if text else 1.0,
        "bytes": out_path.stat().st_size,
        "seconds": round(time.perf_counter() - t0, 2),
    }
    print(f"编码完成: {stats['total_chars']} 字，覆盖 {stats['coverage']:.4%}，{stats['bytes']} B，{stats['seconds']}s")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="CNBE-32 编码")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--db", default="")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    db = args.db or next((str(p) for p in DEFAULT_DBS if p.exists()), "")
    if not db:
        print("找不到 cnbe32.db")
        return 1
    encode(Path(args.input), Path(args.output), db, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
