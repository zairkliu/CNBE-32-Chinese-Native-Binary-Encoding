#!/usr/bin/env python3
"""Reproduce every empirical number cited in docs/FIELD_SEMANTICS_FREEZE_v1.1.md.

PDR reference: WS-3 (field-semantics freeze), inputs from WS-2 queue and Issue #39.

This script is READ-ONLY against data/cnbe32.db. Third-party reference files
(cjkvi-ids, Unihan, 8105 scope) are optional: without them the script still
prints all database-internal evidence; with them it also prints agreement rates.

Usage:
    python scripts/freeze_evidence.py --db data/cnbe32.db \
        [--ids third_party/cjkvi_ids.txt] \
        [--unihan-irgsources third_party/Unihan_IRGSources.txt] \
        [--scope-file third_party/scope_8105.txt]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

# 13 canonical structure labels (governance-approved, mapped to GF 0017-2013 §3.12)
CN_LABELS = {
    "独体字", "上下", "上中下", "左右", "左中右", "左上包", "右上包",
    "左三包", "左下包", "上三包", "下三包", "全包围", "镶嵌",
}
# English legacy-track labels observed in the runtime db
EN_LABELS = {
    "single": "独体字", "up-down": "上下", "up-mid-down": "上中下",
    "left-right": "左右", "left-mid-right": "左中右",
    "top-left-wrap": "左上包", "top-right-wrap": "右上包",
    "left-wrap": "左三包", "bottom-left-wrap": "左下包",
    "top-wrap": "上三包", "bottom-wrap": "下三包", "full-wrap": "全包围",
    "embedded": "镶嵌",
}
IDC_TO_STRUCT = {
    "⿰": "左右", "⿱": "上下", "⿲": "左中右", "⿳": "上中下",
    "⿴": "全包围", "⿵": "上三包", "⿶": "下三包", "⿷": "左三包",
    "⿸": "左上包", "⿹": "右上包", "⿺": "左下包", "⿻": "镶嵌",
}


def load_ids(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        p = line.split("\t")
        if len(p) >= 3 and p[1] and len(p[1]) == 1 and p[2]:
            out[p[1]] = IDC_TO_STRUCT.get(p[2][0], "独体字")
    return out


def load_unihan(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        p = (line.rstrip("\n").split("\t") + ["", ""])[:3]
        if not p[0].startswith("U+"):
            continue
        ch = chr(int(p[0][2:], 16))
        e = out.setdefault(ch, {})
        if p[1] == "kRSUnicode":
            try:
                e["kangxi_radical"] = int(p[2].split()[0].split("'")[0].split(".")[0])
            except ValueError:
                pass
        elif p[1] == "kTotalStrokes":
            try:
                e["total_strokes"] = int(p[2].split()[0])
            except ValueError:
                pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--ids", type=Path)
    ap.add_argument("--unihan-irgsources", type=Path)
    ap.add_argument("--scope-file", type=Path)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    conn = sqlite3.connect(str(args.db))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM cnbe32")]
    conn.close()

    ev: dict = {}

    # E1. struct_name vocabulary
    vocab = Counter(r["struct_name"] for r in rows)
    ev["E1_struct_name_vocab"] = dict(vocab.most_common())
    ev["E1_summary"] = {
        "distinct": len(vocab),
        "canonical_cn_rows": sum(v for k, v in vocab.items() if k in CN_LABELS),
        "english_rows": sum(v for k, v in vocab.items() if k in EN_LABELS),
        "triangle_rows": vocab.get("triangle", 0),
    }

    # E2. dual struct_type numbering proof
    cn_map, en_map = {}, {}
    for st in sorted({r["struct_type"] for r in rows}):
        cn_c = Counter(r["struct_name"] for r in rows
                       if r["struct_type"] == st and r["struct_name"] in CN_LABELS)
        en_c = Counter(r["struct_name"] for r in rows
                       if r["struct_type"] == st and r["struct_name"] in EN_LABELS)
        if cn_c:
            cn_map[st] = cn_c.most_common(1)[0]
        if en_c:
            en_map[st] = (en_c.most_common(1)[0][0],
                          EN_LABELS[en_c.most_common(1)[0][0]],
                          en_c.most_common(1)[0][1])
    ev["E2_struct_type_cn_numbering"] = cn_map
    ev["E2_struct_type_en_numbering"] = en_map

    # E3. triangle rows all carry struct_type=12 (Chinese numbering => 镶嵌 claim)
    tri = Counter(r["struct_type"] for r in rows if r["struct_name"] == "triangle")
    ev["E3_triangle_struct_type"] = dict(tri)

    # E4. idx addressing formula: idx == (unicode - 0x4E00) % 2048
    formula_ok = formula_bad = 0
    for r in rows:
        if r["idx"] == (r["unicode"] - 0x4E00) % 2048:
            formula_ok += 1
        else:
            formula_bad += 1
    per_idx = Counter(r["idx"] for r in rows)
    ev["E4_idx_formula"] = {
        "matches_(unicode-0x4E00)%2048": formula_ok,
        "violations": formula_bad,
        "idx_range": [min(per_idx), max(per_idx)],
        "avg_rows_per_idx": round(len(rows) / len(per_idx), 2),
        "max_rows_per_idx": max(per_idx.values()),
    }

    # E5. strokes=31 cluster
    s31 = [r for r in rows if r["strokes"] == 31]
    ev["E5_strokes31_count"] = len(s31)

    # Optional third-party evidence
    if args.scope_file:
        scope = {l.strip() for l in args.scope_file.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")}
        in_scope = [r for r in rows if r["char"] in scope]
        track = Counter(
            "chinese" if r["struct_name"] in CN_LABELS
            else "triangle" if r["struct_name"] == "triangle" else "english"
            for r in in_scope)
        ev["E6_scope_track_breakdown"] = {"scope_rows": len(in_scope), **dict(track)}
    else:
        scope = None

    if args.ids and scope:
        ids = load_ids(args.ids)
        res = {"chinese": Counter(), "english": Counter()}
        for r in rows:
            if scope and r["char"] not in scope:
                continue
            tr = "chinese" if r["struct_name"] in CN_LABELS else (
                "english" if r["struct_name"] in EN_LABELS else None)
            if tr is None or r["char"] not in ids:
                continue
            mine = r["struct_name"] if tr == "chinese" else EN_LABELS[r["struct_name"]]
            ref = ids[r["char"]]
            if mine == ref:
                res[tr]["agree"] += 1
            elif mine == "独体字" or ref == "独体字":
                res[tr]["convention_difference"] += 1
            else:
                res[tr]["disagree"] += 1
        ev["E7_structure_vs_ids_by_track"] = {k: dict(v) for k, v in res.items()}

    if args.unihan_irgsources and scope:
        uh = load_unihan(args.unihan_irgsources)
        rad = {"chinese": [0, 0], "legacy": [0, 0]}  # [agree, total]
        stk = {"in_scope": [0, 0], "legacy": [0, 0]}
        s31_verdict = {"true_over_31": 0, "wrong": 0, "no_unihan": 0}
        for r in rows:
            ch = r["char"]
            e = uh.get(ch, {})
            in_s = scope and ch in scope
            if "kangxi_radical" in e and in_s:
                tr = "chinese" if r["struct_name"] in CN_LABELS else "legacy"
                rad[tr][1] += 1
                rad[tr][0] += int(e["kangxi_radical"] == r["radix"])
            if "total_strokes" in e:
                k = "in_scope" if in_s else "legacy"
                stk[k][1] += 1
                stk[k][0] += int(e["total_strokes"] == r["strokes"])
                if r["strokes"] == 31:
                    if e["total_strokes"] > 31:
                        s31_verdict["true_over_31"] += 1
                    else:
                        s31_verdict["wrong"] += 1
        ev["E8_radical_vs_kRSUnicode_in_scope"] = rad
        ev["E9_strokes_vs_unihan"] = stk
        ev["E10_strokes31_verdict"] = s31_verdict

    print(json.dumps(ev, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
