#!/usr/bin/env python3
"""Fetch authoritative radical standards attachments and report provenance."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"

SOURCES = {
    "gf0012_zip": {
        "url": "http://video.moe.gov.cn/yuxinsi/15hanzibushou.zip",
        "page_url": "https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/200901/t20090102_186104.html",
        "note": "教育部官方附件：GB13000.1字符集汉字部首归部规范.pdf",
    },
    "gf0011_2022_announcement": {
        "url": "http://www.gov.cn/xinwen/2022-11/24/content_5728500.htm",
        "page_url": "http://www.gov.cn/xinwen/2022-11/24/content_5728500.htm",
        "note": "中国政府网：教育部、国家语委发布《汉字部首表》2022修订公告",
    },
}


def download(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 CNBE-provenance-audit/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def probe_pdf(pdf_bytes: bytes) -> dict:
    head = pdf_bytes[:1024]
    has_text_layer = b"/Font" in pdf_bytes or b"/Contents" in pdf_bytes
    # Count page objects with a lightweight regex over the raw stream.
    import re

    page_count = len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))
    return {
        "magic": head[:8].decode("latin1", "replace"),
        "pdf_size_bytes": len(pdf_bytes),
        "page_object_count_estimate": page_count,
        "has_font_or_contents_objects": has_text_layer,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for key, info in SOURCES.items():
        print(f"== {key}: {info['url']}")
        raw = download(info["url"])
        digest = sha256(raw)
        target = OUT_DIR / f"{key}.bin"
        target.write_bytes(raw)
        entry = {
            "key": key,
            "url": info["url"],
            "page_url": info["page_url"],
            "note": info["note"],
            "sha256": digest,
            "size_bytes": len(raw),
            "local_path": str(target),
        }
        if key == "gf0012_zip":
            try:
                zf = zipfile.ZipFile(io.BytesIO(raw))
                entry["zip_entries"] = [
                    {
                        "name": n,
                        "size": zf.getinfo(n).file_size,
                        "crc32": f"{zf.getinfo(n).CRC & 0xFFFFFFFF:08x}",
                    }
                    for n in zf.namelist()
                ]
                for member in zf.namelist():
                    if member.lower().endswith(".pdf"):
                        entry["pdf_probe"] = probe_pdf(zf.read(member))
                        break
            except zipfile.BadZipFile as exc:
                entry["zip_error"] = str(exc)
        elif key == "gf0011_2022_announcement":
            entry["text_size_chars"] = len(raw.decode("utf-8", "replace"))
            entry["contains_hanzi_bushou"] = "汉字部首表" in raw.decode("utf-8", "replace")
        manifest.append(entry)
        print(json.dumps(entry, ensure_ascii=False, indent=2))

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
