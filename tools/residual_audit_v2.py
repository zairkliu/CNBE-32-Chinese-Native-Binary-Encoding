#!/usr/bin/env python3
"""Audit v1 corpus for residual copyright/watermark noise and manifest drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

HEADER_PATTERNS = [
    "版權信息",
    "版权信息",
    "版权声明",
    "版权所有",
    "版权页",
    "版權頁",
    "CAEBN",
    "CIP",
    "ISBN",
    "书号",
    "書號",
    "定价",
    "定價",
    "互联网出版许可证",
    "互聯網出版許可證",
    "首次发布",
    "首次發佈",
    "更新时间",
    "更新時間",
    "上架建议",
    "上架建議",
    "北京中文在线数字出版股份有限公司",
    "本电子书由",
    "本電子書由",
    "本书著作权为",
    "本書著作權為",
    "非经书面授权",
    "非經書面授權",
    "DNA-BN",
    "电子邮箱",
    "電子郵箱",
    "service@",
    "客服热线",
    "客服熱線",
    "团购热线",
    "團購熱線",
]

FOOTER_PATTERNS = [
    "All rights reserved",
    "ALL RIGHTS RESERVED",
    "No part of this",
    "版本：v1.0",
    "本书仅供个人学习之用",
    "请购买正版书籍",
    "制作说明",
    "製作說明",
    "青苹果数据中心",
    "客服热线",
    "客服熱線",
    "团购热线",
    "團購熱線",
    "版权所有",
    "版权信息",
    "版權信息",
    "出版信息",
    "Table of Contents",
    "所有权利",
    "翻印必究",
    "本电子书由",
    "本電子書由",
    "非经书面授权",
    "非經書面授權",
    "本书著作权为",
    "本書著作權為",
    "DNA-BN",
]

WATERMARK_PATTERNS = [
    re.compile(r"【更多新书朋友圈[^】]*】"),
    re.compile(r"【更多新書朋友圈[^】]*】"),
    re.compile(r"更多新书朋友圈免费首发，微信[^\s，。；】]*"),
    re.compile(r"更多新書朋友圈免費首發，微信[^\s，。；】]*"),
]


def cjk_count(text: str) -> int:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    mask = (
        ((cps >= 0x4E00) & (cps <= 0x9FFF))
        | ((cps >= 0x3400) & (cps <= 0x4DBF))
        | ((cps >= 0xF900) & (cps <= 0xFAFF))
    )
    return int(mask.sum())


def logical_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_entry(entry: dict, root: Path) -> dict:
    path = root / entry["bucket"] / f"{entry['slug']}.txt"
    text = path.read_text(encoding="utf-8", errors="replace")
    chars = len(text)
    cjk = cjk_count(text)
    digest = logical_sha256(text)
    lines = text.split("\n")
    head = "\n".join(lines[:80])
    tail = "\n".join(lines[-80:])
    header_hits = sorted({p for p in HEADER_PATTERNS if p.lower() in head.lower()})
    footer_hits = sorted({p for p in FOOTER_PATTERNS if p.lower() in tail.lower()})
    watermark_count = 0
    watermark_hits = []
    for pattern in WATERMARK_PATTERNS:
        hits = pattern.findall(text)
        if hits:
            watermark_count += len(hits)
            watermark_hits.extend(hits[:5])
    flags = []
    if header_hits:
        flags.append("header")
    if footer_hits:
        flags.append("footer")
    if watermark_count:
        flags.append("watermark")
    return {
        "slug": entry["slug"],
        "bucket": entry["bucket"],
        "batch": entry.get("batch"),
        "chars": chars,
        "cjk": cjk,
        "manifest_chars": entry.get("chars"),
        "manifest_cjk": entry.get("cjk"),
        "manifest_sha256_ok": digest == entry.get("sha256"),
        "flags": flags,
        "header_hits": header_hits,
        "footer_hits": footer_hits,
        "watermark_count": watermark_count,
        "watermark_samples": watermark_hits,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(
        (args.root / "corpus_manifest.json").read_text(encoding="utf-8")
    )
    t0 = time.perf_counter()
    entries = [scan_entry(entry, args.root) for entry in manifest]
    print("scanned", len(entries), "files in", round(time.perf_counter() - t0, 1), "s")

    flagged = [e for e in entries if e["flags"]]
    headers = [e for e in entries if "header" in e["flags"]]
    footers = [e for e in entries if "footer" in e["flags"]]
    watermarks = [e for e in entries if "watermark" in e["flags"]]
    drift = [e for e in entries if not e["manifest_sha256_ok"]]
    stats_drift = [
        e
        for e in entries
        if e["chars"] != e["manifest_chars"] or e["cjk"] != e["manifest_cjk"]
    ]

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(args.root),
        "scanned": len(entries),
        "flagged": len(flagged),
        "header_files": len(headers),
        "footer_files": len(footers),
        "watermark_files": len(watermarks),
        "manifest_sha256_drift": len(drift),
        "manifest_stats_drift": len(stats_drift),
        "summary": {
            "header": headers,
            "footer": footers,
            "watermark": watermarks,
            "manifest_drift": drift,
            "stats_drift": stats_drift,
        },
        "entries": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print("flagged:", len(flagged))
    print("header:", len(headers), "footer:", len(footers), "watermark:", len(watermarks))
    print("sha256 drift:", len(drift), "stats drift:", len(stats_drift))
    print("saved", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
