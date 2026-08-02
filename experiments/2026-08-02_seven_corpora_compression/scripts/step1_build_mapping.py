# -*- coding: utf-8 -*-
"""基于真实 CNBE 流统计 (radix, struct) 频率，构建负载均衡的结构-专家映射表。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_codes(cnbe_path: str):
    data = Path(cnbe_path).read_bytes()
    return np.frombuffer(data, dtype=">u4")


def gini(loads: np.ndarray) -> float:
    s = np.sort(loads.astype(np.float64))
    n = len(s)
    if s.sum() == 0:
        return 0.0
    cum = np.cumsum(s)
    return float((n + 1 - 2 * np.sum(cum) / s.sum()) / n)


def build(cnbe_path: str, out_path: str, num_experts: int = 16, min_freq: int = 1) -> dict:
    codes = load_codes(cnbe_path)
    radix = ((codes >> 24) & 0xFF).astype(np.uint32)
    struct = ((codes >> 15) & 0x0F).astype(np.uint32)
    keys = radix * 16 + struct
    unique, counts = np.unique(keys, return_counts=True)
    order = np.argsort(-counts)

    loads = np.zeros(num_experts, dtype=np.int64)
    mapping = {}
    for idx in order:
        key = int(unique[idx])
        freq = int(counts[idx])
        if freq < min_freq:
            continue
        expert = int(np.argmin(loads))
        mapping[str(key)] = {
            "experts": [expert],
            "freq": freq,
            "radix": key // 16,
            "struct": key % 16,
        }
        loads[expert] += freq

    total = int(len(codes))
    covered = int(sum(v["freq"] for v in mapping.values()))
    stats = {
        "num_experts": num_experts,
        "templates": len(mapping),
        "total_chars": total,
        "covered": covered,
        "coverage": covered / total if total else 0,
        "expert_loads": loads.tolist(),
        "gini": gini(loads),
        "max_min_ratio": float(loads.max() / max(1, loads.min())),
    }
    payload = {"version": 1, "stats": stats, "mapping": mapping}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"模板数: {stats['templates']}，覆盖率: {stats['coverage']:.4%}")
    print(f"专家负载: {loads.tolist()}")
    print(f"基尼系数: {stats['gini']:.4f}，max/min: {stats['max_min_ratio']:.2f}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="构建结构-专家映射表")
    parser.add_argument("--cnbe", required=True)
    parser.add_argument("--output", default="outputs/struct_expert_map.json")
    parser.add_argument("--num-experts", type=int, default=16)
    parser.add_argument("--min-freq", type=int, default=1)
    args = parser.parse_args()
    build(args.cnbe, args.output, args.num_experts, args.min_freq)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
