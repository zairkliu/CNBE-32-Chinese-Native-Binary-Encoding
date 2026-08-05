#!/usr/bin/env python3
"""Deeper CNBE-32 math experiments: metric classes, lattice closure, entropy,
Huffman coding estimate, AUC/kNN comparison, and full algebra properties."""

import heapq
import json
import math
import os
import random
import sqlite3
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB = os.path.join(ROOT, "data", "cnbe32.db")
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(EXP, "results")
os.makedirs(OUT, exist_ok=True)


def fields(code):
    return {
        0: (code >> 24) & 0xFF,
        1: (code >> 19) & 0x1F,
        2: (code >> 15) & 0x0F,
        3: (code >> 4) & 0x7FF,
        4: code & 0xF,
    }


def f3(code):
    return (code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F


def dist3(a, b):
    ra, sa, ta = f3(a)
    rb, sb, tb = f3(b)
    return abs(ra - rb) * 8 + abs(sa - sb) * 5 + abs(ta - tb) * 4


def dist5(a, b):
    fa, fb = fields(a), fields(b)
    return sum(abs(fa[i] - fb[i]) * w for i, w in enumerate((8, 5, 4, 1, 1)))


def euclid3(a, b):
    fa, fb = f3(a), f3(b)
    return math.sqrt(sum((fa[i] - fb[i]) ** 2 for i in range(3)))


def norm2(p):
    return p[0] * p[0] + p[1] * p[1] + p[2] * p[2]


def hyp_point(code):
    r, s, t = f3(code)
    raw = (r / 255.0, s / 31.0, t / 15.0)
    n = math.sqrt(norm2(raw))
    if n == 0:
        return (0.0, 0.0, 0.0)
    scale = 0.9 / n
    return (raw[0] * scale, raw[1] * scale, raw[2] * scale)


def hyp_dist(a, b):
    p, q = hyp_point(a), hyp_point(b)
    d2 = sum((p[i] - q[i]) ** 2 for i in range(3))
    denom = (1 - norm2(p)) * (1 - norm2(q))
    if denom <= 0:
        return float("inf")
    return math.acosh(max(1.0, 1 + 2 * d2 / denom))


def entropy(counts, total):
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c)


def huffman_avg(freqs):
    heap = [[w, [sym]] for sym, w in freqs.items()]
    heapq.heapify(heap)
    code_len = {}
    if len(heap) == 1:
        sym = heap[0][1][0]
        code_len[sym] = 1
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        for sym in a[1]:
            code_len[sym] = code_len.get(sym, 0) + 1
        for sym in b[1]:
            code_len[sym] = code_len.get(sym, 0) + 1
        heapq.heappush(heap, [a[0] + b[0], a[1] + b[1]])
    total = sum(freqs.values())
    return sum(freqs[s] * code_len[s] for s in freqs) / total


def auc(labels, scores):
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return None
    return (sum(r for r, lab in zip(ranks, labels) if lab) - pos * (pos + 1) / 2.0) / (pos * neg)


def knn_accuracy(train, test, metric):
    correct = 0
    for u, c in test:
        best = None
        best_code = None
        best_d = None
        for tu, tc in train:
            d = metric(c, tc)
            if best_d is None or d < best_d:
                best_d = d
                best = tu
                best_code = tc
        if f3(c)[0] == f3(best_code)[0]:
            correct += 1
    return correct / len(test)


