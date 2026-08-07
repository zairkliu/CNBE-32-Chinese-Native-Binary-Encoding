#!/usr/bin/env python3
"""Fetch MOE standard pages and extract attachment links."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"

PAGES = {
    "gf0013_components": "http://www.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75696.html",
    "gf2001_strokes": "https://hudong.moe.gov.cn/jyb_sjzl/ziliao/A19/201001/t20100115_75688.html",
    "gf0011_2022_release": "https://hudong.moe.gov.cn/jyb_xwfb/gzdt_gzdt/s5987/202211/t20221118_995332.html",
    "gf0011_2022_release_alt": "http://www.moe.gov.cn/jyb_xwfb/gzdt_gzdt/s5987/202211/t20221118_995332.html",
}


def fetch(url: str) -> tuple[bytes | None, int]:
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read(), resp.status
    except Exception as exc:  # noqa: BLE001
        return None, 0


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, dict] = {}
    for key, url in PAGES.items():
        raw, status = fetch(url)
        safe_key = key
        entry: dict = {"url": url, "http_status": status}
        if raw:
            text = raw.decode("utf-8", "replace")
            entry["size_bytes"] = len(raw)
            entry["attachment_links"] = sorted(
                {
                    href
                    for href in re.findall(r'href=["\']([^"\']+\.(?:pdf|doc|docx|zip|rar|wps))["\']', text, re.I)
                }
            )
            entry["title"] = (
                re.search(r"<title>(.*?)</title>", text, re.S | re.I).group(1).strip()
                if re.search(r"<title>(.*?)</title>", text, re.S | re.I)
                else ""
            )
            (OUT_DIR / f"{safe_key}.html").write_text(text, encoding="utf-8")
        report[key] = entry
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    (OUT_DIR / "moe_pages_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
