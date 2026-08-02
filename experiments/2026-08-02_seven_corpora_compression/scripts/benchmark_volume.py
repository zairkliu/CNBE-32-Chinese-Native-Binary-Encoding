# -*- coding: utf-8 -*-
"""CNBE Volume 性能基准：随机定位/片段/搜索 vs gzip 全文解压。"""

from __future__ import annotations

import argparse
import gzip
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cnbe_volume.volume import CNBEVolume, load_maps


def main() -> int:
    parser = argparse.ArgumentParser(description="CNBE Volume 基准")
    parser.add_argument("--volume", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--db", default="")
    parser.add_argument("--report", default="volume_report.md")
    parser.add_argument("--label", default="資治通鑑 294 卷")
    parser.add_argument("--pos", type=int, default=100000)
    parser.add_argument("--span", type=int, default=100)
    parser.add_argument("--random-len", type=int, default=500)
    args = parser.parse_args()

    reverse, forward = load_maps(args.db) if args.db else ({}, {})
    vol = CNBEVolume(args.volume, reverse_map=reverse, forward_map=forward)
    text_bytes = Path(args.text).read_bytes()

    def bench(fn, repeat=3):
        best = float("inf")
        for _ in range(repeat):
            t0 = time.perf_counter()
            fn()
            best = min(best, time.perf_counter() - t0)
        return best

    gz = gzip.compress(text_bytes, 6)

    def gzip_read(pos, n):
        return gzip.decompress(gz)[pos : pos + n]

    t_seek = bench(lambda: vol.seek(args.pos))
    t_extract = bench(lambda: vol.extract(args.pos, args.pos + args.span))
    t_random = bench(lambda: vol.random_passage(args.random_len))
    t_search = bench(lambda: vol.search(struct=1, radix=38, limit=1000))
    t_gzip = bench(lambda: gzip_read(args.pos, args.span))
    t_scan = bench(lambda: sum(1 for _ in vol.stream(0, vol.meta["total_chars"])))

    gz_full = bench(lambda: gzip.decompress(gz))
    vol_size = vol.info()["file_size"]
    ratio_text = vol_size / len(text_bytes)
    ratio_gzip = vol_size / len(gz)
    lines = [
        "# CNBE Volume 基准报告",
        "",
        f"- 数据：{args.label}，{vol.meta['total_chars']:,} 字",
        f"- 卷大小：{vol_size:,} B vs 原文 {len(text_bytes):,} B（{ratio_text:.2%}），vs gzip {len(gz):,} B（{ratio_gzip:.2%}）",
        f"- 页大小：{vol.meta['page_size']}",
        "",
        "| 操作 | CNBE Volume | gzip 全文解压后读取 |",
        "|---|---:|---:|",
        f"| seek({args.pos}) | {t_seek*1000:.3f} ms | - |",
        f"| extract {args.span} 字 | {t_extract*1000:.3f} ms | {t_gzip*1000:.3f} ms（解压后切片） |",
        f"| random_passage({args.random_len}) | {t_random*1000:.3f} ms | - |",
        f"| search(radix=38, struct=1) | {t_search*1000:.3f} ms | 不支持 |",
        f"| 全文流式扫描 | {t_scan:.3f} s | {gz_full:.3f} s（仅解压） |",
        "",
        "## 说明",
        "",
        "CNBE Volume 将整篇 gzip 解压时间分摊为按页 O(1) 解压；gzip 单次读",
        "取需要先全文解压。结构化检索（部首/结构/笔画）为 CNBE Volume 独有能力。",
    ]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
