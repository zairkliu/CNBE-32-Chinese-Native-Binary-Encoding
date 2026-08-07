#!/usr/bin/env python3
"""Parse the GF0011 navbox from the rendered Chinese Wikipedia page."""

from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path


EXP = Path(__file__).resolve().parent


def main() -> int:
    source = os.environ.get(
        "ZHWIKI_GF0011_HTML",
        os.path.join(os.environ["TEMP"], "zhwiki_bushou.html"),
    )
    raw = Path(source).read_text(encoding="utf-8", errors="replace")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S)
    groups: list[dict] = []
    code = 1
    entries: list[dict] = []
    for row in rows:
        m = re.search(
            r'<th[^>]*class="[^"]*navbox-group[^"]*"[^>]*>(.*?)</th>', row, re.S
        )
        if not m:
            continue
        group = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        items = []
        for li in re.findall(r"<li[^>]*>(.*?)</li>", row, re.S):
            text = html.unescape(re.sub(r"<[^>]+>", "", li))
            text = re.sub(r"\s+", "", text)
            main_m = re.match(r"^(.*?)(?:（([^）]*)）)?$", text)
            main = main_m.group(1) if main_m else text
            attached = main_m.group(2) if main_m and main_m.group(2) else ""
            item = {
                "code": code,
                "main": main,
                "wiki_attached": attached,
                "stroke_group": group,
                "raw": text,
            }
            items.append(item)
            entries.append(item)
            code += 1
        groups.append({"stroke_group": group, "items": items})

    result = {
        "schema_version": 1,
        "source": "维基百科《汉字部首表》渲染页导航模板 Template:简体中文部首",
        "source_url": "https://zh.wikipedia.org/wiki/汉字部首表",
        "summary": {
            "group_count": len(groups),
            "entry_count": len(entries),
            "group_sizes": {g["stroke_group"]: len(g["items"]) for g in groups},
        },
        "groups": groups,
        "entries": entries,
    }
    out = EXP / "results" / "gf0011_wiki_template_parsed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