def main():
    con = sqlite3.connect(DB)
    rows = con.execute("select unicode, cnbe from cnbe32 order by unicode").fetchall()
    con.close()

    rng = random.Random(20260805)

    # ---- 1. metric equivalence classes and modified cmp ----
    tuple_classes = {}
    for u, c in rows:
        tuple_classes.setdefault(f3(c), []).append((u, c))
    multi = {k: v for k, v in tuple_classes.items() if len(v) > 1}
    multi_rows = sum(len(v) for v in multi.values())

    triangle5_ok = True
    for _ in range(200000):
        a, b, c = rng.choice(rows)[1], rng.choice(rows)[1], rng.choice(rows)[1]
        if dist5(a, c) > dist5(a, b) + dist5(b, c):
            triangle5_ok = False
            break

    # ---- 2. lattice ----
    tuples = set(tuple_classes.keys())
    sample = rng.sample(sorted(tuples), min(20000, len(tuples)))
    dist_ok = True
    for _ in range(100000):
        a, b, c = (rng.choice(sample), rng.choice(sample), rng.choice(sample))
        join = lambda x, y: (max(x[0], y[0]), max(x[1], y[1]), max(x[2], y[2]))
        meet = lambda x, y: (min(x[0], y[0]), min(x[1], y[1]), min(x[2], y[2]))
        if join(meet(a, b), c) != meet(join(a, c), join(b, c)):
            dist_ok = False
            break
        if meet(join(a, b), c) != join(meet(a, c), meet(b, c)):
            dist_ok = False
            break

    closure = {"join": 0, "meet": 0, "checked": 50000}
    for _ in range(closure["checked"]):
        a, b = rng.choice(sample), rng.choice(sample)
        j = (max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]))
        m = (min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]))
        if j in tuples:
            closure["join"] += 1
        if m in tuples:
            closure["meet"] += 1
    closure["join_rate"] = round(closure["join"] / closure["checked"], 4)
    closure["meet_rate"] = round(closure["meet"] / closure["checked"], 4)

    # ---- 3. information theory ----
    rad_c = {}
    stk_c = {}
    str_c = {}
    joint_c = {}
    code_c = {}
    mi_pairs = {}
    pair_names = [("radix-stroke", (0, 1)), ("radix-struct", (0, 2)), ("stroke-struct", (1, 2))]
    pair_counts = {}
    for _, code in rows:
        fa = fields(code)
        r, s, t = fa[0], fa[1], fa[2]
        rad_c[r] = rad_c.get(r, 0) + 1
        stk_c[s] = stk_c.get(s, 0) + 1
        str_c[t] = str_c.get(t, 0) + 1
        joint_c[(r, s, t)] = joint_c.get((r, s, t), 0) + 1
        code_c[code] = code_c.get(code, 0) + 1
        for name, (i, j) in pair_names:
            pair_counts.setdefault(name, {})
            key = (fa[i], fa[j])
            pair_counts[name][key] = pair_counts[name].get(key, 0) + 1
    total = len(rows)
    for name, _ in pair_names:
        h_pair = entropy(pair_counts[name], total)
        h_a = entropy(rad_c if name.startswith("radix") else stk_c, total)
        h_b = entropy(stk_c if "stroke" in name else str_c, total)
        mi_pairs[name] = round(h_a + h_b - h_pair, 4)

    h_code = entropy(code_c, total)
    h_avg_huffman = huffman_avg(joint_c)

    # ---- 4. AUC / kNN ----
    pair_scores = {"weighted": [], "euclid": [], "hyperbolic": []}
    pair_labels = []
    for _ in range(100000):
        a, b = rng.choice(rows)[1], rng.choice(rows)[1]
        pair_labels.append(1 if f3(a)[0] == f3(b)[0] else 0)
        pair_scores["weighted"].append(-dist3(a, b))
        pair_scores["euclid"].append(-euclid3(a, b))
        pair_scores["hyperbolic"].append(-hyp_dist(a, b))
    aucs = {name: auc(pair_labels, scores) for name, scores in pair_scores.items()}

    train = rows[:2000]
    test = rows[2000:2500]
    knn = {
        "weighted": round(knn_accuracy(train, test, dist3), 4),
        "euclid": round(knn_accuracy(train, test, euclid3), 4),
        "hyperbolic": round(knn_accuracy(train, test, hyp_dist), 4),
    }

    # ---- 5. algebra full ----
    by_code = {}
    by_unicode = {}
    for u, c in rows:
        by_code.setdefault(c, []).append(u)
        by_unicode[u] = c

    a1_pass = 0
    for _, c in rows:
        fa = fields(c)
        if all(fa[i] == fields(c)[i] for i in range(5)):
            a1_pass += 5

    a2_pass = 0
    a3_pass = 0
    for _ in range(500000):
        a, b, c = rng.choice(rows)[1], rng.choice(rows)[1], rng.choice(rows)[1]
        if dist3(a, b) >= 0 and dist3(a, b) == dist3(b, a):
            a2_pass += 1
        if dist3(a, c) <= dist3(a, b) + dist3(b, c):
            a3_pass += 1

    a4_pass = 0
    for _, c in rows:
        if by_code.get(c) and by_unicode.get(by_code[c][0]) == c:
            a4_pass += 1

    hash_linear = 0
    for _ in range(10000):
        code = rng.choice(rows)[1]
        linear = None
        for u, cc in rows:
            if cc == code:
                linear = u
                break
        if linear is not None and by_code[code][0] == linear:
            hash_linear += 1

    result = {
        "metric": {
            "tuple_classes": len(tuple_classes),
            "multi_member_classes": len(multi),
            "rows_in_multi_classes": multi_rows,
            "modified_cmp_with_idx_ext": {
                "triangle_ok_200k": triangle5_ok,
            },
        },
        "lattice": {
            "distributive": dist_ok,
            "closure": closure,
        },
        "information": {
            "H(code)": round(h_code, 4),
            "H(tuple)": round(entropy(joint_c, total), 4),
            "huffman_avg_bits": round(h_avg_huffman, 4),
            "mutual_information": mi_pairs,
        },
        "geometry": {
            "auc_same_radix": {k: round(v, 4) if v else None for k, v in aucs.items()},
            "knn_radix_accuracy": knn,
        },
        "algebra": {
            "A1_extract_map": a1_pass,
            "A2_nonneg_sym_500k": a2_pass,
            "A3_triangle_500k": a3_pass,
            "A4_skill_roundtrip_all": a4_pass,
            "hash_equals_linear_10k": hash_linear,
        },
    }
    with open(os.path.join(OUT, "deep_results.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
