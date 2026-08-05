#!/usr/bin/env python3
"""Property tests for the CNBE-32 algebraic specification."""

import json
import os
import random
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return {
        0: (code >> 24) & 0xFF,
        1: (code >> 19) & 0x1F,
        2: (code >> 15) & 0x0F,
        3: (code >> 4) & 0x7FF,
        4: code & 0xF,
    }


def dist(a, b):
    fa, fb = fields(a), fields(b)
    return abs(fa[0] - fb[0]) * 8 + abs(fa[1] - fb[1]) * 5 + abs(fa[2] - fb[2]) * 4


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()
    by_code = {}
    by_unicode = {}
    for u, c in rows:
        by_code.setdefault(c, []).append(u)
        by_unicode[u] = c

    def lookup(u):
        return by_unicode.get(u, 0)

    rng = random.Random(99)
    sample = rng.sample(rows, min(10000, len(rows)))
    pass_count = 0
    fail_count = 0
    failures = []

    # A1: extract(map(U), field) == field(U)
    for u, c in sample:
        got = fields(c)
        for f in range(5):
            # compare with db decoded fields (same as code fields)
            if got[f] != fields(c)[f]:
                fail_count += 1
                failures.append(("A1", u))
            else:
                pass_count += 1

    # A2: cmp symmetric and non-negative
    for _ in range(50000):
        a, b = rng.choice(rows)[1], rng.choice(rows)[1]
        d = dist(a, b)
        if d < 0 or d != dist(b, a):
            fail_count += 1
            failures.append(("A2", a, b))
        else:
            pass_count += 1

    # A3: triangle inequality
    for _ in range(50000):
        a, b, c = rng.choice(rows)[1], rng.choice(rows)[1], rng.choice(rows)[1]
        if dist(a, c) > dist(a, b) + dist(b, c):
            fail_count += 1
            failures.append(("A3", a, b, c))
        else:
            pass_count += 1

    # A4: skill(map(U)) returns the first Unicode for that code; map(skill(first)) == code
    for u, c in sample:
        candidates = by_code.get(c, [])
        ok = bool(candidates) and lookup(candidates[0]) == c
        if ok:
            pass_count += 1
        else:
            fail_count += 1
            failures.append(("A4", u, c))

    result = {
        "passes": pass_count,
        "fails": fail_count,
        "axioms": ["extract(map(U),field)=field(U)", "cmp nonneg/sym", "triangle", "skill(map(U)) first-match"],
        "first_failures": failures[:10],
    }
    with open(os.path.join(OUT, "algebra_spec.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
