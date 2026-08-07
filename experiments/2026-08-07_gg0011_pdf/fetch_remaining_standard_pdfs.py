#!/usr/bin/env python3
"""Fetch remaining MOE standard PDFs and probe their text layers."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

import fitz


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"

PAGES = {
    "gf0014_single_component": {
        "url": "https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75697.html",
        "note": "现代常用独体字规范",
    },
    "gf3002_stroke_order": {
        "url": "http://www.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75619.html",
        "note": "GF3002-1999 GB13000.1字符集汉字笔顺规范",
    },
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def probe_pdf(path: Path, pdf_bytes: bytes) -> dict:
    path.write_bytes(pdf_bytes)
    doc = fitz.open(path)
    pages_with_text = 0
    total_chars = 0
    pages_with_images = 0
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text").strip()
        if text:
            pages_with_text += 1
            total_chars += len(text)
        if page.get_images(full=True):
            pages_with_images += 1
    return {
        "pdf_size_bytes": len(pdf_bytes),
        "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "pages": doc.page_count,
        "pages_with_text": pages_with_text,
        "pages_with_images": pages_with_images,
        "total_extracted_chars": total_chars,
        "title": (doc.metadata or {}).get("title", ""),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, dict] = {}
    for key, info in PAGES.items():
        print(f"== {key}: {info['url']}")
        entry: dict = {"page_url": info["url"], "note": info["note"]}
        try:
            html = fetch(info["url"]).decode("utf-8", "replace")
            entry["page_size_bytes"] = len(html)
            links = sorted(
                {
                    href
                    for href in re.findall(
                        r'href=["\']([^"\']+\.(?:pdf|doc|docx))["\']', html, re.I
                    )
                }
            )
            entry["attachment_links"] = links
            if links:
                first = links[0]
                pdf_url = first if first.startswith("http") else "http://www.moe.gov.cn" + first
                raw = fetch(pdf_url)
                local = OUT_DIR / f"{key}_pdf.pdf"
                entry["pdf_probe"] = probe_pdf(local, raw)
                entry["pdf_url"] = pdf_url
                entry["local_path"] = str(local)
        except Exception as exc:  # noqa: BLE001
            entry["error"] = str(exc)
        report[key] = entry
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    (OUT_DIR / "remaining_standard_pdfs_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
