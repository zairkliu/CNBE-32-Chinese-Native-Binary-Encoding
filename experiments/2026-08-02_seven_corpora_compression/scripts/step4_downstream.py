# -*- coding: utf-8 -*-
"""路由质量代理实验：CNBE 查表路由 vs 学习的线性 Top-K 路由。

注意：本机无真实小 MoE 权重，本脚本提供可控的“结构标签代理任务”：
用真实 CNBE 流生成 (token, 专家标签)，比较两种路由在未见过模板上的准确率。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from step1_build_mapping import gini, load_codes
from step2_cnbe_router import CNBERouter


def main() -> int:
    parser = argparse.ArgumentParser(description="CNBE 路由质量代理验证")
    parser.add_argument("--cnbe", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--num-experts", type=int, default=16)
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--train-tokens", type=int, default=200000)
    parser.add_argument("--test-tokens", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report", default="outputs/routing_quality.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.map).read_text(encoding="utf-8"))
    full_map = payload["mapping"]
    codes = load_codes(args.cnbe)
    radix = ((codes >> 24) & 0xFF).astype(np.int64)
    struct = ((codes >> 15) & 0x0F).astype(np.int64)
    keys = radix * 16 + struct

    # 真实负载与基尼
    routed = np.array([int(full_map[str(k)]["experts"][0]) if str(k) in full_map else 0 for k in keys[: args.test_tokens]])
    true_gini = gini(np.bincount(routed, minlength=args.num_experts).astype(np.float64))

    # 80/20 模板划分：训练路由器只见过 80% 模板
    unique_keys = np.unique(keys)
    rng = np.random.default_rng(args.seed)
    seen = set(int(k) for k in rng.choice(unique_keys, size=int(len(unique_keys) * 0.8), replace=False))
    seen_map = {str(k): full_map[str(k)] for k in seen}

    rng2 = np.random.default_rng(args.seed + 1)
    x = rng2.standard_normal((args.train_tokens, args.d_model)).astype(np.float32)
    labels = np.array([int(full_map[str(k)]["experts"][0]) for k in keys[: args.train_tokens]])

    # 传统路由：线性评分学习（岭回归近似）
    A = x.T @ x + 1e-3 * np.eye(args.d_model)
    b = x.T @ np.eye(args.num_experts)[labels]
    W = np.linalg.solve(A, b)

    test_x = rng2.standard_normal((args.test_tokens, args.d_model)).astype(np.float32)
    test_labels = np.array([int(full_map[str(k)]["experts"][0]) for k in keys[: args.test_tokens]])
    trad_pred = np.argmax(test_x @ W, axis=-1)
    trad_acc = float(np.mean(trad_pred == test_labels))

    cnbe_router = CNBERouter(seen_map, num_experts=args.num_experts)
    cnbe_pred = np.array([cnbe_router.route_fields(radix[i], struct[i])[0] for i in range(args.test_tokens)])
    cnbe_acc = float(np.mean(cnbe_pred == test_labels))

    results = {
        "train_templates": len(seen),
        "test_tokens": args.test_tokens,
        "traditional_accuracy": round(trad_acc, 4),
        "cnbe_accuracy": round(cnbe_acc, 4),
        "accuracy_gap": round(trad_acc - cnbe_acc, 4),
        "expert_load_gini": round(true_gini, 4),
    }
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("说明：这是结构标签代理任务，不等同于真实 MoE 下游任务质量。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
