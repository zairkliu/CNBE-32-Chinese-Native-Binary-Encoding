#!/usr/bin/env python3
"""Extract all OCR substitution pairs with labels for the rerank experiment."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "experiments/2026-08-06_variant_normalization"))
sys.path.insert(0, str(REPO / "experiments/2026-08-05_v1_yongle_ocr_cnbe"))

import analyze_variants as av  # noqa: E402
import run_v1_experiment as v1  # noqa: E402


def main() -> int:
    exp_dir = Path(__file__).resolve().parent
    pages_dir = REPO / "experiments/2026-08-06_paddleocr_vl16" / "pages"
    unihan_path = REPO / "experiments/2026-08-05_scheme_comparison" / "build" / "Unihan_Variants.txt"

    truth_lib = v1.load_truth_library()
    db_std, _, _, _, _ = v1.load_cnbe(v1.REPO / "data" / "cnbe32.db")
    con = sqlite3.connect(str(v1.REPO / "data" / "cnbe32.db"))
    con.row_factory = sqlite3.Row
    db_all = {r["char"]: dict(r) for r in con.execute("SELECT * FROM cnbe32")}
    con.close()

    edges = av.parse_unihan_variants(unihan_path)
    uf = av.UnionFind()
    for a, b in edges:
        uf.union(a, b)

    def same_variant(a: str, b: str) -> bool:
        return a in uf.parent and b in uf.parent and uf.find(a) == uf.find(b)

    subs: list[dict] = []
    for page, truth in sorted(truth_lib.items()):
        md_path = pages_dir / f"page_{page:03d}.md"
        if not md_path.exists():
            continue
        ocr_text = md_path.read_text(encoding="utf-8")
        _, _, page_subs = v1.align(ocr_text, truth)
        for x, t in page_subs:
            if x == t:
                continue
            if same_variant(x, t):
                label = "variant"
            elif x in db_std and t in db_std and av.field_dist(db_std[x], db_std[t]) <= 64:
                label = "shape_confusable"
            elif t not in db_all:
                label = "truth_not_in_db"
            elif t not in db_std:
                label = "truth_not_in_standard"
            elif x not in db_all:
                label = "ocr_not_in_db"
            else:
                label = "other"
            subs.append(
                {
                    "page": page,
                    "ocr": x,
                    "truth": t,
                    "label": label,
                    "ocr_in_standard": x in db_std,
                    "truth_in_standard": t in db_std,
                    "field_distance": (
                        av.field_dist(db_std[x], db_std[t]) if x in db_std and t in db_std else None
                    ),
                }
            )

    out = exp_dir / "all_substitutions.json"
    out.write_text(json.dumps(subs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(Counter(s["label"] for s in subs))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
