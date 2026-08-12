#!/usr/bin/env python3
"""Content-level near-duplicate detection with MinHash on CNBE-char n-grams."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def _signature(
    text: str,
    num_perm: int,
    stride: int,
    a: np.ndarray,
    b: np.ndarray,
) -> np.ndarray:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    if len(cps) < 5:
        return np.full(num_perm, 2**31 - 1, dtype=np.int64)
    windows = np.lib.stride_tricks.sliding_window_view(cps, 5)[::stride]
    weights = np.array([1, 31, 31**2, 31**3, 31**4], dtype=np.uint64)
    h = (windows.astype(np.uint64) @ weights) & 0xFFFFFFFF
    h = h.astype(np.int64)
    p = 2147483647
    sig = np.min((h[:, None] * a[None, :] + b[None, :]) % p, axis=0)
    return sig


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--num-perm", type=int, default=64)
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--size-ratio", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    subset = json.loads(args.subset.read_text(encoding="utf-8"))
    items = [i for i in subset["items"] if Path(i["source"]).exists()]
    rng = np.random.default_rng(args.seed)
    p = 2147483647
    a = rng.integers(1, p - 1, size=args.num_perm, dtype=np.int64)
    b = rng.integers(0, p, size=args.num_perm, dtype=np.int64)
    sigs = []
    sizes = []
    for idx, item in enumerate(items):
        text = Path(item["source"]).read_text(encoding="utf-8")
        sizes.append(len(text))
        sigs.append(_signature(text, args.num_perm, args.stride, a, b))
        if (idx + 1) % 200 == 0:
            print("signed", idx + 1, "files", flush=True)
    sig = np.stack(sigs)
    n = len(items)
    print("signatures", n, "files", flush=True)

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    edges: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if min(sizes[i], sizes[j]) / max(1, max(sizes[i], sizes[j])) < args.size_ratio:
                continue
            sim = float((sig[i] == sig[j]).mean())
            if sim >= args.threshold:
                union(i, j)
                edges.append((i, j, round(sim, 4)))

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    dup_groups = [
        {"members": [items[i]["slug"] for i in members], "count": len(members)}
        for members in groups.values()
        if len(members) > 1
    ]
    dup_groups.sort(key=lambda g: -g["count"])

    report = {
        "subset": subset["name"],
        "files": n,
        "num_perm": args.num_perm,
        "stride": args.stride,
        "threshold": args.threshold,
        "size_ratio": args.size_ratio,
        "groups": dup_groups,
        "edges": [{"a": items[i]["slug"], "b": items[j]["slug"], "similarity": s} for i, j, s in edges],
        "extra_files": sum(g["count"] - 1 for g in dup_groups),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("groups", len(dup_groups), "extra_files", report["extra_files"])
    for g in dup_groups[:20]:
        print(g["count"], g["members"][:4])
    return 0


if __name__ == "__main__":
    sys.exit(main())
