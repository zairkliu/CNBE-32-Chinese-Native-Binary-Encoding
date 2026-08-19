#!/usr/bin/env python3
"""Train a learned stack on OOF base-model scores for OCR candidate reranking."""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "unicode_abs_diff",
    "cnbe_weighted",
    "cnbe_hamming",
    "radix_same",
    "stroke_same",
    "struct_same",
    "idx_same",
    "ocr_in_standard",
    "left_unicode",
    "right_unicode",
    "cand_left_cnbe",
    "cand_right_cnbe",
    "candidate_freq",
    "cnbe_radix_diff",
    "cnbe_stroke_diff",
    "cnbe_struct_diff",
    "variant_target_match",
]

REPO = Path(__file__).resolve().parents[2]


def rank_of(target: str, candidates: list[dict], key) -> int:
    ordered = sorted(candidates, key=key)
    return [c["candidate"] for c in ordered].index(target) + 1


def metrics(rows: list[tuple[int, str]]) -> dict:
    if not rows:
        return {"top1_accuracy": 0.0, "mean_reciprocal_rank": 0.0, "mean_rank": 0.0}
    ranks = [r for _, r in rows]
    return {
        "top1_accuracy": sum(1 for r in ranks if r == 1) / len(ranks),
        "mean_reciprocal_rank": sum(1.0 / r for r in ranks) / len(ranks),
        "mean_rank": sum(ranks) / len(ranks),
    }


def build_models() -> dict:
    return {
        "lr": LogisticRegression(max_iter=1000),
        "gbdt": HistGradientBoostingClassifier(max_iter=300, random_state=42),
        "mlp": Pipeline(
            [
                ("scale", StandardScaler()),
                ("mlp", MLPClassifier(hidden_layer_sizes=(32,), max_iter=500, random_state=42)),
            ]
        ),
    }


def matrix(records):
    return np.array([[r["features"][k] for k in FEATURES] for r in records], dtype=np.float64)


def oof_base_scores(records, groups):
    X = matrix(records)
    y = np.array([r["label"] for r in records])
    scores = {name: np.zeros(len(records)) for name in build_models()}
    gkf = GroupKFold(n_splits=min(4, len(set(groups))))
    for tr, va in gkf.split(X, y, groups):
        for name, model in build_models().items():
            model.fit(X[tr], y[tr])
            scores[name][va] = model.predict_proba(X[va])[:, 1]
    return scores


def main() -> int:
    exp = Path(__file__).resolve().parent
    records = []
    with (exp / "features.jsonl").open(encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    variant_map = {}
    rules_path = REPO / "experiments/2026-08-06_variant_normalization/variant_rules.json"
    if rules_path.exists():
        for rule in json.loads(rules_path.read_text(encoding="utf-8")):
            variant_map[rule["ocr"]] = rule["target"]
    for r in records:
        r["features"]["variant_target_match"] = int(variant_map.get(r["ocr"]) == r["candidate"])

    pages = sorted({r["page"] for r in records})
    rng = random.Random(42)
    rng.shuffle(pages)
    split = max(1, int(len(pages) * 0.8))
    train_pages = set(pages[:split])
    test_pages = set(pages[split:])
    train_records = [r for r in records if r["page"] in train_pages]
    test_records = [r for r in records if r["page"] in test_pages]

    oof = oof_base_scores(train_records, [r["page"] for r in train_records])
    X = matrix(train_records)
    y = np.array([r["label"] for r in train_records])
    for name, model in build_models().items():
        model.fit(X, y)

    def stack_features(recs, base_scores):
        rows = []
        for r in recs:
            f = r["features"]
            rows.append(
                [
                    base_scores["lr"][0] if isinstance(base_scores["lr"], float) else 0.0,
                ]
            )
        return np.array(rows, dtype=np.float64)

    # Build stack inputs from OOF base scores for train and full-model scores for test.
    def stack_matrix(recs, scores):
        rows = []
        for i, r in enumerate(recs):
            f = r["features"]
            rows.append(
                [
                    scores["lr"][i],
                    scores["gbdt"][i],
                    scores["mlp"][i],
                    f["variant_target_match"],
                    1.0 / (1.0 + f["unicode_abs_diff"]),
                    1.0 / (1.0 + f["cnbe_weighted"]),
                    1.0 / (1.0 + f["cnbe_hamming"]),
                ]
            )
        return np.array(rows, dtype=np.float64)

    train_stack = stack_matrix(train_records, oof)
    test_scores = {}
    X_test = matrix(test_records)
    y_test = np.array([r["label"] for r in test_records])
    for name, model in build_models().items():
        model.fit(X, y)
        test_scores[name] = model.predict_proba(X_test)[:, 1]
    test_stack = stack_matrix(test_records, test_scores)

    stack = LogisticRegression(max_iter=1000)
    stack.fit(train_stack, y)
    stack_probs = stack.predict_proba(test_stack)[:, 1]
    for r, p in zip(test_records, stack_probs):
        r["_stack_score"] = float(p)
    for i, name in enumerate(["lr", "gbdt", "mlp"]):
        for r, p in zip(test_records, test_scores[name]):
            r[f"_base_{name}"] = float(p)

    groups = defaultdict(list)
    for r in test_records:
        groups[(r["page"], r["ocr"], r["truth"], r["error_label"])].append(r)

    methods = ["unicode", "learned_gbdt", "learned_mlp", "stack"]
    collected = {m: [] for m in methods}
    for (page, ocr, truth, label), cands in groups.items():
        collected["unicode"].append(
            (label, rank_of(truth, cands, lambda c: (c["features"]["unicode_abs_diff"], ord(c["candidate"]))))
        )
        collected["learned_gbdt"].append(
            (label, rank_of(truth, cands, lambda c: (-c["_base_gbdt"], ord(c["candidate"]))))
        )
        collected["learned_mlp"].append(
            (label, rank_of(truth, cands, lambda c: (-c["_base_mlp"], ord(c["candidate"]))))
        )
        collected["stack"].append(
            (label, rank_of(truth, cands, lambda c: (-c["_stack_score"], ord(c["candidate"]))))
        )

    summary = {m: metrics(collected[m]) for m in methods}
    result = {
        "pages": len(pages),
        "train_pages": len(train_pages),
        "test_pages": len(test_pages),
        "summary": summary,
    }
    out = exp / "stacking_results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
