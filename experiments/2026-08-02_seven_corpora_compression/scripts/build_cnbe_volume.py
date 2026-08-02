# -*- coding: utf-8 -*-
"""构建 CNBE Volume：分页 zlib + 8B/页索引 + 位图摘要。"""

from __future__ import annotations

import argparse
import sys
import struct
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cnbe_volume.volume import HEADER_SIZE, MAGIC, SUMMARY_SIZE, load_reverse_map


def build(cnbe_path: str, out_path: str, page_size: int = 1024, compress_level: int = 6, db_path: str = "") -> dict:
    data = Path(cnbe_path).read_bytes()
    total_chars = len(data) // 4
    total_pages = (total_chars + page_size - 1) // page_size
    index_offset = HEADER_SIZE
    data_offset = index_offset + total_pages * 8

    index = bytearray()
    page_summaries = bytearray()
    t0 = time.perf_counter()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(b"\x00" * HEADER_SIZE)
        fh.write(b"\x00" * (total_pages * 8))
        cur = data_offset
        for p in range(total_pages):
            chunk = data[p * page_size * 4 : (p + 1) * page_size * 4]
            codes = [struct.unpack_from(">I", chunk, i * 4)[0] for i in range(len(chunk) // 4)]
            packed = zlib.compress(chunk, compress_level)
            index += struct.pack("<II", cur, len(packed))
            rb = bytearray(32)
            sb = bytearray(32)
            stb = bytearray(2)
            for code in codes:
                radix = (code >> 24) & 0xFF
                strokes = (code >> 19) & 0x1F
                struct_t = (code >> 15) & 0x0F
                rb[radix // 8] |= 1 << (radix % 8)
                sb[strokes // 8] |= 1 << (strokes % 8)
                stb[struct_t // 8] |= 1 << (struct_t % 8)
            page_summaries += rb + sb + stb
            fh.write(packed)
            cur += len(packed)
        summary_offset = cur
        fh.write(page_summaries)
        fh.seek(index_offset)
        fh.write(index)

        header = MAGIC + struct.pack(
            "<8I",
            1,
            total_chars,
            len(set(struct.unpack_from(">I", data, i * 4)[0] for i in range(total_chars))),
            page_size,
            total_pages,
            index_offset,
            data_offset,
            compress_level,
        )
        header = header.ljust(HEADER_SIZE, b"\x00")
        fh.seek(0)
        fh.write(header)

    unique = len(set(struct.unpack_from(">I", data, i * 4)[0] for i in range(total_chars)))
    stats = {
        "total_chars": total_chars,
        "unique_codes": unique,
        "page_size": page_size,
        "total_pages": total_pages,
        "input_bytes": len(data),
        "volume_bytes": Path(out_path).stat().st_size,
        "ratio_to_cnbe": Path(out_path).stat().st_size / len(data),
        "summary_offset": summary_offset,
        "seconds": round(time.perf_counter() - t0, 2),
    }
    print(f"CNBE Volume 构建完成: {stats['volume_bytes']:,} B（CNBE 的 {stats['ratio_to_cnbe']:.2%}）")
    print(f"页数 {total_pages}，页大小 {page_size}，耗时 {stats['seconds']}s")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 CNBE Volume")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--page-size", type=int, default=1024)
    parser.add_argument("--compress-level", type=int, default=6)
    parser.add_argument("--db", default="")
    args = parser.parse_args()
    build(args.input, args.output, args.page_size, args.compress_level, args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
