# -*- coding: utf-8 -*-
"""预测 + 残差压缩：delta / template / raw，全部 zlib 压缩并做无损校验。"""

from __future__ import annotations

import argparse
import array
import json
import struct
import time
import zlib
from pathlib import Path

TEMPLATE_MARKER = 0xF0000000


def load_codes(path: Path):
    data = path.read_bytes()
    return [struct.unpack(">I", data[i : i + 4])[0] for i in range(0, len(data), 4)]


def delta_residuals(codes):
    out = array.array("I")
    prev = 0
    for i, code in enumerate(codes):
        if i == 0:
            out.append(code)
        else:
            out.append((code - prev) & 0xFFFFFFFF)
        prev = code
    return out


def delta_restore(residuals, n):
    out = []
    prev = 0
    for i, r in enumerate(residuals):
        code = r if i == 0 else (prev + r) & 0xFFFFFFFF
        out.append(code)
        prev = code
    return out[:n]


def template_transform(codes, template_map, reverse=False):
    if reverse:
        out = []
        for code in codes:
            if (code & TEMPLATE_MARKER) == TEMPLATE_MARKER:
                tid = (code >> 15) & 0x3F
                payload = code & 0x7FFF
                info = template_map[str(tid)]
                out.append(((info["radix"] & 0xFF) << 24) | ((info["stroke"] & 0x1F) << 19) | ((info["struct"] & 0x0F) << 15) | payload)
            else:
                out.append(code)
        return out
    lookup = {}
    for tid, info in template_map.items():
        lookup[(info["radix"], info["stroke"], info["struct"])] = int(tid)
    out = []
    hit = 0
    for code in codes:
        key = ((code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F)
        tid = lookup.get(key)
        if tid is not None and (code & TEMPLATE_MARKER) == 0:
            out.append(TEMPLATE_MARKER | (tid << 15) | (code & 0x7FFF))
            hit += 1
        else:
            out.append(code)
    return out, hit


def main() -> int:
    parser = argparse.ArgumentParser(description="预测压缩")
    parser.add_argument("cnbe")
    parser.add_argument("template")
    parser.add_argument("output_prefix")
    parser.add_argument("--level", type=int, default=6)
    parser.add_argument("--verify", action="store_true", default=True)
    args = parser.parse_args()

    t0 = time.perf_counter()
    codes = load_codes(Path(args.cnbe))
    template_map = json.loads(Path(args.template).read_text(encoding="utf-8"))

    delta = delta_residuals(codes)
    d_bytes = delta.tobytes()
    d_z = zlib.compress(d_bytes, args.level)
    Path(args.output_prefix).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{args.output_prefix}_delta.zlib").write_bytes(d_z)
    d_ok = True
    if args.verify:
        restored = delta_restore(array.array("I", zlib.decompress(d_z)), len(codes))
        d_ok = restored == codes

    templated, hits = template_transform(codes, template_map)
    t_bytes = array.array("I", templated).tobytes()
    t_z = zlib.compress(t_bytes, args.level)
    Path(f"{args.output_prefix}_template.zlib").write_bytes(t_z)
    t_ok = True
    if args.verify:
        restored = template_transform(array.array("I", zlib.decompress(t_z)), template_map, reverse=True)
        t_ok = restored == codes

    raw_z = zlib.compress(Path(args.cnbe).read_bytes(), args.level)
    Path(f"{args.output_prefix}_raw.zlib").write_bytes(raw_z)

    original = len(codes) * 4
    print(f"原始 CNBE: {original:,} B")
    print(f"delta+zlib: {len(d_z):,} B ({len(d_z)/original:.2%}) 无损校验: {d_ok}")
    print(f"template+zlib: {len(t_z):,} B ({len(t_z)/original:.2%}) 模板命中 {hits}/{len(codes)} 无损校验: {t_ok}")
    print(f"raw+zlib: {len(raw_z):,} B ({len(raw_z)/original:.2%})")
    print(f"耗时: {time.perf_counter()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
