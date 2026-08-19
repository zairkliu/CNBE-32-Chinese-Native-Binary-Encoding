#!/usr/bin/env python3
"""Train a small learned reranker on CNBE features and compare with baselines."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression


FEATURES = [
    "unicode_abs_diff",
    "cnbe_weighted",
    "cnbe_hamming",
    "radix_same",
    "stroke_same",
    "struct_same",
    "idx_same",
    "ocr_in_standard",
    "truth_in_standard",
    "left_unicode",
    "right_unicode",
    "cand_left_cnbe",
    "cand_right_cnbe",
]

REPO = Path(__file__).resolve().parents[2]


def rank_of(target: str, candidates: list[dict], key) -> int:
    ordered = sorted(candidates, key=key)
    chars = [c["candidate"] for c in ordered]
    return chars.index(target) + 1


def metrics(rows: list[tuple[int, str]]) -> dict:
    if not rows:
        return {"top1_accuracy": 0.0, "mean_reciprocal_rank": 0.0, "mean_rank": 0.0}
    ranks = [r for _, r in rows]
    return {
        "top1_accuracy": sum(1 for r in ranks if r == 1) / len(ranks),
        "mean_reciprocal_rank": sum(1.0 / r for r in ranks) / len(ranks),
        "mean_rank": sum(ranks) / len(ranks),
    }


def main() -> int:
    exp = Path(__file__).resolve().parent
    variant_map = {}
    rules_path = REPO / "experiments/2026-08-06_variant_normalization/variant_rules.json"
    if rules_path.exists():
        for rule in json.loads(rules_path.read_text(encoding="utf-8")):
            variant_map[rule["ocr"]] = rule["target"]

    records = []
    with (exp / "features.jsonl").open(encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    pages = sorted({r["page"] for r in records})
    rng = random.Random(42)
    rng.shuffle(pages)
    split = max(1, int(len(pages) * 0.8))
    train_pages = set(pages[:split])
    test_pages = set(pages[split:])

    def matrix(rs):
        return np.array([[r["features"][k] for k in FEATURES] for r in rs], dtype=np.float64)

    train_records = [r for r in records if r["page"] in train_pages]
    test_records = [r for r in records if r["page"] in test_pages]
    models = {
        "learned_lr": LogisticRegression(max_iter=1000),
        "learned_gbdt": HistGradientBoostingClassifier(max_iter=300, random_state=42),
    }
    for name, clf in models.items():
        clf.fit(matrix(train_records), [r["label"] for r in train_records])
        probs = clf.predict_proba(matrix(test_records))[:, 1]
        for r, p in zip(test_records, probs):
            r[f"_score_{name}"] = float(p)

    groups = defaultdict(list)
    for r in test_records:
        groups[(r["page"], r["ocr"], r["truth"], r["error_label"])].append(r)

    methods = [
        "random",
        "unicode",
        "cnbe_weighted",
        "cnbe_hamming",
        "variant_map",
        "learned_lr",
        "learned_gbdt",
    ]
    collected = {m: [] for m in methods}
    for (page, ocr, truth, label), cands in groups.items():
        shuffled = list(cands)
        rng.shuffle(shuffled)
        random_rank = next(i + 1 for i, c in enumerate(shuffled) if c["candidate"] == truth)
        collected["random"].append((label, random_rank))
        collected["unicode"].append(
            (label, rank_of(truth, cands, lambda c: (c["features"]["unicode_abs_diff"], ord(c["candidate"]))))
        )
        collected["cnbe_weighted"].append(
            (label, rank_of(truth, cands, lambda c: (c["features"]["cnbe_weighted"], ord(c["candidate"]))))
        )
        collected["cnbe_hamming"].append(
            (label, rank_of(truth, cands, lambda c: (c["features"]["cnbe_hamming"], ord(c["candidate"]))))
        )
        mapped = variant_map.get(ocr)
        collected["variant_map"].append(
            (
                label,
                rank_of(
                    truth,
                    cands,
                    lambda c: (0 if mapped is not None and c["candidate"] == mapped else 1, ord(c["candidate"])),
                ),
            )
        )
        for name in models:
            collected[name].append(
                (label, rank_of(truth, cands, lambda c, n=name: (-c[f"_score_{n}"], ord(c["candidate"]))))
            )

    summary = {"overall": {}, "by_label": {}}
    for method in methods:
        summary["overall"][method] = metrics(collected[method])
    labels = sorted({lab for lab, _ in collected["learned_lr"]})
    for label in labels:
        summary["by_label"][label] = {
            method: metrics([r for r in collected[method] if r[0] == label]) for method in methods
        }

    result = {
        "pages": len(pages),
        "train_pages": len(train_pages),
        "test_pages": len(test_pages),
        "train_records": len(train_records),
        "test_records": len(test_records),
        "summary": summary,
    }
    out = exp / "learner_results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
