#!/usr/bin/env python3
"""Batch-encode cleaned publication text into CNBE-32 streams.

Reads the cleaner manifest, applies quality filters, and writes one .cnbe
per selected book plus an encode report with per-file coverage.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np


class FastCNBEEncoder:
    def __init__(self, db_path: str):
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT char, cnbe FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
        conn.close()
        self.table = np.zeros(0x110000, dtype=np.uint32)
        for ch, code in rows:
            if ch and code is not None:
                cp = ord(ch)
                if cp < len(self.table):
                    self.table[cp] = int(code)

    def encode(self, text_path: Path, out_path: Path) -> dict:
        text = text_path.read_text(encoding="utf-8")
        cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
        codes = self.table[cps].astype(">u4")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(codes.tobytes())
        unknown = int((codes == 0).sum())
        return {
            "total_chars": int(len(codes)),
            "unknown": unknown,
            "coverage": round(1 - unknown / len(codes), 6) if len(codes) else 1.0,
            "bytes": out_path.stat().st_size,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--min-cjk-ratio", type=float, default=0.3)
    ap.add_argument("--min-chars", type=int, default=1000)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected = [
        f
        for f in manifest["files"]
        if f.get("output_chars", 0) >= args.min_chars
        and f.get("cjk_ratio", 0.0) >= args.min_cjk_ratio
    ]
    print("selected", len(selected), "of", len(manifest["files"]))

    encoder = FastCNBEEncoder(str(args.db))
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {"encoder_db": str(args.db), "files": [], "totals": {}}
    totals = {"total_chars": 0, "unknown": 0, "bytes": 0}
    t0 = time.perf_counter()

    for entry in selected:
        src = Path(entry["output"])
        if not src.exists():
            print("missing", src)
            continue
        out_path = out_dir / f"{entry['slug']}.cnbe"
        stats = encoder.encode(src, out_path)
        stats["slug"] = entry["slug"]
        stats["source"] = str(src)
        report["files"].append(stats)
        totals["total_chars"] += stats["total_chars"]
        totals["unknown"] += stats["unknown"]
        totals["bytes"] += stats["bytes"]
        if (len(report["files"]) % 200) == 0:
            print("encoded", len(report["files"]), "files", flush=True)

    report["totals"] = totals
    report["coverage"] = (
        round(1 - totals["unknown"] / max(1, totals["total_chars"]), 6)
    )
    report["seconds"] = round(time.perf_counter() - t0, 1)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("encoded files:", len(report["files"]))
    print("totals:", totals)
    print("coverage:", report["coverage"], "seconds:", report["seconds"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
