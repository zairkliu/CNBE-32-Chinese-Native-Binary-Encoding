#!/usr/bin/env python3
"""Search GitHub for open-source projects that can supplement radical/standard gaps."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"
QUERIES = [
    "GF0012",
    "汉字部首归部",
    "汉字部首表",
    "CJK IDS decomposition",
    "Unihan radical stroke",
    "kRSUnicode",
    "汉字部件规范",
    "通用规范汉字表",
    "cjkvi ids",
    "四角号码",
    "汉字结构 拆分",
    "CHISE",
]


def search(query: str) -> list[dict]:
    url = (
        "https://api.github.com/search/repositories?"
        + urllib.parse.urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": 20}
        )
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CNBE-32-source-audit/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return [
        {
            "full_name": item.get("full_name"),
            "html_url": item.get("html_url"),
            "description": (item.get("description") or "")[:160],
            "language": item.get("language"),
            "stars": item.get("stargazers_count"),
            "updated_at": item.get("updated_at"),
            "archived": item.get("archived"),
            "license": (item.get("license") or {}).get("spdx_id"),
        }
        for item in payload.get("items", [])
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, list[dict]] = {}
    for query in QUERIES:
        try:
            report[query] = search(query)
            print(f"== {query}: {len(report[query])} results")
        except Exception as exc:  # noqa: BLE001
            report[query] = []
            print(f"== {query}: ERROR {exc}")
        time.sleep(1.5)
    target = OUT_DIR / "github_supplement_projects.json"
    slim = {
        query: items
        for query, items in report.items()
        if items
    }
    target.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
