# -*- coding: utf-8 -*-
"""与 gzip 对比并生成 report.md。"""

from __future__ import annotations

import argparse
import gzip
import json
import time
import zlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="压缩基准与报告")
    parser.add_argument("text")
    parser.add_argument("cnbe")
    parser.add_argument("--delta", default="")
    parser.add_argument("--template", default="")
    parser.add_argument("--raw-zlib", default="")
    parser.add_argument("--report", default="report.md")
    parser.add_argument("--meta", default="")
    parser.add_argument("--template-coverage", type=float, default=0.0)
    args = parser.parse_args()

    text_bytes = Path(args.text).read_bytes()
    cnbe_bytes = Path(args.cnbe).read_bytes()

    t0 = time.perf_counter()
    text_gz = gzip.compress(text_bytes, 6)
    gz_time = time.perf_counter() - t0
    text_zlib = zlib.compress(text_bytes, 6)

    rows = [
        ("UTF-8 原文", len(text_bytes), len(text_bytes) / len(text_bytes)),
        ("UTF-8 gzip", len(text_gz), len(text_gz) / len(text_bytes)),
        ("UTF-8 zlib", len(text_zlib), len(text_zlib) / len(text_bytes)),
        ("CNBE-32 定长", len(cnbe_bytes), len(cnbe_bytes) / len(text_bytes)),
        ("CNBE raw+zlib", len(Path(args.raw_zlib).read_bytes()) if args.raw_zlib and Path(args.raw_zlib).exists() else 0, 0),
        ("CNBE delta+zlib", len(Path(args.delta).read_bytes()) if args.delta and Path(args.delta).exists() else 0, 0),
        ("CNBE template+zlib", len(Path(args.template).read_bytes()) if args.template and Path(args.template).exists() else 0, 0),
    ]
    rows = [(name, size, size / len(text_bytes)) for name, size, ratio in rows if size > 0]

    meta = {}
    if args.meta and Path(args.meta).exists():
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))

    lines = [
        "# CNBE-32 压缩实验报告",
        "",
        f"- 数据：資治通鑑（胡三省注 294 卷）",
        f"- 中文字符：{meta.get('total_chars', len(text_bytes))}",
        f"- 唯一字：{meta.get('unique_chars', '?')}，CNBE 覆盖：{meta.get('coverage', '?')}",
        f"- 模板覆盖率（top-64）：{args.template_coverage:.4%}" if args.template_coverage else f"- 模板覆盖率（top-64）：{meta.get('template_coverage', '?')}",
        "",
        "| 方案 | 大小 | 相对原文 |",
        "|---|---:|---:|",
    ]
    for name, size, ratio in rows:
        lines.append(f"| {name} | {size:,} B | {ratio:.4%} |")
    lines.append("")
    lines.append(f"- UTF-8 gzip 耗时：{gz_time:.2f}s")
    lines.append("")
    lines.append("## 结论")
    best = min((r for r in rows if r[0] != "UTF-8 原文"), key=lambda r: r[1])
    if best[0].startswith("UTF-8"):
        lines.append("通用 gzip 仍然最优；CNBE 定长流在该测试集上未超越 gzip，说明"
                     "32 bit/字 的定长形态在纯压缩场景下不占优，其价值应放在字段级"
                     "预测/检索/结构化语义，而非对抗通用压缩器。")
    else:
        lines.append(f"最优方案为 {best[0]}（{best[1]:,} B），CNBE 结构化压缩在该数据集上优于通用 gzip。")
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines), encoding="utf-8")
    for name, size, ratio in rows:
        print(f"{name}: {size:,} B ({ratio:.2%})")
    print("报告:", args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
