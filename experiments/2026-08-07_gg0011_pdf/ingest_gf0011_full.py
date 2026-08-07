#!/usr/bin/env python3
"""Build the canonical GF0011-2009 full table and write it into data/."""

from __future__ import annotations

import json
import sys
from pathlib import Path


EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
RESULTS = EXP / "results"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    current = load(REPO / "data" / "gf0011_201_radicals.json")["radicals"]
    docx = load(RESULTS / "gf0011_docx_parsed.json")
    wiki = load(RESULTS / "gf0011_wiki_template_parsed.json")

    current_by_code = {r["code"]: r for r in current}
    docx_by_code = {r["code"]: r for r in docx["radicals"]}
    wiki_by_code = {r["code"]: r for r in wiki["entries"]}
    docx_attached_entries = docx.get("attached_entries", {})

    corrections = {
        80: {
            "attached": "扌龵",
            "status": "CORRECTED",
            "note": "docx 文字层与维基模板均为 扌龵；原公开转载表 扌看 为 OCR 同形误读",
        },
        123: {
            "attached": "耂",
            "status": "CORRECTED",
            "note": "docx 文字层与维基模板均有 耂；原公开转载表漏列",
        },
        170: {
            "attached": "⻗",
            "status": "CORRECTED",
            "note": "维基模板与通用部首知识均为 雨（⻗）；原公开转载表漏列",
        },
        50: {
            "status": "NEEDS_REVIEW",
            "note": "docx 文字层为 彑彐，维基模板为 ⺕彑，原公开转载表为 彐彑；字形/顺序待官方页图像最终确认",
        },
        61: {
            "status": "NEEDS_REVIEW",
            "note": "维基模板附形含 𤣩玉，docx 文字层与 ichara 均为 玉；𤣩 是否入表待官方页图像确认",
        },
    }

    rows = []
    for code in range(1, 202):
        base = current_by_code[code]
        d = docx_by_code[code]
        w = wiki_by_code[code]
        correction = corrections.get(code, {})
        attached = correction.get("attached", base["attached"])
        status = correction.get("status", "CONSISTENT")
        note = correction.get("note", "")

        docx_forms = docx_attached_entries.get(str(code), [])
        row = {
            "code": code,
            "main": base["main"],
            "attached": attached,
            "stroke_group": w["stroke_group"],
            "attached_entries": [
                {"form": form, "source": "docx_text_layer", "draft": True}
                for form in docx_forms
            ],
            "source_status": status,
            "note": note,
            "docx_main": d["main"],
            "docx_attached": d["attached"],
            "wiki_attached": w["wiki_attached"],
        }
        if code == 5:
            row["unlisted_attached_forms_raw"] = (
                "乛、㇇、㇈、㇄、丨、㇀、㇒、丿、㇓、㇆、㇆、㇁"
            )
            row["unlisted_attached_count"] = 15
            row["note"] = (
                "标准 5.5：乛 部 15 个附形部首因数量较多未在部首表中列出"
            )
        rows.append(row)

    out = {
        "schema_version": 2,
        "standard": "GF 0011-2009 汉字部首表",
        "title": "汉字部首表（完整版入库）",
        "ingested_at": "2026-08-07",
        "status": "INGESTED",
        "source_chain": [
            {
                "id": "official_docx",
                "description": "用户提供完整版 docx，含官方 PDF 9 页图像与文字层",
                "path": "C:/Users/zairk/WorkBuddy/2026-08-07-20-23-37/GF_0011-2009_汉字部首表.docx",
            },
            {
                "id": "public_transcription",
                "url": "https://www.ichara.cn/web/account/view_article.php?art_id=110",
            },
            {
                "id": "wikipedia_template",
                "url": "https://zh.wikipedia.org/wiki/汉字部首表",
                "note": "Template:简体中文部首，201 主部首 + 100 附形部首",
            },
        ],
        "summary": {
            "main_count": len(rows),
            "attached_entry_count": sum(len(r["attached_entries"]) for r in rows),
            "listed_attached_form_count": 84,
            "unlisted_attached_form_count": 15,
            "total_attached_form_count_2009_late_document": 99,
            "stroke_group_sizes": {
                group: sum(1 for r in rows if r["stroke_group"] == group)
                for group in [r["stroke_group"] for r in rows]
            },
            "corrected": sum(1 for r in rows if r["source_status"] == "CORRECTED"),
            "needs_review": sum(1 for r in rows if r["source_status"] == "NEEDS_REVIEW"),
        },
        "radicals": rows,
    }
    target = REPO / "data" / "gf0011_201_radicals_full.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False, indent=2))
    print("saved:", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
