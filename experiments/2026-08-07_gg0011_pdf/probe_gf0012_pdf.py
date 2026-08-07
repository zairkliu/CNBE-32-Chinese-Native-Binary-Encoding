#!/usr/bin/env python3
"""Probe text layer and layout of the official GF0012-2009 PDF."""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
ZIP_PATH = ROOT / "authoritative_sources" / "gf0012_zip.bin"
PDF_DIR = ROOT / "authoritative_sources" / "gf0012_pdf"


def main() -> int:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        names = zf.namelist()
        pdf_name = next((n for n in names if n.lower().endswith(".pdf")), None)
        if pdf_name is None:
            print("no pdf found in zip")
            return 1
        pdf_bytes = zf.read(pdf_name)
        target = PDF_DIR / pdf_name
        target.write_bytes(pdf_bytes)

    doc = fitz.open(target)
    report = {
        "pdf_name": pdf_name,
        "pages": doc.page_count,
        "metadata": doc.metadata,
    }

    def page_summary(idx: int) -> dict:
        page = doc.load_page(idx)
        text = page.get_text("text")
        imgs = page.get_images(full=True)
        return {
            "page": idx + 1,
            "text_chars": len(text.strip()),
            "text_head": text.strip()[:400],
            "image_count": len(imgs),
        }

    probe_pages = [0, 1, 2, 3, 4, 5, 10, 50, 100, 150, 200, doc.page_count - 1]
    probe_pages = sorted({p for p in probe_pages if 0 <= p < doc.page_count})
    report["page_probes"] = [page_summary(p) for p in probe_pages]

    total_text = 0
    pages_with_text = 0
    pages_with_images = 0
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text").strip()
        if text:
            pages_with_text += 1
            total_text += len(text)
        if page.get_images(full=True):
            pages_with_images += 1
    report["whole_document"] = {
        "pages_with_text": pages_with_text,
        "pages_with_images": pages_with_images,
        "total_extracted_chars": total_text,
    }

    out = ROOT / "authoritative_sources" / "gf0012_pdf_probe.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
