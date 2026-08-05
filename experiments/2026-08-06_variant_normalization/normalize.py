#!/usr/bin/env python3
"""Direction-aware variant normalization for ancient OCR output.

Builds rules from `variant_pairs.json` (VL-1.6 residual errors + Unihan variant
relations) and applies them only in the learned OCR->truth direction. A naive
canonical map is intentionally not used: it destroys traditional text.

Usage:
    python3 normalize.py --pages-dir ../2026-08-06_paddleocr_vl16/pages \
        --rules variant_rules.json --out-pages normalized --out-json normalization_eval.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "2026-08-05_v1_yongle_ocr_cnbe"))

import run_v1_experiment as v1  # noqa: E402

CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


class VariantNormalizer:
    def __init__(self, rules: dict[str, str]) -> None:
        self.rules = rules

    def normalize(self, text: str) -> tuple[str, int]:
        out = []
        changes = 0
        for ch in text:
            if ch in self.rules and self.rules[ch] != ch:
                out.append(self.rules[ch])
                changes += 1
            else:
                out.append(ch)
        return "".join(out), changes


def build_rules(variant_pairs_path: Path, min_count: int = 2) -> dict[str, str]:
    pairs = json.loads(variant_pairs_path.read_text(encoding="utf-8"))
    counter: Counter[tuple[str, str]] = Counter((p["ocr"], p["truth"]) for p in pairs)
    rules: dict[str, str] = {}
    for (x, t), n in counter.items():
        if n >= min_count and x != t:
            rules[x] = t
    return rules


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant-pairs", type=Path, default=Path("variant_pairs.json"))
    parser.add_argument("--pages-dir", type=Path, default=Path("../2026-08-06_paddleocr_vl16/pages"))
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--rules-out", type=Path, default=Path("variant_rules.json"))
    parser.add_argument("--out-pages", type=Path, default=Path("normalized"))
    parser.add_argument("--out-json", type=Path, default=Path("normalization_eval.json"))
    parser.add_argument("--report", type=Path, default=Path("NORMALIZATION_REPORT.md"))
    args = parser.parse_args()

    rules = build_rules(args.variant_pairs, args.min_count)
    rule_records = [
        {"ocr": k, "target": v, "min_count": args.min_count, "source": "yongle_vl16_37p_variant_pairs"}
        for k, v in sorted(rules.items())
    ]
    args.rules_out.write_text(
        json.dumps(rule_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    normalizer = VariantNormalizer(rules)
    truth_lib = v1.load_truth_library()
    args.out_pages.mkdir(parents=True, exist_ok=True)

    rb = ra = 0
    rt = 0
    total_changes = 0
    total_correct = 0
    page_rows = []
    for page, truth in sorted(truth_lib.items()):
        src = args.pages_dir / f"page_{page:03d}.md"
        if not src.exists():
            continue
        ocr_text = src.read_text(encoding="utf-8")
        norm_text, changes = normalizer.normalize(ocr_text)
        (args.out_pages / f"page_{page:03d}.md").write_text(norm_text, encoding="utf-8")
        mb, tb, _ = v1.align(ocr_text, truth)
        ma, _, _ = v1.align(norm_text, truth)
        rb += mb
        ra += ma
        rt += tb
        total_changes += changes
        ocr_chars = list(v1.cjk_clean(ocr_text))
        norm_chars = list(v1.cjk_clean(norm_text))
        truth_chars = list(v1.cjk_clean(truth))
        n = min(len(ocr_chars), len(truth_chars))
        correct = sum(
            1
            for i in range(n)
            if ocr_chars[i] != norm_chars[i] and norm_chars[i] == truth_chars[i]
        )
        total_correct += correct
        page_rows.append(
            {
                "page": page,
                "baseline_matched": mb,
                "normalized_matched": ma,
                "changes": changes,
                "correct_changes_approx": correct,
            }
        )

    result = {
        "schema_version": 1,
        "rules_count": len(rules),
        "min_count": args.min_count,
        "truth_chars": rt,
        "baseline_accuracy": round(rb / rt, 4) if rt else 0.0,
        "normalized_accuracy": round(ra / rt, 4) if rt else 0.0,
        "changes": total_changes,
        "correct_changes_approx": total_correct,
        "pages": page_rows,
    }
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    lines = [
        "# Direction-Aware Variant Normalization",
        "",
        f"Date: 2026-08-06",
        "",
        f"- Rules: {len(rules)} (min count {args.min_count} in 37-page VL-1.6 residual pairs)",
        f"- Baseline accuracy: {result['baseline_accuracy']:.4f}",
        f"- Normalized accuracy: {result['normalized_accuracy']:.4f}",
        f"- Changes: {total_changes}",
        f"- Correct changes (position-approx): {total_correct}",
        "",
        "Rules are directional (OCR form -> target form) and must not be applied "
        "in reverse. Naive canonical normalization is intentionally not used.",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
