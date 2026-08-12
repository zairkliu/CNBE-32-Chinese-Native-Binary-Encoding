#!/usr/bin/env python3
"""Stratified manual audit sampling for the merged CNBE corpus."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path


def sample_by_stratum(entries: list[dict], stratum: str, n: int, rng: random.Random) -> list[dict]:
    pool = [e for e in entries if e["bucket"] == stratum]
    if not pool:
        return []
    return rng.sample(pool, min(n, len(pool)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("quality_check"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--total", type=int, default=40)
    args = ap.parse_args()

    manifest = json.loads(
        (args.root / "corpus_manifest.json").read_text(encoding="utf-8")
    )
    rng = random.Random(args.seed)
    technical_n = max(5, args.total // 8)
    guji_n = max(5, args.total // 8)
    remaining = args.total - technical_n - guji_n
    pub_pool = [e for e in manifest if e["batch"] != "guji" and e["bucket"] == "core"]
    core_pub = [e for e in pub_pool if e["bucket"] == "core"]
    batch_groups: dict[str, list[dict]] = {}
    for e in core_pub:
        batch_groups.setdefault(e["batch"], []).append(e)

    sample: list[dict] = []
    sample += sample_by_stratum(manifest, "technical", technical_n, rng)
    sample += rng.sample([e for e in manifest if e["batch"] == "guji"], guji_n)
    batch_names = sorted(batch_groups)
    share = remaining / max(1, len(batch_names))
    for i, batch in enumerate(batch_names):
        n = int(share) + (1 if i < remaining - int(share) * len(batch_names) else 0)
        sample += rng.sample(batch_groups[batch], min(n, len(batch_groups[batch])))

    sample = sorted(
        sample,
        key=lambda e: (
            e["bucket"] != "core",
            e["batch"],
            -e["chars"],
        ),
    )
    args.output_dir = args.root / args.output_dir
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "manual_sample_40.csv"
    md_path = args.output_dir / "manual_sample_40.md"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "序号",
                "slug",
                "桶",
                "批次",
                "字符数",
                "中文占比",
                "乱码检查",
                "排版残留",
                "段落完整性",
                "古籍无污染",
                "元数据一致",
            ]
        )
        for i, e in enumerate(sample, 1):
            writer.writerow(
                [
                    i,
                    e["slug"],
                    e["bucket"],
                    e["batch"],
                    e["chars"],
                    e["cjk_ratio"],
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )

    lines = [
        "# 人工抽检清单（40 本）",
        "",
        f"随机种子：`{args.seed}`，抽取数：`{len(sample)}`",
        "",
        "| 序号 | 桶 | 批次 | 书名 | 字符数 | 中文占比 | 乱码 | 排版 | 完整 | 古籍 | 元数据 |",
        "|---|---|---|---|---:|---:|---|---|---|---|---|",
    ]
    for i, e in enumerate(sample, 1):
        lines.append(
            f"| {i} | {e['bucket']} | {e['batch']} | {e['name']} | "
            f"{e['chars']:,} | {e['cjk_ratio']:.3f} |  |  |  |  |  |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("sample", len(sample))
    print("saved", csv_path)
    print("saved", md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
