#!/usr/bin/env python3
"""Fetch metadata for shortlisted GitHub supplement candidates."""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "authoritative_sources"

REPOS = [
    "cjkvi/cjkvi-ids",
    "Transfusion/cjkvi-ids-unicode",
    "shengdoushi/common-standard-chinese-characters-table",
    "max32002/chinese_dictionary",
    "howl-anderson/hanzi_chaizi",
    "hanziku/hanziyin",
    "skishore/makemeahanzi",
    "yawnoc/unihan-radical-strokes-readable",
    "cihai/unihan-etl",
    "JuliaCJK/IDSGraphs.jl",
    "leechenhwa2/nlp-han-dicts",
    "kanripo/KR1j0048",
    "he426100/kangxi",
    "mreichhoff/kanji-linear-algebra",
    "Radically/radically",
    "cnchar/cnchar",
]


def fetch(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CNBE-32-source-audit/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, dict] = {}
    for repo in REPOS:
        print("==", repo)
        try:
            data = fetch(f"https://api.github.com/repos/{repo}")
            report[repo] = {
                "full_name": data.get("full_name"),
                "html_url": data.get("html_url"),
                "description": data.get("description"),
                "language": data.get("language"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "updated_at": data.get("updated_at"),
                "archived": data.get("archived"),
                "license": (data.get("license") or {}).get("spdx_id"),
                "default_branch": data.get("default_branch"),
                "size_kb": data.get("size"),
            }
        except Exception as exc:  # noqa: BLE001
            report[repo] = {"error": str(exc)}
        time.sleep(0.4)
    target = OUT_DIR / "github_candidate_metadata.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
