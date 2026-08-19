#!/usr/bin/env python3
"""Run the small-scale real OCR residual reranking experiment."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402


def rank_of(target: str, candidates: list[str], key) -> int:
    ordered = sorted(candidates, key=key)
    return ordered.index(target) + 1


def metrics_for(rows: list[dict], method: str) -> dict:
    ranks = [r[f"{method}_rank"] for r in rows]
    return {
        "top1_accuracy": sum(1 for r in ranks if r == 1) / len(ranks),
        "mean_reciprocal_rank": sum(1.0 / r for r in ranks) / len(ranks),
        "mean_rank": sum(ranks) / len(ranks),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pairs",
        default=str(Path(__file__).parent / "all_substitutions.json"),
    )
    ap.add_argument("--output", default=str(Path(__file__).parent / "results.json"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--candidates", type=int, default=20)
    args = ap.parse_args()

    bridge = CNBEKnowledgeBridge()
    pairs = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    standard_pool = [r["char"] for r in bridge._all_rows() if r.get("track") == "standard"]
    page_chars: dict[int, list[str]] = defaultdict(list)
    for p in pairs:
        if p["truth"] not in page_chars[p["page"]]:
            page_chars[p["page"]].append(p["truth"])

    rng = random.Random(args.seed)
    rows = []
    skipped = 0
    for p in pairs:
        ocr, truth, label = p["ocr"], p["truth"], p["label"]
        if bridge.lookup(ocr) is None or bridge.lookup(truth) is None:
            skipped += 1
            continue
        page_cands = [c for c in page_chars[p["page"]] if c not in (ocr, truth)]
        need = max(0, args.candidates - len(page_cands) - 1)
        distractor_pool = [c for c in standard_pool if c not in (ocr, truth) and c not in page_cands]
        distractors = [c for c in rng.sample(distractor_pool, min(need, len(distractor_pool)))]
        candidates = [truth] + page_cands + distractors
        rng.shuffle(candidates)

        unicode_key = lambda c: (abs(ord(ocr) - ord(c)), ord(c))

        def weighted_key(c):
            d = bridge.distance(ocr, c)
            return (d["field_weighted_distance"] if d else 10**9, ord(c))

        def hamming_key(c):
            d = bridge.distance(ocr, c)
            return (d["bit_hamming_distance"] if d else 10**9, ord(c))

        rows.append(
            {
                "page": p["page"],
                "ocr": ocr,
                "truth": truth,
                "label": label,
                "candidate_count": len(candidates),
                "random_rank": candidates.index(truth) + 1,
                "unicode_rank": rank_of(truth, candidates, unicode_key),
                "cnbe_weighted_rank": rank_of(truth, candidates, weighted_key),
                "cnbe_hamming_rank": rank_of(truth, candidates, hamming_key),
            }
        )

    methods = ["random", "unicode", "cnbe_weighted", "cnbe_hamming"]
    summary = {"overall": {}, "by_label": {}}
    for method in methods:
        summary["overall"][method] = metrics_for(rows, method)
    labels = sorted({r["label"] for r in rows})
    for label in labels:
        sub = [r for r in rows if r["label"] == label]
        summary["by_label"][label] = {method: metrics_for(sub, method) for method in methods}

    result = {
        "seed": args.seed,
        "input_pairs": len(pairs),
        "evaluated_pairs": len(rows),
        "skipped_not_in_db": skipped,
        "label_counts": {label: sum(1 for r in rows if r["label"] == label) for label in labels},
        "summary": summary,
        "rows": rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
