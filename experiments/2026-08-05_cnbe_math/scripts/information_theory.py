#!/usr/bin/env python3
"""Entropy analysis of CNBE-32 field allocation."""

import json
import math
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F


def entropy(counts, total):
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c)


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()
    total = len(rows)

    rad_counts = {}
    stk_counts = {}
    str_counts = {}
    joint_counts = {}
    rad_stk_joint = {}
    for _, code in rows:
        r, s, t = fields(code)
        rad_counts[r] = rad_counts.get(r, 0) + 1
        stk_counts[s] = stk_counts.get(s, 0) + 1
        str_counts[t] = str_counts.get(t, 0) + 1
        joint_counts[(r, s, t)] = joint_counts.get((r, s, t), 0) + 1
        rad_stk_joint[(r, s)] = rad_stk_joint.get((r, s), 0) + 1

    h_rad = entropy(rad_counts, total)
    h_stk = entropy(stk_counts, total)
    h_str = entropy(str_counts, total)
    h_joint = entropy(joint_counts, total)

    # H(stroke | radix)
    h_stk_given_rad = 0.0
    for r, c in rad_counts.items():
        cond = {k[1]: v for k, v in rad_stk_joint.items() if k[0] == r}
        h_stk_given_rad += (c / total) * entropy(cond, c)

    mi_rad_stk = h_rad + h_stk - entropy(rad_stk_joint, total)
    capacity = 8 + 5 + 4
    result = {
        "rows": total,
        "H(radix)": round(h_rad, 4),
        "H(stroke)": round(h_stk, 4),
        "H(struct)": round(h_str, 4),
        "H(radix,stroke,struct)": round(h_joint, 4),
        "H(stroke|radix)": round(h_stk_given_rad, 4),
        "I(radix;stroke)": round(mi_rad_stk, 4),
        "field_capacity_bits": capacity,
        "redundancy_bits": round(capacity - h_joint, 4),
        "effective_bits": round(h_joint, 4),
        "distinct_radix": len(rad_counts),
        "distinct_stroke": len(stk_counts),
        "distinct_struct": len(str_counts),
    }
    with open(os.path.join(OUT, "information_theory.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
