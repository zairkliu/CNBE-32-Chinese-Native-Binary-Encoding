#!/usr/bin/env python3
"""Build candidate-level features for the learned OCR reranker."""

from __future__ import annotations

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments/2026-08-05_v1_yongle_ocr_cnbe"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402
import run_v1_experiment as v1  # noqa: E402


def cjk_clean(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fff]", "", text)


def main() -> int:
    exp = Path(__file__).resolve().parent
    pairs = json.loads((exp / "all_substitutions.json").read_text(encoding="utf-8"))
    bridge = CNBEKnowledgeBridge()
    freq = v1.load_corpus_freq(
        REPO / "experiments/2026-08-02_seven_corpora_compression" / "data"
    )
    standard_pool = [r["char"] for r in bridge._all_rows() if r.get("track") == "standard"]
    page_chars: dict[int, list[str]] = defaultdict(list)
    page_text: dict[int, str] = {}
    for p in pairs:
        if p["truth"] not in page_chars[p["page"]]:
            page_chars[p["page"]].append(p["truth"])
    pages_dir = REPO / "experiments/2026-08-06_paddleocr_vl16" / "pages"
    for page in page_chars:
        md = pages_dir / f"page_{page:03d}.md"
        if md.exists():
            page_text[page] = cjk_clean(md.read_text(encoding="utf-8"))

    rng = random.Random(42)
    records = []
    skipped = 0
    for p in pairs:
        ocr, truth = p["ocr"], p["truth"]
        if bridge.lookup(ocr) is None or bridge.lookup(truth) is None:
            skipped += 1
            continue
        text = page_text.get(p["page"], "")
        idx = text.find(ocr)
        left = text[idx - 1] if idx > 0 else ""
        right = text[idx + 1] if 0 <= idx + 1 < len(text) else ""
        page_cands = [c for c in page_chars[p["page"]] if c not in (ocr, truth)]
        need = max(0, 20 - len(page_cands) - 1)
        distractor_pool = [c for c in standard_pool if c not in (ocr, truth) and c not in page_cands]
        distractors = rng.sample(distractor_pool, min(need, len(distractor_pool)))
        candidates = [truth] + page_cands + distractors
        rng.shuffle(candidates)
        for cand in candidates:
            d = bridge.distance(ocr, cand)
            if d is None:
                continue
            fields = d["fields"]
            left_d = bridge.distance(cand, left) if left else None
            right_d = bridge.distance(cand, right) if right else None
            so = bridge.lookup(ocr)
            sc = bridge.lookup(cand)
            records.append(
                {
                    "page": p["page"],
                    "ocr": ocr,
                    "truth": truth,
                    "candidate": cand,
                    "error_label": p["label"],
                    "label": int(cand == truth),
                    "features": {
                        "unicode_abs_diff": abs(ord(ocr) - ord(cand)),
                        "cnbe_weighted": d["field_weighted_distance"],
                        "cnbe_hamming": d["bit_hamming_distance"],
                        "radix_same": int(fields["radix_same"]),
                        "stroke_same": int(fields["stroke_same"]),
                        "struct_same": int(fields["struct_same"]),
                        "idx_same": int(fields["index_same"]),
                        "ocr_in_standard": int(bridge.lookup(ocr).track == "standard"),
                        "truth_in_standard": int(bridge.lookup(truth).track == "standard"),
                        "left_unicode": ord(left) if left else 0,
                        "right_unicode": ord(right) if right else 0,
                        "cand_left_cnbe": (
                            left_d["field_weighted_distance"] if left_d else 999
                        ),
                        "cand_right_cnbe": (
                            right_d["field_weighted_distance"] if right_d else 999
                        ),
                        "candidate_freq": freq.get(cand, 0),
                        "truth_freq": freq.get(truth, 0),
                        "cnbe_radix_diff": abs(so.radix - sc.radix),
                        "cnbe_stroke_diff": abs(so.stroke - sc.stroke),
                        "cnbe_struct_diff": abs(so.struct - sc.struct),
                    },
                }
            )

    out = exp / "features.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("records:", len(records), "skipped:", skipped)
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
