#!/usr/bin/env python3
"""Build an evidence-graded remediation packet for CNBE coverage gaps.

For every unique truth char outside the CNBE standard track, join:
  - runtime DB track/fields
  - Unihan kRSUnicode + kTotalStrokes (cross-reference)
  - CHISE IDS structure operator (cross-reference)

The packet classifies each char as INSERT_CANDIDATE / INSERT_REVIEW /
UPGRADE_CANDIDATE / UPGRADE_REVIEW. No release DB write is performed.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

STRUCT_ORDER = [
    "\u72ec\u4f53\u5b57",  # 独体字
    "\u4e0a\u4e0b",        # 上下
    "\u4e0a\u4e2d\u4e0b",  # 上中下
    "\u5de6\u53f3",        # 左右
    "\u5de6\u4e2d\u53f3",  # 左中右
    "\u5de6\u4e0a\u5305",  # 左上包
    "\u53f3\u4e0a\u5305",  # 右上包
    "\u5de6\u4e09\u5305",  # 左三包
    "\u5de6\u4e0b\u5305",  # 左下包
    "\u4e0a\u4e09\u5305",  # 上三包
    "\u4e0b\u4e09\u5305",  # 下三包
    "\u5168\u5305\u56f4",  # 全包围
    "\u9576\u5d4c",        # 镶嵌
]
STRUCT_CODE = {name: i for i, name in enumerate(STRUCT_ORDER)}
IDS_STRUCT = {
    "\u2ff0": "\u5de6\u53f3",        # ⿰ 左右
    "\u2ff1": "\u4e0a\u4e0b",        # ⿱ 上下
    "\u2ff2": "\u5de6\u4e2d\u53f3",  # ⿲ 左中右
    "\u2ff3": "\u4e0a\u4e2d\u4e0b",  # ⿳ 上中下
    "\u2ff4": "\u5168\u5305\u56f4",  # ⿴ 全包围
    "\u2ff5": "\u4e0a\u4e09\u5305",  # ⿵ 上三包
    "\u2ff6": "\u4e0b\u4e09\u5305",  # ⿶ 下三包
    "\u2ff7": "\u5de6\u4e09\u5305",  # ⿷ 左三包
    "\u2ff8": "\u5de6\u4e0a\u5305",  # ⿸ 左上包
    "\u2ff9": "\u53f3\u4e0a\u5305",  # ⿹ 右上包
    "\u2ffa": "\u5de6\u4e0b\u5305",  # ⿺ 左下包
    "\u2ffb": "\u9576\u5d4c",        # ⿻ 镶嵌
}


def load_unihan_irg(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        result.setdefault(parts[0], {})[parts[1]] = parts[2].strip()
    return result


def load_ids(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        ucp, _, rest = line.partition("\t")
        if re.fullmatch(r"U\+[0-9A-Fa-f]{4,6}", ucp):
            result[ucp] = rest
    return result


def load_radix_name_map(path: Path) -> dict[int, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[int, str] = {}
    for rec in data.get("records", []):
        code = rec.get("code")
        if code is not None and rec.get("status") in ("DIRECT", "ALIAS"):
            result.setdefault(code, rec.get("canonical_radical") or rec["radical"])
    return result


def infer_structure(ids_text: str | None) -> str | None:
    if not ids_text:
        return None
    for op, name in IDS_STRUCT.items():
        if op in ids_text:
            return name
    return "\u72ec\u4f53\u5b57" if len(ids_text.strip()) <= 2 else None


def main() -> None:
    gaps = [
        g
        for g in json.loads((EXP / "coverage_gap.json").read_text(encoding="utf-8"))
        if not g["in_standard"]
    ]
    build = EXP.parent / "2026-08-05_scheme_comparison" / "build"
    unihan = load_unihan_irg(build / "Unihan_IRGSources.txt")
    ids_map = load_ids(build / "ids.txt")
    radix_name = load_radix_name_map(REPO / "evidence" / "8105" / "cnbe8105_radical_code_map.json")

    con = sqlite3.connect(str(REPO / "data" / "cnbe32.db"))
    con.row_factory = sqlite3.Row
    db = {r["char"]: dict(r) for r in con.execute("SELECT * FROM cnbe32")}
    con.close()

    entries = []
    actions: Counter[str] = Counter()
    for g in gaps:
        c = g["char"]
        ucp = f"U+{ord(c):04X}"
        unihan_row = unihan.get(ucp, {})
        krs = unihan_row.get("kRSUnicode")
        kst = unihan_row.get("kTotalStrokes")
        krs_code = int(re.match(r"\d+", krs).group(0)) if krs and re.match(r"\d+", krs) else None
        strokes = int(kst) if kst and kst.isdigit() else None
        ids_text = ids_map.get(ucp)
        structure = infer_structure(ids_text)
        has_evidence = krs_code is not None and strokes is not None and structure is not None
        current = db.get(c)
        action = (
            "INSERT_CANDIDATE" if current is None and has_evidence
            else "INSERT_REVIEW" if current is None
            else "UPGRADE_CANDIDATE" if has_evidence
            else "UPGRADE_REVIEW"
        )
        actions[action] += 1
        proposed = None
        if has_evidence:
            proposed = {
                "radix": krs_code,
                "radix_name": radix_name.get(krs_code),
                "strokes": strokes,
                "struct_name": structure,
                "struct_type": STRUCT_CODE[structure],
                "index": (ord(c) - 0x4E00) % 2048,
                "ext": 0,
                "track": "provisional",
            }
        entries.append(
            {
                "char": c,
                "codepoint": ucp,
                "count": g["count"],
                "in_db": current is not None,
                "db_track": current["track"] if current else None,
                "current": current,
                "evidence": {
                    "kRSUnicode": krs,
                    "krs_radical_code": krs_code,
                    "kTotalStrokes": kst,
                    "ids": ids_text,
                    "inferred_structure": structure,
                },
                "evidence_grade": "cross_reference_unihan_ids" if has_evidence else "review_required",
                "action": action,
                "proposed": proposed,
            }
        )

    entries.sort(key=lambda e: (-e["count"], e["char"]))
    packet = {
        "schema_version": 1,
        "summary": {
            "total": len(entries),
            "actions": dict(actions),
            "insert_candidates": sum(1 for e in entries if e["action"] == "INSERT_CANDIDATE"),
            "upgrade_candidates": sum(1 for e in entries if e["action"] == "UPGRADE_CANDIDATE"),
            "write_gate": "NO_WRITE_TO_RELEASE_DB",
        },
        "entries": entries,
    }
    (EXP / "coverage_remediation_packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    missing_candidates = [
        {"char": e["char"], "codepoint": e["codepoint"], "proposed": e["proposed"]}
        for e in entries
        if e["action"] == "INSERT_CANDIDATE"
    ]
    (EXP / "missing_six_candidates.json").write_text(
        json.dumps(missing_candidates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(packet["summary"], ensure_ascii=False, indent=2))
    for e in entries[:8]:
        print(e["char"], e["action"], e["evidence"]["inferred_structure"], e["proposed"])


if __name__ == "__main__":
    main()
