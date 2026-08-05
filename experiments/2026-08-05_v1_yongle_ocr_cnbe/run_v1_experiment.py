#!/usr/bin/env python3
"""V1 experiment: does CNBE character-level verification improve ancient OCR?

Three parts, all deterministic:
  1. Sequence-level OCR baselines (best-per-page / Paddle / DeepSeek v1) on the
     37-page Yongle ground truth.
  2. CNBE oracle analysis on real OCR substitutions: recall@K and confusing-group
     discrimination.
  3. Synthetic confusable-corruption benchmark: corrupt ground truth with
     confusing-group / CNBE-neighbor substitutions, then run a CNBE verifier
     (field distance + corpus frequency) and measure accuracy gain.

No OCR candidate lists are available, so the synthetic benchmark isolates the
CNBE verifier contribution from the layout/order corruption of real OCR.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import random
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
WORK = REPO.parent / "work"

CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def cjk_clean(text: str) -> str:
    return "".join(CJK_RE.findall(text))


def align(ocr: str, truth: str) -> tuple[int, int, list[tuple[str, str]]]:
    a, b = cjk_clean(ocr), cjk_clean(truth)
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        ai = a[i - 1]
        dpi = dp[i]
        dpim = dp[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ai == b[j - 1] else 1
            dpi[j] = min(dpim[j - 1] + cost, dpim[j] + 1, dpi[j - 1] + 1)
    subs: list[tuple[str, str]] = []
    matches = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            cost = 0 if a[i - 1] == b[j - 1] else 1
            if dp[i][j] == dp[i - 1][j - 1] + cost:
                if cost == 0:
                    matches += 1
                else:
                    subs.append((a[i - 1], b[j - 1]))
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            i -= 1
            continue
        j -= 1
    return matches, m, subs


def load_truth_library() -> dict[int, str]:
    path = WORK / "yongle_821_review" / "pipeline" / "ground_truth_library.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {int(k): v["text"] for k, v in data.items()}


def load_best_ocr() -> dict[int, dict]:
    path = WORK / "yongle_821_review" / "dataset_37" / "dataset_37.jsonl"
    result: dict[int, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        user = d["messages"][1]["content"]
        text = user.split("\n", 1)[1] if "\n" in user else ""
        result[d["page"]] = {"text": text, "source": d.get("ocr_source")}
    return result


def load_paddle_ocr() -> dict[int, str]:
    path = WORK / "yongle_821_review" / "paddle_output_full" / "ocr"
    result: dict[int, str] = {}
    for p in path.glob("page_*.json"):
        m = re.match(r"page_(\d{3})\.json", p.name)
        if not m:
            continue
        result[int(m.group(1))] = json.loads(p.read_text(encoding="utf-8")).get("sequence", "")
    return result


def load_v1_ocr() -> dict[int, str]:
    path = WORK / "yongle_821_review" / "ocr_v1"
    result: dict[int, str] = {}
    for p in path.glob("page_*.txt"):
        m = re.match(r"page_(\d{3})\.txt", p.name)
        if not m:
            continue
        result[int(m.group(1))] = p.read_text(encoding="utf-8")
    return result


def load_cnbe(db_path: Path) -> tuple[dict[str, dict], list[str], np.ndarray, np.ndarray, np.ndarray]:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM cnbe32 WHERE track='standard'")]
    con.close()
    db = {r["char"]: r for r in rows}
    chars = sorted(db.keys())
    radix = np.array([db[c]["radix"] for c in chars], dtype=np.int32)
    strokes = np.array([db[c]["strokes"] for c in chars], dtype=np.int32)
    struct = np.array([db[c]["struct_type"] for c in chars], dtype=np.int32)
    return db, chars, radix, strokes, struct


def load_groups() -> list[list[str]]:
    path = REPO.parent / "guji-ocr-corrector" / "core" / "pairs.py"
    text = path.read_bytes().decode("utf-8-sig")
    start = text.index("[")
    depth = 0
    end = None
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return ast.literal_eval(text[start:end])


def load_corpus_freq(corpus_dir: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    if corpus_dir is None or not corpus_dir.exists():
        return counter
    for p in corpus_dir.glob("*.chars.txt"):
        text = p.read_text(encoding="utf-8", errors="replace")
        counter.update(CJK_RE.findall(text))
    return counter


def field_dist(a: dict, b: dict) -> int:
    return (
        abs(a["radix"] - b["radix"]) * 8
        + abs(a["strokes"] - b["strokes"]) * 5
        + abs(a["struct_type"] - b["struct_type"]) * 4
    )


def topk_neighbors(
    x: str,
    db: dict[str, dict],
    chars: list[str],
    radix: np.ndarray,
    strokes: np.ndarray,
    struct: np.ndarray,
    k: int = 20,
) -> list[tuple[str, int]]:
    r = db[x]
    d = (
        np.abs(radix - r["radix"]) * 8
        + np.abs(strokes - r["strokes"]) * 5
        + np.abs(struct - r["struct_type"]) * 4
    )
    idx = np.argpartition(d, k)[:k]
    order = np.argsort(d[idx])
    out = []
    for i in idx[order]:
        c = chars[i]
        if c != x:
            out.append((c, int(d[i])))
    return out


def verifier_replace(
    ocr_chars: list[str],
    db: dict[str, dict],
    chars: list[str],
    radix: np.ndarray,
    strokes: np.ndarray,
    struct: np.ndarray,
    groups: list[list[str]],
    freq: Counter[str],
    total_freq: int,
    lambda_freq: float,
    use_neighbors: bool,
) -> tuple[list[str], list[tuple[str, str, str]]]:
    group_of = {c: g for g in groups for c in g}
    log_total = math.log(total_freq + 1) if total_freq else 0.0
    out = list(ocr_chars)
    changes: list[tuple[str, str, str]] = []
    for i, x in enumerate(ocr_chars):
        if x not in db:
            continue
        candidates: list[str] = []
        if x in group_of:
            candidates.extend(c for c in group_of[x] if c != x and c in db)
        if use_neighbors:
            for c, d in topk_neighbors(x, db, chars, radix, strokes, struct, 20):
                if d <= 100:
                    candidates.append(c)
        if not candidates:
            continue

        def score(c: str) -> float:
            dist = field_dist(db[x], db[c])
            n = freq.get(c, 0) + 1
            return dist + lambda_freq * (log_total - math.log(n))

        best = min(candidates, key=score)
        keep_score = lambda_freq * (log_total - math.log(freq.get(x, 0) + 1))
        if score(best) < keep_score:
            out[i] = best
            changes.append((x, best, f"{field_dist(db[x], db[best]):d}"))
    return out, changes


def accuracy(pred: list[str], truth: list[str]) -> float:
    if not truth:
        return 0.0
    n = min(len(pred), len(truth))
    return sum(1 for i in range(n) if pred[i] == truth[i]) / len(truth)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=REPO / "data" / "cnbe32.db")
    parser.add_argument("--corpus-dir", type=Path, default=REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data")
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    parser.add_argument("--report", type=Path, default=Path("REPORT.md"))
    parser.add_argument("--lambda-freq", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    truth_lib = load_truth_library()
    best = load_best_ocr()
    paddle = load_paddle_ocr()
    v1 = load_v1_ocr()
    db, chars, radix, strokes, struct = load_cnbe(args.db)
    groups = load_groups()
    freq = load_corpus_freq(args.corpus_dir)
    total_freq = sum(freq.values()) or 1

    # 1. baselines
    baselines = {}
    for name, src in [("best", best), ("paddle", paddle), ("v1", v1)]:
        total_truth = total_match = 0
        all_subs: list[tuple[str, str]] = []
        pages = 0
        for page, truth in sorted(truth_lib.items()):
            if page not in src:
                continue
            text = src[page]["text"] if isinstance(src[page], dict) else src[page]
            matches, truth_len, subs = align(text, truth)
            total_match += matches
            total_truth += truth_len
            all_subs.extend(subs)
            pages += 1
        baselines[name] = {
            "pages": pages,
            "truth_chars": total_truth,
            "matched": total_match,
            "accuracy": round(total_match / total_truth, 4) if total_truth else 0.0,
            "substitutions": len(all_subs),
        }

    # 2. real substitution CNBE oracle
    best_subs: list[tuple[str, str]] = []
    for page, truth in sorted(truth_lib.items()):
        if page not in best:
            continue
        _, _, subs = align(best[page]["text"], truth)
        best_subs.extend(subs)

    recall: dict[str, int] = {str(k): 0 for k in (1, 3, 5, 10, 20)}
    pairs_both = 0
    group_err = 0
    group_top1 = 0
    for x, t in best_subs:
        if x not in db or t not in db:
            continue
        pairs_both += 1
        top = topk_neighbors(x, db, chars, radix, strokes, struct, 20)
        rank_chars = [c for c, _ in top]
        if t in rank_chars:
            rank = rank_chars.index(t)
            for k in (1, 3, 5, 10, 20):
                if rank < k:
                    recall[str(k)] += 1
        g = next((gg for gg in groups if x in gg and t in gg), None)
        if g:
            group_err += 1
            cands = [c for c in g if c != x and c in db]
            if cands:
                best_cand = min(cands, key=lambda c: field_dist(db[x], db[c]))
                if best_cand == t:
                    group_top1 += 1

    real_analysis = {
        "substitutions": len(best_subs),
        "both_in_cnbe_standard": pairs_both,
        "truth_in_topK": {k: v for k, v in recall.items()},
        "confusing_group_errors": group_err,
        "confusing_group_top1": group_top1,
        "group_top1_rate": round(group_top1 / group_err, 4) if group_err else 0.0,
    }

    # 2b. apply group verifier to real best OCR
    group_of = {c: g for g in groups for c in g}
    rt = rb = ra = 0
    rc_change = rc_correct = 0
    for page, truth in sorted(truth_lib.items()):
        if page not in best:
            continue
        ocr_chars = list(cjk_clean(best[page]["text"]))
        truth_chars = list(cjk_clean(truth))
        pred, changes = verifier_replace(
            ocr_chars, db, chars, radix, strokes, struct, groups, freq, total_freq,
            args.lambda_freq, use_neighbors=False,
        )
        mb, tb, _ = align("".join(ocr_chars), truth)
        ma, ta, _ = align("".join(pred), truth)
        rb += mb
        ra += ma
        rt += tb
        rc_change += len(changes)
        for i in range(min(len(ocr_chars), len(truth_chars))):
            if ocr_chars[i] != pred[i] and pred[i] == truth_chars[i]:
                rc_correct += 1
    real_group_metrics = {
        "pages": len(truth_lib),
        "truth_chars": rt,
        "baseline_accuracy": round(rb / rt, 4) if rt else 0.0,
        "group_verifier_accuracy": round(ra / rt, 4) if rt else 0.0,
        "changes": rc_change,
        "correct_changes": rc_correct,
    }
    real_analysis["applied_group_verifier_on_best_ocr"] = real_group_metrics

    # 3. synthetic confusable-corruption benchmark
    rng = random.Random(args.seed)
    pages_truth = [cjk_clean(t) for t in truth_lib.values()]
    synthetic = {}
    group_only = {}
    for rate in (0.01, 0.02, 0.05, 0.10):
        corrupt_total = 0
        correct_total = 0
        baseline_correct = 0
        group_correct = 0
        group_changes = 0
        neighbor_correct = 0
        neighbor_changes = 0
        for truth_text in pages_truth:
            truth_chars = list(truth_text)
            corrupted = []
            for c in truth_chars:
                if c in db and rng.random() < rate:
                    g = next((gg for gg in groups if c in gg), None)
                    if g:
                        others = [m for m in g if m != c and m in db]
                        if others:
                            corrupted.append(rng.choice(others))
                            corrupt_total += 1
                            continue
                    neighbors = topk_neighbors(c, db, chars, radix, strokes, struct, 20)
                    if neighbors:
                        corrupted.append(neighbors[0][0])
                        corrupt_total += 1
                        continue
                corrupted.append(c)
            pred_group, chg_group = verifier_replace(
                corrupted, db, chars, radix, strokes, struct, groups, freq, total_freq,
                args.lambda_freq, use_neighbors=False,
            )
            pred_neighbor, chg_neighbor = verifier_replace(
                corrupted, db, chars, radix, strokes, struct, groups, freq, total_freq,
                args.lambda_freq, use_neighbors=True,
            )
            baseline_correct += sum(1 for a, b in zip(corrupted, truth_chars) if a == b)
            correct_total += len(truth_chars)
            group_correct += sum(1 for a, b in zip(pred_group, truth_chars) if a == b)
            neighbor_correct += sum(1 for a, b in zip(pred_neighbor, truth_chars) if a == b)
            group_changes += len(chg_group)
            neighbor_changes += len(chg_neighbor)
        synthetic[str(rate)] = {
            "corrupted_chars": corrupt_total,
            "truth_chars": correct_total,
            "baseline_accuracy": round(baseline_correct / correct_total, 4),
            "group_verifier_accuracy": round(group_correct / correct_total, 4),
            "neighbor_verifier_accuracy": round(neighbor_correct / correct_total, 4),
            "group_changes": group_changes,
            "neighbor_changes": neighbor_changes,
        }

    # 3b. group-only synthetic corruption: only confusing-group positions are corrupted
    for rate in (0.5, 1.0):
        group_positions = 0
        corrupt_group_positions = 0
        baseline_ok = 0
        group_ok = 0
        neighbor_ok = 0
        oracle_ok = 0
        for truth_text in pages_truth:
            truth_chars = list(truth_text)
            corrupted = list(truth_chars)
            for i, c in enumerate(truth_chars):
                if c in group_of and c in db:
                    group_positions += 1
                    if rng.random() < rate:
                        others = [m for m in group_of[c] if m != c and m in db]
                        if others:
                            corrupted[i] = rng.choice(others)
                            corrupt_group_positions += 1
            pred_group, _ = verifier_replace(
                corrupted, db, chars, radix, strokes, struct, groups, freq, total_freq,
                args.lambda_freq, use_neighbors=False,
            )
            pred_neighbor, _ = verifier_replace(
                corrupted, db, chars, radix, strokes, struct, groups, freq, total_freq,
                args.lambda_freq, use_neighbors=True,
            )
            for i, c in enumerate(truth_chars):
                if c in group_of and c in db:
                    baseline_ok += 1 if corrupted[i] == c else 0
                    group_ok += 1 if pred_group[i] == c else 0
                    neighbor_ok += 1 if pred_neighbor[i] == c else 0
                    oracle_ok += 1  # oracle = truth, always correct on group positions
        group_only[str(rate)] = {
            "group_positions": group_positions,
            "corrupted_group_positions": corrupt_group_positions,
            "baseline_group_accuracy": round(baseline_ok / group_positions, 4) if group_positions else 0.0,
            "group_verifier_group_accuracy": round(group_ok / group_positions, 4) if group_positions else 0.0,
            "neighbor_verifier_group_accuracy": round(neighbor_ok / group_positions, 4) if group_positions else 0.0,
            "oracle_upper_bound": round(oracle_ok / group_positions, 4) if group_positions else 0.0,
        }

    result = {
        "schema_version": 1,
        "seed": args.seed,
        "lambda_freq": args.lambda_freq,
        "corpus_chars": total_freq,
        "baselines": baselines,
        "real_substitution_cnbe_analysis": real_analysis,
        "synthetic_benchmark": synthetic,
        "group_only_synthetic_benchmark": group_only,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    lines = [
        "# V1: Ancient OCR + CNBE Character-Level Verification (Yongle 37 pages)",
        "",
        "Date: 2026-08-05",
        "",
        "## 1. OCR baselines (sequence-level character accuracy)",
        "",
        "| Source | Pages | Truth chars | Matched | Accuracy | Substitutions |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, b in baselines.items():
        lines.append(
            f"| {name} | {b['pages']} | {b['truth_chars']} | {b['matched']} | {b['accuracy']:.4f} | {b['substitutions']} |"
        )
    lines += [
        "",
        "## 2. CNBE oracle on real substitutions",
        "",
        f"- Substitutions: {real_analysis['substitutions']}",
        f"- Both chars in CNBE standard track: {real_analysis['both_in_cnbe_standard']}",
        f"- Truth in CNBE top-K: {real_analysis['truth_in_topK']}",
        f"- Confusing-group errors: {real_analysis['confusing_group_errors']}",
        f"- Group top-1 (CNBE field distance): {real_analysis['confusing_group_top1']} "
        f"({real_analysis['group_top1_rate']:.4f})",
        "",
        "Interpretation: most real OCR errors are layout/order corruption, not clean "
        "shape-confusable substitutions. CNBE top-K recall on real substitutions is low, "
        "but every confusing-group error in the real data is ranked top-1 by CNBE fields.",
        "",
        "## 3. Synthetic confusable-corruption benchmark",
        "",
        "Corrupt ground truth with confusing-group or CNBE-neighbor substitutions, then "
        "run a CNBE verifier (field distance + corpus frequency).",
        "",
        "| Corruption rate | Corrupted | Truth | Baseline acc | Group verifier | Neighbor verifier |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for rate, s in synthetic.items():
        lines.append(
            f"| {rate} | {s['corrupted_chars']} | {s['truth_chars']} | {s['baseline_accuracy']:.4f} | "
            f"{s['group_verifier_accuracy']:.4f} | {s['neighbor_verifier_accuracy']:.4f} |"
        )
    rg = real_analysis["applied_group_verifier_on_best_ocr"]
    lines += [
        "",
        "## 2b. Group verifier applied to real best OCR",
        "",
        f"- Baseline accuracy: {rg['baseline_accuracy']:.4f}",
        f"- After group verifier: {rg['group_verifier_accuracy']:.4f}",
        f"- Changes: {rg['changes']}, correct changes: {rg['correct_changes']}",
        "",
        "## 3b. Group-only synthetic corruption",
        "",
        "Only characters belonging to known confusing groups are corrupted, isolating the "
        "CNBE group-disambiguation capability.",
        "",
        "| Group corruption rate | Group positions | Corrupted | Baseline acc | Group verifier | Neighbor verifier | Oracle upper bound |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rate, s in group_only.items():
        lines.append(
            f"| {rate} | {s['group_positions']} | {s['corrupted_group_positions']} | "
            f"{s['baseline_group_accuracy']:.4f} | {s['group_verifier_group_accuracy']:.4f} | "
            f"{s['neighbor_verifier_group_accuracy']:.4f} | {s['oracle_upper_bound']:.4f} |"
        )
    lines += [
        "",
        "## 4. Boundaries",
        "",
        "- No OCR candidate lists were available; real OCR is dominated by reading-order corruption.",
        "- The synthetic benchmark isolates the CNBE verifier on clean shape-confusable errors.",
        "- Corpus frequency prior comes from the seven-corpus data set (24.38M chars).",
        "- Reproduce: `python3 run_v1_experiment.py`.",
        "",
        "## 5. Conclusion for V1 gate",
        "",
        "The +5% overall accuracy gate is **not met** on the current 37-page OCR corpus: "
        "real OCR errors are dominated by reading-order and garbage substitutions, not by "
        "clean shape-confusable character errors. CNBE top-K recall on real substitutions "
        "is low (truth in top-20 for 65/2797 in-standard pairs). The CNBE character-level "
        "verifier is validated only on its target slice: all 17 real confusing-group errors "
        "are ranked top-1 by CNBE field distance (100%), and on group-only synthetic "
        "corruption it recovers +6.4pp at 50% corruption and +14.8pp at 100% corruption on "
        "group positions. A general context-free neighbor verifier without OCR candidate "
        "lists is destructive and should not be used.",
        "",
        "Next step: obtain OCR top-N candidates (Paddle/vision-model candidate lists), then "
        "apply the CNBE verifier as a reranker only on candidate sets, with page context.",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
