# -*- coding: utf-8 -*-
"""CNBE 结构路由器：O(1) 查表，未命中回退默认 Top-K。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


class CNBERouter:
    def __init__(self, struct_expert_map: Dict[str, dict], num_experts: int, default_topk: int = 2):
        self.num_experts = num_experts
        self.default_topk = default_topk
        self.lookup: Dict[int, List[int]] = {
            int(key): [int(e) for e in value["experts"]]
            for key, value in struct_expert_map.items()
        }
        default = list(range(self.default_topk))
        self.table = np.full((256 * 16, self.default_topk), default[0], dtype=np.int64)
        for key, experts in self.lookup.items():
            for i, e in enumerate(experts[: self.default_topk]):
                self.table[key, i] = e
        for row in range(256 * 16):
            if row not in self.lookup:
                self.table[row] = default

    def route_codes(self, codes: np.ndarray) -> List[List[int]]:
        return self.route_indices(codes).tolist()

    def route_indices(self, codes: np.ndarray) -> np.ndarray:
        codes = np.asarray(codes).reshape(-1)
        radix = ((codes >> 24) & 0xFF).astype(np.int64)
        struct = ((codes >> 15) & 0x0F).astype(np.int64)
        keys = radix * 16 + struct
        return self.table[keys]

    def route_fields(self, radix, struct):
        return self.lookup.get(int(radix) * 16 + int(struct), list(range(self.default_topk)))

    def get_compute_cost(self, tokens: int, m: int, d: int) -> dict:
        return {
            "tokens": tokens,
            "lookup_flops": tokens,
            "expert_flops": tokens * m * d,
            "total_flops": tokens + tokens * m * d,
        }

    @classmethod
    def from_file(cls, map_path: str, num_experts: int = 16, default_topk: int = 2) -> "CNBERouter":
        payload = json.loads(Path(map_path).read_text(encoding="utf-8"))
        return cls(payload["mapping"], num_experts=num_experts, default_topk=default_topk)
