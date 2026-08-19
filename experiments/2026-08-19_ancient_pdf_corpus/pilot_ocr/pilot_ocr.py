#!/usr/bin/env python3
"""Small-scale ancient PDF OCR pilot using poppler + deepseek-ocr + CNBE coverage."""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from cnbe32 import CNBEKnowledgeBridge  # noqa: E402


PDFINFO = r"C:\Users\zairk\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdfinfo.exe"
PDFTOPPM = r"C:\Users\zairk\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"


def ollama_ocr(image_path: Path, model: str = "deepseek-ocr", timeout: int = 300) -> str:
    payload = {
        "model": model,
        "prompt": "OCR the image",
        "images": [base64.b64encode(image_path.read_bytes()).decode("ascii")],
        "stream": False,
        "options": {"temperature": 0.0},
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return str(data.get("response", "")).strip()


def cjk(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fff]", "", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pdf",
        default=r"D:\古籍\【古籍】永乐大典219本.散本收集✔\永乐大典（明嘉靖隆庆间内府重写本）\永乐大典.卷913-914.尸字.明嘉靖隆庆间内府重写本.pdf",
    )
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=2)
    ap.add_argument("--dpi", type=int, default=60)
    ap.add_argument("--out", default=str(Path(__file__).parent / "output"))
    args = ap.parse_args()

    pdf = Path(args.pdf)
    out = Path(args.out)
    pages_dir = out / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    prefix = str(pages_dir / "page")

    subprocess.run(
        [
            PDFTOPPM,
            "-f",
            str(args.first),
            "-l",
            str(args.last),
            "-r",
            str(args.dpi),
            "-png",
            str(pdf),
            prefix,
        ],
        check=True,
    )

    bridge = CNBEKnowledgeBridge()
    page_results = []
    for png in sorted(pages_dir.glob("*.png")):
        t0 = time.perf_counter()
        text = ollama_ocr(png)
        txt_path = png.with_suffix(".txt")
        txt_path.write_text(text, encoding="utf-8")
        cjk_text = cjk(text)
        chars = list(cjk_text)
        in_db = [c for c in chars if bridge.lookup(c) is not None]
        in_standard = [c for c in chars if bridge.lookup(c) is not None and bridge.lookup(c).track == "standard"]
        page_results.append(
            {
                "page": png.name,
                "chars": len(chars),
                "unique_chars": len(set(chars)),
                "in_db": len(in_db),
                "in_standard": len(in_standard),
                "coverage_db": round(len(in_db) / len(chars), 4) if chars else 0.0,
                "coverage_standard": round(len(in_standard) / len(chars), 4) if chars else 0.0,
                "elapsed": round(time.perf_counter() - t0, 2),
                "text_preview": text[:120],
            }
        )
        print(json.dumps(page_results[-1], ensure_ascii=False), flush=True)

    result = {
        "pdf": str(pdf),
        "first": args.first,
        "last": args.last,
        "pages": page_results,
        "summary": {
            "pages": len(page_results),
            "total_chars": sum(r["chars"] for r in page_results),
            "coverage_db_avg": round(
                sum(r["coverage_db"] for r in page_results) / len(page_results), 4
            )
            if page_results
            else 0.0,
        },
    }
    (out / "pilot_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("saved:", out / "pilot_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
