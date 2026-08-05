#!/usr/bin/env python3
"""Validate metric-space axioms for cnbe.cmp."""

import json
import os
import random
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F


def dist(a, b):
    ra, sa, ta = fields(a)
    rb, sb, tb = fields(b)
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()
    codes = [c for _, c in rows]

    rng = random.Random(42)

    # non-negative / symmetric
    nonneg = sym = True
    for _ in range(200000):
        a, b = rng.choice(codes), rng.choice(codes)
        d = dist(a, b)
        if d < 0:
            nonneg = False
        if d != dist(b, a):
            sym = False

    # identity: D == 0 iff same tuple; report duplicate-tuple pairs
    tuple_groups = {}
    for u, c in rows:
        tuple_groups.setdefault(fields(c), []).append((u, c))
    zero_diff_pairs = 0
    for vals in tuple_groups.values():
        if len(vals) > 1:
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    if vals[i][1] != vals[j][1]:
                        zero_diff_pairs += 1

    # triangle inequality
    violations = 0
    checked = 0
    for _ in range(200000):
        a, b, c = rng.choice(codes), rng.choice(codes), rng.choice(codes)
        checked += 1
        if dist(a, c) > dist(a, b) + dist(b, c):
            violations += 1

    result = {
        "rows": len(codes),
        "non_negative": nonneg,
        "symmetric": sym,
        "triangle_checked": checked,
        "triangle_violations": violations,
        "triangle_holds": violations == 0,
        "zero_distance_different_codes": zero_diff_pairs,
        "note": "cmp excludes idx/ext, so different codes with identical radix/stroke/struct have distance 0",
    }
    with open(os.path.join(OUT, "metric_space.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
