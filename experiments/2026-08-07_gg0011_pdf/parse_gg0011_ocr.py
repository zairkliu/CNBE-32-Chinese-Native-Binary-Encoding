#!/usr/bin/env python3
"""Parse PaddleOCR-VL output for GG 0011-2009 radical table.

Reads pages 6/7/100 markdown, extracts main radicals and attached forms, then
cross-checks against the existing GF0011 public table in data/.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

MAIN_RE = re.compile(r"^(\d{1,3})\s*([^\s(（]+)\s*(?:[（(]([^）)]*)[）)])?\s*$")
ATTACHED_RE = re.compile(r"^\[(\d{1,3})\]\s*[（(]\s*([^）)]+?)\s*[）)]$")
SECTIONS = {"一画", "二画", "三画", "四画", "五画", "六画", "七画", "八画", "九画", "十画", "十一画", "十二画", "十三画", "十四画", "十五画", "十六画", "十七画"}


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def html_cells(text: str) -> list[str]:
    table = text[text.find("<table"):]
    table = table[: table.find("</table>") + 8]
    return [strip_html(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", table, re.S)]


def parse_text_cells(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def classify(cell: str) -> tuple[str, dict | None]:
    m = MAIN_RE.match(cell)
    if m:
        return "main", {
            "id": int(m.group(1)),
            "main": m.group(2),
            "attached_raw": m.group(3) or "",
        }
    a = ATTACHED_RE.match(cell)
    if a:
        return "attached", {"id": int(a.group(1)), "form": a.group(2)}
    if cell in SECTIONS or cell.endswith("画"):
        return "section", None
    return "other", None


def main() -> int:
    pages_dir = EXP / "ocr_cloud" / "pages"
    cells = []
    for name in ("page_006.md", "page_100.md"):
        text = (pages_dir / name).read_text(encoding="utf-8")
        cells.extend(html_cells(text))
    cells.extend(parse_text_cells((pages_dir / "page_007.md").read_text(encoding="utf-8")))

    mains: dict[int, dict] = {}
    attached: dict[int, list[str]] = {}
    raw_entries = []
    for cell in cells:
        kind, data = classify(cell)
        if kind == "main":
            mains.setdefault(
                data["id"],
                {"id": data["id"], "main": data["main"], "attached_raw": data["attached_raw"]},
            )
            raw_entries.append({"kind": "main", **data})
        elif kind == "attached":
            attached.setdefault(data["id"], []).append(data["form"])
            raw_entries.append({"kind": "attached", **data})

    gf = json.loads((REPO / "data" / "gf0011_201_radicals.json").read_text(encoding="utf-8"))["radicals"]
    gf_by_id = {r["code"]: r for r in gf}

    relation = []
    for r in gf:
        code = r["code"]
        ocr_main = mains.get(code)
        ocr_attached = attached.get(code, [])
        gf_attached = r.get("attached", "") or ""
        status = "MATCH"
        if ocr_main is None:
            status = "OCR_MISSING_MAIN"
        elif ocr_main["main"] != r["main"]:
            status = "OCR_MAIN_MISMATCH"
        if ocr_attached and gf_attached and "".join(ocr_attached) != gf_attached:
            status = "OCR_ATTACHED_MISMATCH" if status == "MATCH" else status + "_AND_ATTACHED"
        relation.append(
            {
                "id": code,
                "main": r["main"],
                "attached_forms": list(gf_attached),
                "ocr_main": ocr_main["main"] if ocr_main else None,
                "ocr_attached_forms": ocr_attached,
                "status": status,
            }
        )

    summary = {
        "gf_main_total": len(gf),
        "ocr_main_found": len(mains),
        "ocr_attached_found": sum(len(v) for v in attached.values()),
        "missing_main": [c for c in gf_by_id if c not in mains],
        "extra_main": [c for c in mains if c not in gf_by_id],
        "main_mismatch": sum(1 for r in relation if r["status"].startswith("OCR_MAIN_MISMATCH")),
        "attached_mismatch": sum(1 for r in relation if "ATTACHED_MISMATCH" in r["status"]),
        "full_match": sum(1 for r in relation if r["status"] == "MATCH"),
    }
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "gg0011_api_raw_entries.json").write_text(
        json.dumps({"source": "PaddleOCR-VL-1.6", "entries": raw_entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "gg0011_main_attached_relation.json").write_text(
        json.dumps({"schema_version": 1, "summary": summary, "radicals": relation}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
