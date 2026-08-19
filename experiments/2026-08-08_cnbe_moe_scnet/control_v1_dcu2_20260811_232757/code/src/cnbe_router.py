# -*- coding: utf-8 -*-
"""CNBE O(1) 路由：位运算 + 预计算专家映射表。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import torch


def build_balanced_mapping(codes: np.ndarray, num_experts: int, mode: int = 2) -> dict:
    """按 CNBE 字段频率贪心构建负载均衡映射。
    mode=2: (radix, struct)；mode=3: (radix, struct, strokes)。
    """
    codes = np.asarray(codes, dtype=np.uint32)
    radix = (codes >> 24) & 0xFF
    struct = (codes >> 15) & 0x0F
    strokes = (codes >> 19) & 0x1F
    if mode == 3:
        keys = (radix << 9) | (struct << 5) | strokes
    else:
        keys = radix.astype(np.uint32) * 16 + struct
    unique, counts = np.unique(keys, return_counts=True)
    order = np.argsort(-counts)
    loads = np.zeros(num_experts, dtype=np.int64)
    mapping = {}
    for idx in order:
        key = int(unique[idx])
        freq = int(counts[idx])
        expert = int(np.argmin(loads))
        if mode == 3:
            mapping[str(key)] = {
                "experts": [expert],
                "freq": freq,
                "radix": key >> 9,
                "struct": (key >> 5) & 0x0F,
                "strokes": key & 0x1F,
            }
        else:
            mapping[str(key)] = {"experts": [expert], "freq": freq, "radix": key // 16, "struct": key % 16}
        loads[expert] += freq
    return {"version": 1, "stats": {"num_experts": num_experts, "mode": mode}, "mapping": mapping}


class CNBERouter:
    """基于 (radix, struct) 的频率均衡映射表，O(1) 查表。"""

    def __init__(
        self,
        num_experts: int = 16,
        mapping_path: str | None = None,
        num_activated: int = 2,
        fallback: int = 0,
    ):
        self.num_experts = num_experts
        self.num_activated = num_activated
        self.fallback = fallback
        mapping = {}
        if mapping_path and Path(mapping_path).exists():
            payload = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
            mapping = payload["mapping"]
        keys_parsed = [int(k) for k in mapping.keys() if str(k).isdigit()]
        self.key_mode = 3 if keys_parsed and max(keys_parsed) >= 256 * 16 else 2
        self.table = np.full(256 * 16 * (32 if self.key_mode == 3 else 1), fallback, dtype=np.int64)
        for key, info in mapping.items():
            try:
                idx = int(key)
            except Exception:  # noqa: BLE001
                continue
            experts = [int(e) for e in info.get("experts", [])]
            if experts:
                self.table[idx] = experts[0] % num_experts
        self.table_t = torch.tensor(self.table, dtype=torch.long)

    def route(self, codes: torch.Tensor) -> torch.Tensor:
        """codes: (batch, seq) 32 位 CNBE 编码 -> (batch, seq, m) 专家索引。"""
        radix = (codes >> 24) & 0xFF
        struct = (codes >> 15) & 0x0F
        if self.key_mode == 3:
            strokes = (codes >> 19) & 0x1F
            flat = (radix << 9) | (struct << 5) | strokes
        else:
            flat = radix * 16 + struct
        primary = self.table_t.to(codes.device)[flat]
        out = torch.stack([primary] * self.num_activated, dim=-1)
        if self.num_activated > 1:
            for k in range(1, self.num_activated):
                out[..., k] = (out[..., k] + k) % self.num_experts
        return out

    @staticmethod
    def flops_speedup(num_experts: int, m: int) -> float:
        return num_experts / m
