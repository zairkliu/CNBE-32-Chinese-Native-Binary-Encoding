# -*- coding: utf-8 -*-
"""CNBE 路由 vs 传统 Top-K 路由：FLOPs 与实测耗时。"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from step2_cnbe_router import CNBERouter
from step1_build_mapping import load_codes


class TraditionalRouter:
    def __init__(self, num_experts: int, d_model: int, top_k: int = 2, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.num_experts = num_experts
        self.d_model = d_model
        self.top_k = top_k
        self.W = rng.standard_normal((num_experts, d_model)).astype(np.float32)

    def forward(self, x: np.ndarray) -> np.ndarray:
        scores = x @ self.W.T
        probs = np.exp(scores - scores.max(axis=-1, keepdims=True))
        probs /= probs.sum(axis=-1, keepdims=True)
        return np.argpartition(-probs, self.top_k - 1, axis=-1)[:, : self.top_k]

    def get_compute_cost(self, tokens: int) -> int:
        return tokens * self.num_experts * self.d_model


def main() -> int:
    parser = argparse.ArgumentParser(description="CNBE 路由效率基准")
    parser.add_argument("--cnbe", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--num-experts", type=int, default=16)
    parser.add_argument("--d-model", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seq-len", type=int, default=512)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--report", default="outputs/routing_benchmark.json")
    args = parser.parse_args()

    codes = load_codes(args.cnbe)[: args.batch_size * args.seq_len]
    if len(codes) < args.batch_size * args.seq_len:
        codes = np.resize(codes, args.batch_size * args.seq_len)
    codes_seq = codes.reshape(args.batch_size, args.seq_len)

    router = CNBERouter.from_file(args.map, num_experts=args.num_experts)
    trad = TraditionalRouter(args.num_experts, args.d_model, top_k=2)
    x = np.random.default_rng(0).standard_normal((args.batch_size, args.d_model)).astype(np.float32)

    t0 = time.perf_counter()
    for _ in range(args.trials):
        trad.forward(x)
    trad_time = (time.perf_counter() - t0) / args.trials

    t0 = time.perf_counter()
    for _ in range(args.trials):
        router.route_indices(codes_seq)
    cnbe_time = (time.perf_counter() - t0) / args.trials

    tokens = args.batch_size * args.seq_len
    m = 2
    trad_flops = trad.get_compute_cost(tokens)
    cnbe_cost = router.get_compute_cost(tokens, m=m, d=args.d_model)

    results = {
        "num_experts": args.num_experts,
        "d_model": args.d_model,
        "tokens": tokens,
        "traditional_flops": trad_flops,
        "cnbe_flops": cnbe_cost["total_flops"],
        "speedup_flops": trad_flops / cnbe_cost["total_flops"],
        "traditional_time_ms": round(trad_time * 1000, 4),
        "cnbe_time_ms": round(cnbe_time * 1000, 4),
        "speedup_time": round(trad_time / cnbe_time, 2),
        "extrapolated_896_speedup": round(896 / m, 1),
    }
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
