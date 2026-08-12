#!/usr/bin/env python3
"""Quantify expert routing waste in the CNBE-MoE hard-router pipeline.

Reads a balanced expert mapping and optionally a .cnbe corpus, then reports:
- template and token distribution across experts
- padding factor of the vectorized grouped GEMM for one training step
- expert-context slot collapse caused by sharing one route across layers
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def load_mapping(path: Path) -> tuple[dict, int, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = payload["mapping"]
    keys = [int(k) for k in mapping if str(k).isdigit()]
    key_mode = 3 if keys and max(keys) >= 256 * 16 else 2
    expert_stats = {
        "num_experts": int(payload["stats"]["num_experts"]),
        "mode": int(payload["stats"].get("mode", key_mode)),
    }
    return mapping, key_mode, expert_stats


def build_table(mapping: dict, key_mode: int, num_experts: int) -> np.ndarray:
    size = 256 * 16 * (32 if key_mode == 3 else 1)
    table = np.zeros(size, dtype=np.int64)
    for k, info in mapping.items():
        idx = int(k)
        experts = [int(e) for e in info.get("experts", [])]
        if experts:
            table[idx] = experts[0] % num_experts
    return table


def route_step(codes: np.ndarray, table: np.ndarray, num_experts: int, top_k: int) -> np.ndarray:
    radix = (codes >> 24) & 0xFF
    struct = (codes >> 15) & 0x0F
    strokes = (codes >> 19) & 0x1F
    flat = (radix << 9) | (struct << 5) | strokes
    primary = table[flat]
    parts = [primary]
    for k in range(1, top_k):
        parts.append((primary + k) % num_experts)
    return np.concatenate(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mapping", type=Path, required=True)
    ap.add_argument("--cnbe", type=Path)
    ap.add_argument("--vocab", type=Path)
    ap.add_argument("--tokens", type=int, default=8192)
    ap.add_argument("--top-k", type=int, default=2)
    ap.add_argument("--layers", type=int, default=8)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    mapping, key_mode, stats = load_mapping(args.mapping)
    n = stats["num_experts"]
    table = build_table(mapping, key_mode, n)

    tpl_counts = np.zeros(n, dtype=np.int64)
    tok_counts = np.zeros(n, dtype=np.int64)
    for info in mapping.values():
        e = int(info["experts"][0]) % n
        tpl_counts[e] += 1
        tok_counts[e] += int(info.get("freq", 0))

    result: dict = {
        "mapping": str(args.mapping),
        "num_experts": n,
        "key_mode": key_mode,
        "templates": len(mapping),
        "templates_per_expert": {
            "min": int(tpl_counts.min()),
            "max": int(tpl_counts.max()),
            "mean": round(float(tpl_counts.mean()), 3),
            "std": round(float(tpl_counts.std()), 3),
        },
        "tokens_per_expert": {
            "min": int(tok_counts.min()),
            "max": int(tok_counts.max()),
            "mean": round(float(tok_counts.mean()), 3),
            "std": round(float(tok_counts.std()), 3),
        },
    }

    if args.vocab:
        vocab = json.loads(args.vocab.read_text(encoding="utf-8"))
        codes = np.array([int(x) for x in vocab.keys()], dtype=np.int64)
        radix = (codes >> 24) & 0xFF
        struct = (codes >> 15) & 0x0F
        strokes = (codes >> 19) & 0x1F
        flat = (radix << 9) | (struct << 5) | strokes
        _, counts = np.unique(flat, return_counts=True)
        result["vocab_triples"] = int(len(counts))
        result["codes_per_triple"] = {
            "min": int(counts.min()),
            "max": int(counts.max()),
            "mean": round(float(counts.mean()), 3),
        }

    if args.cnbe:
        codes = np.fromfile(args.cnbe, dtype=">u4").astype(np.int64)
        sample = codes[: args.tokens]
        if len(sample) < args.tokens:
            sample = np.resize(sample, args.tokens)
        expert_idx = route_step(sample, table, n, args.top_k)
        counts = np.bincount(expert_idx, minlength=n)
        max_c = int(counts.max())
        rows = int(len(expert_idx))
        slots = n * max_c
        result["step"] = {
            "tokens": int(len(sample)),
            "rows": rows,
            "max_tokens_per_expert": max_c,
            "min_tokens_per_expert": int(counts.min()),
            "mean_tokens_per_expert": round(float(counts.mean()), 3),
            "experts_used": int((counts > 0).sum()),
            "vectorized_slots": slots,
            "padding_factor": round(slots / rows, 3),
        }
        result["layer_slots"] = {
            "actual": n,
            "potential": n * args.layers,
        }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
