# -*- coding: utf-8 -*-
"""映射粒度消融：2 字段 vs 3 字段专家映射的负载均衡。"""

from __future__ import annotations

import numpy as np

from src.data import load_codes


def gini_loads(loads: np.ndarray) -> float:
    s = np.sort(loads.astype(float))
    n = len(s)
    if s.sum() == 0:
        return 0.0
    cum = np.cumsum(s)
    return float((n + 1 - 2 * np.sum(cum) / s.sum()) / n)


def build_route(train: np.ndarray, eval: np.ndarray, num_experts: int, mode: int):
    if mode == 2:
        keys = ((train >> 24) & 0xFF) * 16 + ((train >> 15) & 0x0F)
        ekeys = ((eval >> 24) & 0xFF) * 16 + ((eval >> 15) & 0x0F)
        size = 256 * 16
    else:
        keys = (((train >> 24) & 0xFF) << 9) | (((train >> 15) & 0x0F) << 5) | ((train >> 19) & 0x1F)
        ekeys = (((eval >> 24) & 0xFF) << 9) | (((eval >> 15) & 0x0F) << 5) | ((eval >> 19) & 0x1F)
        size = 256 * 16 * 32
    unique, counts = np.unique(keys, return_counts=True)
    order = np.argsort(-counts)
    loads = np.zeros(num_experts)
    table = np.full(size, 0, dtype=np.int64)
    for idx in order:
        key = int(unique[idx])
        freq = int(counts[idx])
        e = int(np.argmin(loads))
        table[key] = e
        loads[e] += freq
    assigned = table[ekeys]
    second = (assigned + 1) % num_experts
    all_e = np.concatenate([assigned, second])
    counts_e = np.bincount(all_e, minlength=num_experts).astype(float)
    return gini_loads(counts_e), counts_e.min(), counts_e.max()


def main() -> int:
    paths = [
        "data/zzjh_294.cnbe",
        "data/jinyong.cnbe",
        "data/caixin.cnbe",
        "data/sushi.cnbe",
    ]
    codes = load_codes(paths, 6_300_000)
    train = codes[:6_000_000]
    eval = codes[6_000_000:6_300_000]
    for n in (16, 64):
        for mode in (2, 3):
            g, mn, mx = build_route(train, eval, n, mode)
            print(f"experts={n} fields={mode} gini={g:.4f} min={mn:.0f} max={mx:.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
