#!/usr/bin/env python3
"""Parse GF 0011-2009 full docx table and diff against the current JSON."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from docx import Document


EXP = Path(__file__).resolve().parent
REPO = EXP.parents[1]

SECTION_RE = re.compile(r"^([一二三四五六七八九十]+)画$")
MAIN_RE = re.compile(
    r"^(\d{1,3})\s*([^\s（(［]+?)\s*(?:[（(]([^）)]*)[）)])?$"
)
ATTACHED_RE = re.compile(r"^[［\[]\s*(\d{1,3})\s*[］\]]\s*[（(]([^）)]*)[）)]$")


def normalize(line: str) -> str:
    return line.replace("\u3000", " ").replace("\xa0", " ").strip()


def extract_lines(doc: Document) -> list[str]:
    lines: list[str] = []
    for ti in range(3):
        for row in doc.tables[ti].rows:
            for cell in row.cells:
                for raw in cell.text.split("\n"):
                    line = normalize(raw)
                    if line:
                        lines.append(line)
    return lines


def parse(lines: list[str]) -> dict:
    sections: dict[str, list[dict]] = {}
    current_section = ""
    mains: dict[int, dict] = {}
    attached_entries: dict[int, list[str]] = {}
    order: list[dict] = []

    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            current_section = m.group(1)
            sections.setdefault(current_section, [])
            continue
        a = ATTACHED_RE.match(line)
        if a:
            code = int(a.group(1))
            form = a.group(2)
            attached_entries.setdefault(code, []).append(form)
            sections.setdefault(current_section, []).append(
                {"kind": "attached", "code": code, "form": form}
            )
            order.append({"kind": "attached", "code": code, "form": form})
            continue
        m = MAIN_RE.match(line)
        if m:
            code = int(m.group(1))
            main = m.group(2)
            attached = m.group(3) or ""
            if code in mains:
                raise ValueError(f"duplicate main code {code}: {line}")
            item = {
                "kind": "main",
                "code": code,
                "main": main,
                "attached": attached,
                "stroke_group": current_section,
                "raw": line,
            }
            mains[code] = item
            sections.setdefault(current_section, []).append(item)
            order.append(item)
            continue
        raise ValueError(f"unparsed line: {line!r}")

    missing = [c for c in range(1, 202) if c not in mains]
    extra = sorted(set(mains) - set(range(1, 202)))
    return {
        "schema_version": 1,
        "source": "GF 0011-2009 汉字部首表（完整版 docx 文字层）",
        "summary": {
            "main_count": len(mains),
            "attached_entry_count": sum(len(v) for v in attached_entries.values()),
            "missing_codes": missing,
            "extra_codes": extra,
        },
        "radicals": [mains[c] for c in range(1, 202) if c in mains],
        "attached_entries": {
            str(c): forms for c, forms in sorted(attached_entries.items())
        },
        "order": order,
    }


def load_current() -> list[dict]:
    path = REPO / "data" / "gf0011_201_radicals.json"
    return json.loads(path.read_text(encoding="utf-8"))["radicals"]


def diff(parsed: dict, current: list[dict]) -> dict:
    parsed_by_code = {r["code"]: r for r in parsed["radicals"]}
    current_by_code = {r["code"]: r for r in current}
    rows = []
    for code in range(1, 202):
        p = parsed_by_code.get(code)
        c = current_by_code.get(code)
        if p is None or c is None:
            rows.append(
                {
                    "code": code,
                    "status": "MISSING",
                    "docx": p,
                    "current": c,
                }
            )
            continue
        diffs = []
        if p["main"] != c["main"]:
            diffs.append(
                {"field": "main", "docx": p["main"], "current": c["main"]}
            )
        if p["attached"] != c["attached"]:
            diffs.append(
                {
                    "field": "attached",
                    "docx": p["attached"],
                    "current": c["attached"],
                }
            )
        rows.append(
            {
                "code": code,
                "docx_main": p["main"],
                "docx_attached": p["attached"],
                "current_main": c["main"],
                "current_attached": c["attached"],
                "status": "MATCH" if not diffs else "DIFF",
                "diffs": diffs,
            }
        )
    summary = {
        "total": len(rows),
        "match": sum(1 for r in rows if r["status"] == "MATCH"),
        "diff": sum(1 for r in rows if r["status"] == "DIFF"),
        "missing": sum(1 for r in rows if r["status"] == "MISSING"),
    }
    return {"summary": summary, "rows": rows}


def main() -> int:
    source = os.environ.get(
        "GF0011_DOCX",
        os.path.join(os.environ["TEMP"], "gf0011_full.docx"),
    )
    doc = Document(source)
    lines = extract_lines(doc)
    parsed = parse(lines)

    current = load_current()
    comparison = diff(parsed, current)

    out_dir = EXP / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gf0011_docx_parsed.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "gf0011_docx_vs_current.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(parsed["summary"], ensure_ascii=False, indent=2))
    print(json.dumps(comparison["summary"], ensure_ascii=False, indent=2))
    print("saved parsed and diff JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())
