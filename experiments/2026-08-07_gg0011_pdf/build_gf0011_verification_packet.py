#!/usr/bin/env python3
"""Build a human-review packet for all GF0011 main and attached radicals."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd


EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]
RESULTS = EXP / "results"


def load(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def split_forms(attached: str) -> list[str]:
    if not attached:
        return []
    if attached in ("阝右", "阝左"):
        return [attached]
    return list(attached)


def normalize_wiki(attached: str) -> str:
    if not attached:
        return ""
    return (
        attached.replace("⻏，在右", "阝右")
        .replace("⻏,在右", "阝右")
        .replace("⻖，在左", "阝左")
        .replace("⻖,在左", "阝左")
    )


VARIANT_MAP = {
    "⺁": "𠂆",
    "𠂆": "⺁",
    "⺇": "𠘨",
    "𠘨": "⺇",
    "⺋": "㔾",
    "㔾": "⺋",
    "⺕": "彑",
    "⺪": "𤴔",
    "𤴔": "⺪",
    "⺮": "𥫗",
    "𥫗": "⺮",
    "⺽": "𦥑",
    "𦥑": "⺽",
    "⺷": "𦍌",
    "𦍌": "⺷",
    "⻊": "𧾷",
    "𧾷": "⻊",
}

NOTES_MAP = {
    2: "维基模板把 亅 挂在 5 乛 后；docx 与 ichara 均为 2 丨（亅），采用 docx/ichara",
    75: "docx/ichara 为 ⺜曰，维基为 曰⺜，顺序待官方页图像确认",
    126: "docx/ichara 为 襾西，维基仅列 西；台湾《教育部重編國語辭典》襾部附形为 覀西，佐证 襾西",
}


def is_variant(a: str, b: str) -> bool:
    return a in VARIANT_MAP and VARIANT_MAP[a] == b


def compare(canonical: list[str], wiki: list[str]) -> str:
    if canonical == wiki:
        return "CONSISTENT"
    if len(canonical) == len(wiki) and all(
        x == y or is_variant(x, y) or is_variant(y, x)
        for x, y in zip(canonical, wiki)
    ):
        return "VARIANT"
    return "DIFF"


def main() -> int:
    full = load("data/gf0011_201_radicals_full.json")["radicals"]
    docx = load(
        "experiments/2026-08-07_gg0011_pdf/results/gf0011_docx_parsed.json"
    )
    docx_by_code = {r["code"]: r for r in docx["radicals"]}
    wiki = load(
        "experiments/2026-08-07_gg0011_pdf/results/gf0011_wiki_template_parsed.json"
    )["entries"]
    wiki_by_code = {r["code"]: r for r in wiki}
    baseline = load(
        "experiments/2026-08-07_gg0011_pdf/results/gf0011_docx_vs_current.json"
    )["rows"]
    baseline_by_code = {r["code"]: r for r in baseline}

    rows = []
    form_rows = []
    for r in full:
        code = r["code"]
        canonical_forms = split_forms(r["attached"])
        docx_attached = docx_by_code[code]["attached"]
        wiki_raw = wiki_by_code[code]["wiki_attached"]
        baseline_attached = baseline_by_code[code].get("current_attached", "")
        wiki_forms = split_forms(normalize_wiki(wiki_raw))
        status = r["source_status"]
        if status == "CONSISTENT":
            status = compare(canonical_forms, wiki_forms)
        note = r.get("note", "") or NOTES_MAP.get(code, "")
        rows.append(
            {
                "code": code,
                "main": r["main"],
                "attached": r["attached"],
                "forms": "/".join(canonical_forms),
                "form_count": len(canonical_forms),
                "stroke_group": r["stroke_group"],
                "docx_text_layer": docx_attached,
                "public_baseline": baseline_attached,
                "wiki_template": wiki_raw,
                "source_status": status,
                "note": note,
            }
        )
        for form in canonical_forms:
            form_rows.append(
                {
                    "code": code,
                    "main": r["main"],
                    "attached_form": form,
                    "in_docx": form in docx_attached or (
                        form in ("阝右", "阝左") and "阝" in docx_attached
                    ),
                    "in_public_baseline": form in baseline_attached or (
                        form in ("阝右", "阝左") and "阝" in baseline_attached
                    ),
                    "in_wiki": form in wiki_raw or any(
                        x == form or is_variant(x, form) or is_variant(form, x)
                        for x in wiki_forms
                    ),
                    "source_status": r["source_status"],
                    "note": note,
                }
            )

    summary = {
        "main_count": len(rows),
        "listed_attached_form_count": sum(r["form_count"] for r in rows),
        "status_counts": {},
        "needs_review_codes": [r["code"] for r in rows if r["source_status"] == "NEEDS_REVIEW"],
        "variant_codes": [r["code"] for r in rows if r["source_status"] == "VARIANT"],
        "diff_codes": [r["code"] for r in rows if r["source_status"] == "DIFF"],
        "unlisted_yi_attached_count": 15,
    }
    for r in rows:
        summary["status_counts"][r["source_status"]] = (
            summary["status_counts"].get(r["source_status"], 0) + 1
        )

    csv_path = RESULTS / "GF0011_201_MAIN_ATTACHED_VERIFICATION.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    xlsx_path = RESULTS / "GF0011_201_MAIN_ATTACHED_VERIFICATION.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="main_attached", index=False)
        pd.DataFrame(form_rows).to_excel(
            writer, sheet_name="attached_forms", index=False
        )
        pd.DataFrame(
            [
                {
                    "code": 5,
                    "main": "乛",
                    "unlisted_attached_count": 15,
                    "note": "标准 5.5：乛 部 15 个附形部首因数量较多未在部首表中列出",
                }
            ]
        ).to_excel(writer, sheet_name="unlisted_yi_5", index=False)

    report = RESULTS / "GF0011_201_MAIN_ATTACHED_VERIFICATION.md"
    lines = [
        "# GF0011-2009 主部首与附形部首全量核对",
        "",
        "- 主部首：201",
        f"- 表内列出的附形部首形式：{summary['listed_attached_form_count']}",
        "- 5 乛 部未列出附形：15",
        "- 口径：2009 后期正式文件附形部首 99（=84+15）；2022 修订调整为 100",
        "",
        "## 状态分布",
        "",
        "| 状态 | 数量 |",
        "|---|---:|",
    ]
    for k, v in sorted(summary["status_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## 待复核与差异项")
    lines.append("")
    for code in summary["needs_review_codes"] + summary["variant_codes"] + summary["diff_codes"]:
        r = next(x for x in rows if x["code"] == code)
        lines.append(
            f"- {r['code']} {r['main']}（{r['attached']}）：{r['source_status']}"
        )
        if r["note"]:
            lines.append(f"  - {r['note']}")
    lines.append("")
    lines.append("## 产物")
    lines.append("")
    lines.append(f"- CSV：`results/GF0011_201_MAIN_ATTACHED_VERIFICATION.csv`")
    lines.append(f"- XLSX：`results/GF0011_201_MAIN_ATTACHED_VERIFICATION.xlsx`")
    report.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("saved:", csv_path, xlsx_path, report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
