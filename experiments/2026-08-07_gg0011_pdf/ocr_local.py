#!/usr/bin/env python3
"""Local PaddleOCR fallback for GG 0011-2009 pages.

Cloud PaddleOCR-VL API returned 401, so this script runs the local PP-OCR
engine and saves per-page boxes/text for later table parsing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent


def main() -> int:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    pages_dir = EXP / "pages"
    out_dir = EXP / "ocr"
    out_dir.mkdir(parents=True, exist_ok=True)
    all_pages = []
    for image in sorted(pages_dir.glob("page_*.png")):
        result = ocr.predict(str(image))
        page = image.stem
        boxes = []
        if result and hasattr(result[0], "get"):
            texts = result[0].get("rec_texts", []) or []
            scores = result[0].get("rec_scores", [0.0] * len(texts)) or []
            polys = result[0].get("rec_polys") or result[0].get("dt_polys") or []
            for text, score, poly in zip(texts, scores, polys):
                pts = [[float(v) for v in p] for p in poly]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                boxes.append(
                    {
                        "text": str(text),
                        "score": float(score),
                        "x0": min(xs),
                        "y0": min(ys),
                        "x1": max(xs),
                        "y1": max(ys),
                    }
                )
        boxes.sort(key=lambda b: (round(b["y0"] / 20), b["x0"]))
        all_pages.append({"page": page, "boxes": boxes})
        (out_dir / f"{page}.json").write_text(
            json.dumps({"page": page, "boxes": boxes}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(page, "boxes", len(boxes))
    (out_dir / "all_pages.json").write_text(
        json.dumps({"engine": "PaddleOCR_PP-OCRv4_local", "pages": all_pages}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
