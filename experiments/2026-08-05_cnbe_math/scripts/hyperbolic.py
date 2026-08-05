#!/usr/bin/env python3
"""Hyperbolic-geometry distance analysis for CNBE-32 fields."""

import json
import math
import os
import random
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F


def point(code):
    r, s, t = fields(code)
    raw = (r / 255.0, s / 31.0, t / 15.0)
    n = math.sqrt(norm2(raw))
    if n == 0:
        return (0.0, 0.0, 0.0)
    scale = 0.9 / n
    return (raw[0] * scale, raw[1] * scale, raw[2] * scale)


def norm2(p):
    return p[0] * p[0] + p[1] * p[1] + p[2] * p[2]


def poincare_dist(p, q):
    d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
    denom = (1 - norm2(p)) * (1 - norm2(q))
    if denom <= 0:
        return float("inf")
    arg = 1 + 2 * d2 / denom
    return math.acosh(max(1.0, arg))


def weighted_dist(a, b):
    ra, sa, ta = fields(a)
    rb, sb, tb = fields(b)
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()
    codes = [c for _, c in rows]
    rng = random.Random(2026)

    same_rad = []
    diff_rad = []
    hyp = []
    lin = []
    for _ in range(200000):
        a, b = rng.choice(codes), rng.choice(codes)
        d = poincare_dist(point(a), point(b))
        w = weighted_dist(a, b)
        hyp.append(d)
        lin.append(w)
        if fields(a)[0] == fields(b)[0]:
            same_rad.append(d)
        else:
            diff_rad.append(d)

    mean_hyp = sum(hyp) / len(hyp)
    mean_lin = sum(lin) / len(lin)
    same_mean = sum(same_rad) / len(same_rad)
    diff_mean = sum(diff_rad) / len(diff_rad)

    def rank_list(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0] * len(vals)
        for pos, idx in enumerate(order):
            ranks[idx] = pos
        return ranks

    rl = rank_list(lin)
    rh = rank_list(hyp)
    n = len(rl)
    mean = n / 2
    cov = sum((rl[i] - mean) * (rh[i] - mean) for i in range(n))
    var = sum((x - mean) ** 2 for x in rl)
    spearman = cov / var if var else 0

    result = {
        "samples": len(hyp),
        "mean_hyperbolic": round(mean_hyp, 4),
        "mean_weighted": round(mean_lin, 4),
        "same_radix_mean_hyp": round(same_mean, 4),
        "diff_radix_mean_hyp": round(diff_mean, 4),
        "radix_separation_ratio": round(diff_mean / same_mean, 4) if same_mean else None,
        "rank_correlation_weighted_hyp": round(spearman, 4),
        "note": "Hyperbolic distance is a monotone-ish transform of the field vector; it does not add new labeled-benchmark information without a confusable-character dataset.",
    }
    with open(os.path.join(OUT, "hyperbolic.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
