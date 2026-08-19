#!/usr/bin/env python3
"""Merge corpus v1 with the national legal/government document subset to create v2."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

V1_ROOT = Path(r"D:\1 训练语料\CNBE中文出版物合并去重_v1")
LEGAL_ROOT = Path(r"D:\1 训练语料\政务法规语料_2026-08-13")
V2_ROOT = Path(r"D:\1 训练语料\CNBE中文出版物合并去重_v2")


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    v1 = json.loads((V1_ROOT / "corpus_manifest.json").read_text(encoding="utf-8"))
    legal = json.loads((LEGAL_ROOT / "corpus_manifest.json").read_text(encoding="utf-8"))
    print("v1", len(v1), "legal", len(legal), flush=True)

    if V2_ROOT.exists():
        print("v2 already exists:", V2_ROOT)
        return 1
    for bucket in ("core", "technical"):
        (V2_ROOT / bucket).mkdir(parents=True, exist_ok=True)

    entries = []
    for entry in v1:
        src = V1_ROOT / entry["bucket"] / f"{entry['slug']}.txt"
        dst = V2_ROOT / entry["bucket"] / f"{entry['slug']}.txt"
        link_or_copy(src, dst)
        entries.append(entry)

    legal_added = 0
    for entry in legal:
        src = LEGAL_ROOT / entry["bucket"] / f"{entry['slug']}.txt"
        dst = V2_ROOT / entry["bucket"] / f"{entry['slug']}.txt"
        link_or_copy(src, dst)
        entries.append(entry)
        legal_added += 1

    entries.sort(key=lambda e: e["slug"])
    (V2_ROOT / "corpus_manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    stats = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "v1_entries": len(v1),
        "legal_entries": legal_added,
        "total_entries": len(entries),
        "core": sum(1 for e in entries if e["bucket"] == "core"),
        "technical": sum(1 for e in entries if e["bucket"] == "technical"),
        "by_batch": {},
    }
    for entry in entries:
        stats["by_batch"].setdefault(entry["batch"], 0)
        stats["by_batch"][entry["batch"]] += 1
    (V2_ROOT / "merge_report.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
