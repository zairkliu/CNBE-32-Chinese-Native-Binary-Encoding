#!/usr/bin/env python3
"""End-to-end 37-page Yongle Dadian evaluation: baseline vs variant-map correction."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments/2026-08-05_v1_yongle_ocr_cnbe"))

import run_v1_experiment as v1  # noqa: E402
from cnbe32 import CNBEKnowledgeBridge  # noqa: E402


def main() -> int:
    exp = Path(__file__).resolve().parent
    truth_lib = v1.load_truth_library()
    pages_dir = REPO / "experiments/2026-08-06_paddleocr_vl16" / "pages"
    rules = json.loads(
        (REPO / "experiments/2026-08-06_variant_normalization/variant_rules.json").read_text(
            encoding="utf-8"
        )
    )
    variant_map = {r["ocr"]: r["target"] for r in rules}
    bridge = CNBEKnowledgeBridge()

    page_rows = []
    total_base_correct = 0
    total_truth = 0
    total_fix_correct = 0
    for page, truth_raw in sorted(truth_lib.items()):
        md = pages_dir / f"page_{page:03d}.md"
        if not md.exists():
            continue
        ocr = v1.cjk_clean(md.read_text(encoding="utf-8"))
        truth = v1.cjk_clean(truth_raw)
        base_matches, _, base_subs = v1.align(ocr, truth)
        fixed_ocr = "".join(variant_map.get(c, c) for c in ocr)
        fix_matches, _, fix_subs = v1.align(fixed_ocr, truth)
        truth_chars = list(truth)
        in_db = sum(1 for c in truth_chars if bridge.lookup(c) is not None)
        in_std = sum(
            1
            for c in truth_chars
            if bridge.lookup(c) is not None and bridge.lookup(c).track == "standard"
        )
        page_rows.append(
            {
                "page": page,
                "truth_chars": len(truth_chars),
                "base_matches": base_matches,
                "fix_matches": fix_matches,
                "base_subs": len(base_subs),
                "fix_subs": len(fix_subs),
                "truth_in_db": in_db,
                "truth_in_standard": in_std,
            }
        )
        total_base_correct += base_matches
        total_truth += len(truth_chars)
        total_fix_correct += fix_matches

    summary = {
        "pages": len(page_rows),
        "truth_chars": total_truth,
        "baseline_accuracy": round(total_base_correct / total_truth, 4),
        "variant_map_accuracy": round(total_fix_correct / total_truth, 4),
        "variant_map_gain": round((total_fix_correct - total_base_correct) / total_truth, 4),
    }
    result = {"summary": summary, "pages": page_rows}
    out = exp / "yongle_37p_results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
