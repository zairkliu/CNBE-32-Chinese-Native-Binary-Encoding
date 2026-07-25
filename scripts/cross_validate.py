#!/usr/bin/env python3
"""Cross-validate CNBE-32 runtime annotations against open-source second opinions.

PDR reference: WS-2 (cross-validation layer), requirements WS2-R1 .. WS2-R4.

Sources (all third-party, all lower evidence tier than national standards):
- cjkvi-ids (CHISE IDS Database): character decomposition / structure
- Unihan (Unicode.org): kRSUnicode (Kangxi 214 radical), kTotalStrokes

Governance rules:
- This script NEVER writes to any source table. It only produces:
  1. a human-readable report (reports/8105_CROSS_VALIDATION.md)
  2. a machine-readable adjudication queue (data/review_queue.jsonl)
- Source tables may only be modified through the human-authorized governance
  workflow (docs/CNBE8105_ENCODING_GOVERNANCE.md, gate 12).

Important semantic notes:
- Unihan kRSUnicode uses the Kangxi 214-radical system; GF 0011-2009 uses 201
  principal radicals. Radical agreement here validates against the Kangxi/Unicode
  tradition, NOT against GF 0011. GF 0011 anchoring is a separate workstream (WS-3).
- cjkvi-ids is a cross-reference source, not a national standard. Disagreement
  does not imply CNBE is wrong; it implies the row needs expert adjudication.

Usage:
    python scripts/cross_validate.py \
        --db data/cnbe32.db \
        --ids third_party/cjkvi_ids.txt \
        --unihan-irgsources /path/to/Unihan_IRGSources.txt \
        [--scope-file path/to/8105_chars.txt] \
        [--out-report reports/8105_CROSS_VALIDATION.md] \
        [--out-queue data/review_queue.jsonl]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

SCRIPT_VERSION = "0.1.0"

# Project-approved 13 structure labels (docs/CNBE8105_ENCODING_GOVERNANCE.md),
# mapped 1:1 to GF 0017-2013 section 3.12.
CANONICAL_STRUCTS = (
    "独体字", "上下", "上中下", "左右", "左中右", "左上包", "右上包",
    "左三包", "左下包", "上三包", "下三包", "全包围", "镶嵌",
)

# Bilingual runtime labels observed in data/cnbe32.db -> canonical label.
STRUCT_NORMALIZE = {
    # English runtime labels
    "single": "独体字", "up_down": "上下", "up-down": "上下",
    "up-mid-down": "上中下", "left_right": "左右", "left-right": "左右",
    "left-mid-right": "左中右", "top-left-wrap": "左上包",
    "top-right-wrap": "右上包", "left-wrap": "左三包",
    "bottom-left-wrap": "左下包", "top-wrap": "上三包",
    "bottom-wrap": "下三包", "full-wrap": "全包围", "embedded": "镶嵌",
    # Chinese canonical labels (identity)
    **{c: c for c in CANONICAL_STRUCTS},
}

# IDS (Ideographic Description Characters) -> canonical structure.
IDC_TO_STRUCT = {
    "⿰": "左右", "⿱": "上下", "⿲": "左中右", "⿳": "上中下",
    "⿴": "全包围", "⿵": "上三包", "⿶": "下三包", "⿷": "左三包",
    "⿸": "左上包", "⿹": "右上包", "⿺": "左下包", "⿻": "镶嵌",
}

PRIORITY = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def load_cnbe(db_path: Path) -> dict[str, dict]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(cnbe32)")}
    rows = {}
    for r in conn.execute("SELECT * FROM cnbe32"):
        d = dict(r)
        char = d.get("char")
        if not isinstance(char, str) or len(char) != 1:
            continue
        rows[char] = {
            "unicode": d.get("unicode") or f"U+{ord(char):04X}",
            "radix": d.get("radix"),
            "radix_name": d.get("radix_name") if "radix_name" in cols else None,
            "strokes": d.get("strokes") if "strokes" in cols else d.get("stroke"),
            "struct_name": d.get("struct_name"),
        }
    conn.close()
    return rows


def load_ids(ids_path: Path) -> dict[str, str]:
    """char -> canonical structure derived from the leading IDS operator."""
    result = {}
    for line in ids_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) < 3 or not parts[1]:
            continue
        char, ids = parts[1], parts[2]
        if len(char) != 1:
            continue
        result[char] = IDC_TO_STRUCT.get(ids[0], "独体字") if ids else "独体字"
    return result


def load_unihan(path: Path) -> dict[str, dict]:
    """char -> {'kangxi_radical': int, 'total_strokes': int} from Unihan_IRGSources.txt."""
    result: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        cp, tag, value = (line.split("\t") + ["", ""])[:3]
        if not cp.startswith("U+"):
            continue
        char = chr(int(cp[2:], 16))
        entry = result.setdefault(char, {})
        if tag == "kRSUnicode":
            first = value.split()[0].split("'")[0]  # strip simplified-form marker
            try:
                entry["kangxi_radical"] = int(first.split(".")[0])
            except ValueError:
                pass
        elif tag == "kTotalStrokes":
            try:
                entry["total_strokes"] = int(value.split()[0])
            except ValueError:
                pass
    return result


def cross_validate(
    db_path: Path,
    ids_path: Path,
    unihan_path: Path,
    scope_file: Path | None = None,
) -> tuple[dict, list[dict]]:
    cnbe = load_cnbe(db_path)
    ids = load_ids(ids_path)
    unihan = load_unihan(unihan_path)

    scope: set[str] | None = None
    if scope_file is not None:
        scope = {
            ln.strip() for ln in scope_file.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        }

    stats = {
        "total_rows": 0,
        "structure": Counter(),
        "radical": Counter(),
        "strokes": Counter(),
        "unapproved_labels": Counter(),
        "capped_stroke_chars": [],
    }
    queue: list[dict] = []

    for char, row in sorted(cnbe.items(), key=lambda kv: ord(kv[0])):
        if scope is not None and char not in scope:
            continue
        stats["total_rows"] += 1
        issues: list[str] = []
        prio = 5  # lower = more severe; 5 means no issue

        # --- structure ---
        raw_label = row["struct_name"]
        cnbe_struct = STRUCT_NORMALIZE.get(raw_label)
        if cnbe_struct is None:
            stats["structure"]["unapproved_label"] += 1
            stats["unapproved_labels"][raw_label] += 1
            issues.append(f"label_not_approved:{raw_label}")
            prio = min(prio, PRIORITY["P1"])
        ids_struct = ids.get(char)
        if ids_struct is None:
            stats["structure"]["ids_missing"] += 1
        elif cnbe_struct is not None:
            if cnbe_struct == ids_struct:
                stats["structure"]["agree"] += 1
            elif cnbe_struct == "独体字" or ids_struct == "独体字":
                # Convention/coverage difference, not an error:
                # - CNBE says singleton but IDS decomposes (丁=⿱一亅):
                #   GF 0013 allows splitting singletons into strokes only;
                #   CHISE IDS decomposes anything decomposable.
                # - IDS says singleton: CHISE coverage gap for this char.
                stats["structure"]["convention_difference"] += 1
            else:
                stats["structure"]["disagree"] += 1
                issues.append(
                    f"structure_mismatch:cnbe={cnbe_struct},ids={ids_struct}"
                )
                prio = min(prio, PRIORITY["P3"])

        # --- radical (Kangxi 214 tradition; NOT GF 0011) ---
        uh = unihan.get(char, {})
        kangxi = uh.get("kangxi_radical")
        if kangxi is None:
            stats["radical"]["unihan_missing"] += 1
        elif row["radix"] is None:
            stats["radical"]["cnbe_missing"] += 1
        elif int(row["radix"]) == kangxi:
            stats["radical"]["agree"] += 1
        else:
            stats["radical"]["disagree"] += 1
            issues.append("radical_mismatch")
            prio = min(prio, PRIORITY["P2"])

        # --- strokes ---
        total = uh.get("total_strokes")
        if total is None:
            stats["strokes"]["unihan_missing"] += 1
        elif row["strokes"] is None:
            stats["strokes"]["cnbe_missing"] += 1
        elif int(row["strokes"]) == total:
            stats["strokes"]["agree"] += 1
        elif int(row["strokes"]) == 31 and total > 31:
            stats["strokes"]["capped"] += 1
            stats["capped_stroke_chars"].append(char)
            issues.append(f"stroke_capped:cnbe=31,unihan={total}")
            prio = min(prio, PRIORITY["P1"])
        else:
            stats["strokes"]["disagree"] += 1
            issues.append(f"stroke_mismatch:cnbe={row['strokes']},unihan={total}")
            prio = min(prio, PRIORITY["P2"])

        if issues:
            queue.append({
                "unicode": row["unicode"],
                "char": char,
                "issues": issues,
                "priority": f"P{prio}",
                "cnbe": {"radix": row["radix"], "strokes": row["strokes"],
                         "struct_name": raw_label, "struct_canonical": cnbe_struct},
                "cjkvi_ids": {"struct_canonical": ids_struct},
                "unihan": {"kangxi_radical": kangxi, "total_strokes": total},
                "evidence_note": "cjkvi-ids/Unihan are cross-reference sources, not "
                                 "national standards; adjudication requires expert review",
            })

    return stats, queue


def write_report(stats: dict, queue: list[dict], out: Path, inputs: dict) -> None:
    s = stats

    def rate(counter: Counter) -> str:
        agree, disagree = counter["agree"], counter["disagree"]
        total = agree + disagree
        return f"{agree}/{total} ({agree / total:.1%})" if total else "n/a"

    prio_dist = Counter(q["priority"] for q in queue)
    lines = [
        "# CNBE-32 三方交叉验证报告（WS-2）",
        "",
        f"- 生成脚本：`scripts/cross_validate.py` v{SCRIPT_VERSION}",
        f"- 输入：{inputs}",
        f"- 总行数：{s['total_rows']}",
        "",
        "> 证据等级声明：cjkvi-ids 与 Unihan 均为**交叉参考源**，非国家标准。",
        "> 分歧不等于 CNBE 错误，只意味着该行需要专家裁决。本报告不修改任何源表。",
        "> 部首比对基于**康熙 214 部首体系**（Unihan kRSUnicode），不是 GF 0011-2009",
        "> 的 201 部首；GF 0011 锚定属于 WS-3 工作流。",
        "",
        "## 字段一致率",
        "",
        "| 字段 | 一致率（一致/可比行） | 分歧 | 缺源 |",
        "|---|---|---|---|",
        f"| 结构（vs cjkvi-ids） | {rate(s['structure'])} | 实质分歧 {s['structure']['disagree']}，约定/覆盖差异 {s['structure']['convention_difference']} | ids 缺 {s['structure']['ids_missing']}，未批准标签 {s['structure']['unapproved_label']} |",
        f"| 部首（vs Unihan 康熙214） | {rate(s['radical'])} | {s['radical']['disagree']} | unihan 缺 {s['radical']['unihan_missing']}，cnbe 缺 {s['radical']['cnbe_missing']} |",
        f"| 笔画（vs Unihan） | {rate(s['strokes'])} | {s['strokes']['disagree']} | unihan 缺 {s['strokes']['unihan_missing']}，截断(=31真实>31) {s['strokes']['capped']} |",
        "",
        "## 未批准结构标签（治理红线，对应 Issue #39 发现 1）",
        "",
        "| 标签 | 行数 |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in s["unapproved_labels"].most_common()],
        "",
        "## 裁决队列",
        "",
        f"- 队列文件：`data/review_queue.jsonl`，共 **{len(queue)}** 行",
        f"- 优先级分布：{dict(sorted(prio_dist.items()))}",
        "- 优先级定义：P1=笔画截断/未批准标签（数据错误级），P2=部首或笔画实质分歧，P3=结构分歧",
        "",
        "## 笔画截断字符（P1，前 40 个）",
        "",
        "".join(s["capped_stroke_chars"][:40]) or "（无）",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", type=Path, default=Path("data/cnbe32.db"))
    p.add_argument("--ids", type=Path, default=Path("third_party/cjkvi_ids.txt"))
    p.add_argument("--unihan-irgsources", type=Path, required=True)
    p.add_argument("--scope-file", type=Path, default=None)
    p.add_argument("--out-report", type=Path, default=Path("reports/8105_CROSS_VALIDATION.md"))
    p.add_argument("--out-queue", type=Path, default=Path("data/review_queue.jsonl"))
    args = p.parse_args(argv)

    for f in (args.db, args.ids, args.unihan_irgsources):
        if not f.exists():
            raise SystemExit(f"input not found: {f}")

    stats, queue = cross_validate(args.db, args.ids, args.unihan_irgsources, args.scope_file)

    args.out_queue.parent.mkdir(parents=True, exist_ok=True)
    with args.out_queue.open("w", encoding="utf-8", newline="\n") as fh:
        for q in queue:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")

    write_report(stats, queue, args.out_report, {
        "db": str(args.db), "ids": str(args.ids),
        "unihan": str(args.unihan_irgsources), "scope": str(args.scope_file),
    })
    print(json.dumps({
        "total_rows": stats["total_rows"],
        "queue_rows": len(queue),
        "structure": dict(stats["structure"]),
        "radical": dict(stats["radical"]),
        "strokes": dict(stats["strokes"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
