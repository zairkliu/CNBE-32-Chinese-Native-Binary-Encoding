#!/usr/bin/env python3
"""Fetch additional official MOE standard PDFs and probe their text layers."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

import fitz


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"

SOURCES = {
    "gf0013_components_pdf": {
        "url": "http://www.moe.gov.cn/ewebeditor/uploadfile/2015/01/13/20150113090318445.pdf",
        "page_url": "http://www.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75696.html",
        "note": "现代常用字部件及部件名称规范",
    },
    "gf2001_stroke_shapes_pdf": {
        "url": "http://www.moe.gov.cn/ewebeditor/uploadfile/2015/01/12/20150112170016626.pdf",
        "page_url": "https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75688.html",
        "note": "GB 13000.1 字符集汉字折笔规范",
    },
    "gb18030_2022_notice": {
        "url": "https://openstd.samr.gov.cn/bzgk/std/nd?no=1783",
        "page_url": "https://openstd.samr.gov.cn/bzgk/std/nd?no=1783",
        "note": "国家标准全文公开系统：GB 18030-2022 题录入口",
    },
}


def download(url: str, timeout: int = 180) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001
        print(f"download error for {url}: {exc}")
        return None


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
    for key, info in SOURCES.items():
        print(f"== {key}: {info['url']}")
        raw = download(info["url"])
        entry = {
            "url": info["url"],
            "page_url": info["page_url"],
            "note": info["note"],
            "downloaded": raw is not None,
        }
        if raw:
            if key.endswith("_pdf"):
                local = OUT_DIR / f"{key}.pdf"
                entry["pdf_probe"] = probe_pdf(local, raw)
                entry["local_path"] = str(local)
            else:
                entry["size_bytes"] = len(raw)
                text = raw.decode("utf-8", "replace")
                entry["contains_18030"] = "18030" in text
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                entry["attachment_links"] = sorted(
                    {
                        href
                        for href in re.findall(
                            r'href=["\']([^"\']+\.(?:pdf|doc|docx|zip))["\']', text, re.I
                        )
                    }
                )
        report[key] = entry
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    (OUT_DIR / "official_pdfs_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
