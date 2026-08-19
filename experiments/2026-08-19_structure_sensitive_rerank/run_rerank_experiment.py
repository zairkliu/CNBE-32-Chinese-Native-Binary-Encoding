#!/usr/bin/env python3
"""Zero-shot structure-sensitive candidate reranking benchmark.

For each query character, we construct a hard candidate list from its
confusable-character family plus random distractors, then compare:

1. Random ranking
2. Unicode code-point distance
3. CNBE field-weighted distance
4. CNBE bit Hamming distance

The task is to rank the true character first. This is a deterministic
zero-shot proxy for OCR candidate re-ranking and confusable-character
disambiguation.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402


CONFUSABLE_FAMILIES = [
    ["戊", "戌", "戎", "戍"],
    ["己", "已", "巳"],
    ["日", "曰"],
    ["未", "末"],
    ["土", "士"],
    ["人", "入"],
    ["大", "太"],
    ["天", "夭"],
    ["干", "千"],
    ["田", "由", "甲", "申"],
    ["王", "玉"],
    ["我", "找"],
    ["目", "日"],
    ["白", "自"],
    ["月", "用"],
    ["乌", "鸟"],
    ["免", "兔"],
    ["哀", "衰"],
    ["崇", "祟"],
    ["泊", "柏"],
    ["拔", "拨"],
    ["晴", "睛"],
    ["喝", "渴"],
    ["析", "柝"],
    ["冠", "寇"],
    ["冶", "治"],
    ["徒", "徙"],
    ["待", "侍"],
    ["辨", "辩"],
    ["赢", "羸"],
    ["风", "凤"],
    ["冈", "罔"],
    ["余", "佘"],
    ["侯", "候"],
    ["宦", "宧"],
    ["誉", "誊"],
    ["茶", "荼"],
    ["妲", "姮"],
    ["亘", "旦"],
    ["卯", "印"],
]


def rank_of(target: str, candidates: list[str], key) -> int:
    ordered = sorted(candidates, key=key)
    return ordered.index(target) + 1


def evaluate(
    bridge: CNBEKnowledgeBridge,
    families: list[list[str]],
    pool: list[dict],
    seed: int = 42,
    distractors: int = 20,
) -> dict:
    rng = random.Random(seed)
    rows = []
    for family in families:
        available = [ch for ch in family if bridge.lookup(ch) is not None]
        if not available:
            continue
        for query in available:
            for target in available:
                if query == target:
                    continue
                family_chars = [ch for ch in available if ch != query]
                random_pool = [
                    r["char"]
                    for r in rng.sample(pool, distractors)
                    if r["char"] not in available
                ]
                candidates = family_chars + random_pool
                rng.shuffle(candidates)
                unicode_key = lambda c: (abs(ord(query) - ord(c)), ord(c))

                def weighted_key(c):
                    d = bridge.distance(query, c)
                    return (d["field_weighted_distance"] if d else 10**9, ord(c))

                def hamming_key(c):
                    d = bridge.distance(query, c)
                    return (d["bit_hamming_distance"] if d else 10**9, ord(c))

                unicode_rank = rank_of(target, candidates, unicode_key)
                weighted_rank = rank_of(target, candidates, weighted_key)
                hamming_rank = rank_of(target, candidates, hamming_key)
                random_rank = candidates.index(target) + 1
                rows.append(
                    {
                        "query": query,
                        "target": target,
                        "family_size": len(available),
                        "candidate_count": len(candidates),
                        "random_rank": random_rank,
                        "unicode_rank": unicode_rank,
                        "cnbe_weighted_rank": weighted_rank,
                        "cnbe_hamming_rank": hamming_rank,
                    }
                )

    methods = ["random", "unicode", "cnbe_weighted", "cnbe_hamming"]
    summary = {}
    for method in methods:
        ranks = [r[f"{method}_rank"] for r in rows]
        summary[method] = {
            "top1_accuracy": sum(1 for r in ranks if r == 1) / len(ranks),
            "mean_reciprocal_rank": sum(1.0 / r for r in ranks) / len(ranks),
            "mean_rank": sum(ranks) / len(ranks),
        }
    return {"n_queries": len(rows), "summary": summary, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default=str(Path(__file__).parent / "results.json"))
    ap.add_argument("--distractors", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    bridge = CNBEKnowledgeBridge()
    pool = [r for r in bridge._all_rows() if r.get("track") == "standard"]
    result = evaluate(bridge, CONFUSABLE_FAMILIES, pool, seed=args.seed, distractors=args.distractors)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
