#!/usr/bin/env python3
"""Rebuild deterministic ~200MB text shards from per-book corpus files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build(bucket: str, root: Path, target_bytes: int) -> list[Path]:
    src_dir = root / bucket
    shard_dir = root / f"shards_{bucket}"
    shard_dir.mkdir(parents=True, exist_ok=True)
    for old in shard_dir.glob("*.txt"):
        old.unlink()

    files = sorted(src_dir.glob("*.txt"))
    parts: list[str] = []
    size = 0
    shards: list[Path] = []
    for idx, path in enumerate(files):
        text = path.read_text(encoding="utf-8", errors="replace").rstrip("\n") + "\n"
        encoded_len = len(text.encode("utf-8"))
        if parts and size + encoded_len + 2 > target_bytes:
            shard = shard_dir / f"shard_{len(shards):04d}.txt"
            shard.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
            shards.append(shard)
            parts = []
            size = 0
        parts.append(text)
        size += encoded_len + (2 if len(parts) > 1 else 0)
    if parts:
        shard = shard_dir / f"shard_{len(shards):04d}.txt"
        shard.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        shards.append(shard)
    return shards


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--target-bytes", type=int, default=200 * 1024 * 1024)
    args = ap.parse_args()

    for bucket in ("core", "technical"):
        shards = build(bucket, args.root, args.target_bytes)
        total = sum(p.stat().st_size for p in shards)
        print(bucket, "shards", len(shards), "bytes", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
