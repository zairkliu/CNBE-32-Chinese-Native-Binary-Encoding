#!/usr/bin/env python3
"""Lattice / poset validation and 3D range-query acceleration."""

import json
import os
import random
import sqlite3
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()

    grid = [[[0 for _ in range(16)] for _ in range(32)] for _ in range(256)]
    tuples = set()
    for _, code in rows:
        r, s, t = fields(code)
        grid[r][s][t] += 1
        tuples.add((r, s, t))

    # 3D prefix sums
    pref = [[[0 for _ in range(17)] for _ in range(33)] for _ in range(257)]
    for r in range(256):
        for s in range(32):
            for t in range(16):
                pref[r + 1][s + 1][t + 1] = (
                    grid[r][s][t]
                    + pref[r][s + 1][t + 1]
                    + pref[r + 1][s][t + 1]
                    + pref[r + 1][s + 1][t]
                    - pref[r][s][t + 1]
                    - pref[r][s + 1][t]
                    - pref[r + 1][s][t]
                    + pref[r][s][t]
                )

    def range_count(r0, r1, s0, s1, t0, t1):
        return (
            pref[r1 + 1][s1 + 1][t1 + 1]
            - pref[r0][s1 + 1][t1 + 1]
            - pref[r1 + 1][s0][t1 + 1]
            - pref[r1 + 1][s1 + 1][t0]
            + pref[r0][s0][t1 + 1]
            + pref[r0][s1 + 1][t0]
            + pref[r1 + 1][s0][t0]
            - pref[r0][s0][t0]
        )

    # distributive-lattice properties on random tuples
    rng = random.Random(7)
    sample = rng.sample(sorted(tuples), min(20000, len(tuples)))
    checks = {"idempotent": True, "commutative": True, "associative": True, "absorption": True}
    for _ in range(50000):
        a, b, c = (rng.choice(sample), rng.choice(sample), rng.choice(sample))
        join = lambda x, y: (max(x[0], y[0]), max(x[1], y[1]), max(x[2], y[2]))
        meet = lambda x, y: (min(x[0], y[0]), min(x[1], y[1]), min(x[2], y[2]))
        if join(a, a) != a or meet(a, a) != a:
            checks["idempotent"] = False
        if join(a, b) != join(b, a) or meet(a, b) != meet(b, a):
            checks["commutative"] = False
        if join(join(a, b), c) != join(a, join(b, c)):
            checks["associative"] = False
        if meet(join(a, b), a) != a or join(meet(a, b), a) != a:
            checks["absorption"] = False

    # range query benchmark
    queries = []
    for _ in range(1000):
        r0, r1 = sorted((rng.randrange(256), rng.randrange(256)))
        s0, s1 = sorted((rng.randrange(32), rng.randrange(32)))
        t0, t1 = sorted((rng.randrange(16), rng.randrange(16)))
        queries.append((r0, r1, s0, s1, t0, t1))

    t0 = time.perf_counter()
    prefix_results = [range_count(*q) for q in queries]
    prefix_time = time.perf_counter() - t0

    def brute(q):
        r0, r1, s0, s1, t0, t1 = q
        return sum(
            1
            for _, code in rows
            for r, s, t in [fields(code)]
            if r0 <= r <= r1 and s0 <= s <= s1 and t0 <= t <= t1
        )

    t0 = time.perf_counter()
    brute_results = [brute(q) for q in queries]
    brute_time = time.perf_counter() - t0

    result = {
        "rows": len(rows),
        "distinct_tuples": len(tuples),
        "product_space": 256 * 32 * 16,
        "lattice_properties": checks,
        "range_queries": len(queries),
        "prefix_time_s": round(prefix_time, 6),
        "brute_time_s": round(brute_time, 6),
        "speedup": round(brute_time / prefix_time, 2) if prefix_time else None,
        "all_matches": prefix_results == brute_results,
    }
    with open(os.path.join(OUT, "lattice_range.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
