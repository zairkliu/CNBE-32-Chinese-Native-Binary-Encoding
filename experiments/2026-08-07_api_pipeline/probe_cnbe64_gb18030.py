#!/usr/bin/env python3
"""Probe CNBE64 layout feasibility for GB18030 alignment.

Layout proposal:
  bits 63..60: version (4)
  bits 59..39: gb18030_pointer (21)
  bit  38:     gb18030_present (1)
  bits 37..36: mapping_status (2) 0=MAPPED 1=CONFLICT 2=MISSING 3=UNKNOWN
  bits 35..32: reserved (4)
  bits 31..0:  CNBE32 preserved (32)
"""

from __future__ import annotations

import gzip
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

VERSION = 1


def gb18030_pointer(ch: str) -> tuple[int, bool]:
    b = ch.encode("gb18030")
    if len(b) == 4:
        ptr = (b[0] - 0x81) * 12600 + (b[1] - 0x30) * 1260 + (b[2] - 0x81) * 10 + (b[3] - 0x30)
    else:
        ptr = (b[0] - 0x81) * 190 + (b[1] - 0x40) - (1 if b[1] > 0x7F else 0)
    return ptr, len(b) == 4


def load_catalog_rows(path: Path, limit: int = 0) -> list[dict]:
    rows = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("id,"):
                continue
            parts = line.split(",")
            ucp = parts[1]
            rows.append(
                {
                    "ucp": ucp,
                    "char": chr(int(ucp[2:], 16)),
                    "cnbe_hex": parts[2],
                    "block": parts[6],
                }
            )
            if limit and len(rows) >= limit:
                break
    return rows


def pack(version: int, pointer: int, status: int) -> int:
    assert 0 <= version < 16
    assert 0 <= pointer < (1 << 21)
    assert 0 <= status < 4
    return (version << 60) | (pointer << 39) | (1 << 38) | (status << 36)


def unpack(code: int) -> dict:
    return {
        "version": (code >> 60) & 0xF,
        "pointer": (code >> 39) & 0x1FFFFF,
        "present": (code >> 38) & 1,
        "status": (code >> 36) & 0x3,
        "reserved": (code >> 32) & 0xF,
        "low32": code & 0xFFFFFFFF,
    }


def main() -> int:
    parser = __import__("argparse").ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows = load_catalog_rows(REPO / "data" / "cnbe_catalog_fixed.csv.gz", limit=args.limit)
    seen: dict[int, str] = {}
    status_counter = Counter()
    codes: set[int] = set()
    failures: list[str] = []
    max_pointer = 0
    sample: list[dict] = []

    for row in rows:
        try:
            ptr, is_four = gb18030_pointer(row["char"])
        except UnicodeEncodeError:
            status = 2
            ptr = 0
            failures.append(row["ucp"])
        else:
            max_pointer = max(max_pointer, ptr)
            status = 1 if ptr in seen else 0
            seen.setdefault(ptr, row["ucp"])
        status_counter[status] += 1
        low32 = int(row["cnbe_hex"], 16)
        code = pack(VERSION, ptr, status) | low32
        codes.add(code)
        if len(sample) < 5:
            sample.append(
                {
                    "ucp": row["ucp"],
                    "char": row["char"],
                    "gb18030_pointer": ptr,
                    "four_byte": is_four,
                    "status": status,
                    "cnbe64": hex(code),
                    "unpack": unpack(code),
                }
            )

    total = len(rows)
    pointer_bits = max_pointer.bit_length() if max_pointer else 0
    result = {
        "schema_version": 1,
        "layout": {
            "version_bits": [63, 60],
            "pointer_bits": [59, 39],
            "present_bit": 38,
            "status_bits": [37, 36],
            "reserved_bits": [35, 32],
            "cnbe32_bits": [31, 0],
        },
        "rows": total,
        "unique_cnbe64": len(codes),
        "unique_cnbe64_rate": round(len(codes) / total, 4) if total else 0.0,
        "max_gb18030_pointer": max_pointer,
        "pointer_bits_needed": pointer_bits,
        "pointer_fits_21bits": max_pointer < (1 << 21),
        "status_counts": {
            "MAPPED": status_counter[0],
            "CONFLICT": status_counter[1],
            "MISSING": status_counter[2],
            "UNKNOWN": status_counter[3],
        },
        "encode_failures": failures[:20],
        "sample": sample,
        "write_gate": "NO_WRITE_TO_RELEASE_DB",
    }
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "cnbe64_gb18030_probe.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "sample"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
