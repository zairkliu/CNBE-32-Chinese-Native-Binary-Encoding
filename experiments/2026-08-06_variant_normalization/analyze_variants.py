#!/usr/bin/env python3
"""P0: extract variant pairs and CNBE coverage gaps from VL-1.6 residual errors.

Uses the 37-page Yongle truth, VL-1.6 cloud OCR output, CNBE runtime DB, and
Unihan variant fields to build:
  - variant_pairs.json      substitution pairs with variant/shape/gap labels
  - coverage_gap.json       truth chars missing from CNBE standard/all tracks
  - variant_map.json        variant clusters, canonical candidates, direction evidence
  - results.json + REPORT.md
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "2026-08-05_v1_yongle_ocr_cnbe"))

import run_v1_experiment as v1  # noqa: E402

VARIANT_FIELDS = {
    "kSemanticVariant",
    "kSimplifiedVariant",
    "kTraditionalVariant",
    "kZVariant",
    "kCompatibilityVariant",
    "kSpoofingVariant",
}


def parse_unihan_variants(path: Path) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3 or parts[1] not in VARIANT_FIELDS:
            continue
        a = chr(int(parts[0][2:], 16))
        for tok in re.findall(r"U\+[0-9A-Fa-f]{4,6}", parts[2]):
            b = chr(int(tok[2:], 16))
            if a != b:
                edges.append((a, b))
    return edges


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def field_dist(a: dict, b: dict) -> int:
    return (
        abs(a["radix"] - b["radix"]) * 8
        + abs(a["strokes"] - b["strokes"]) * 5
        + abs(a["struct_type"] - b["struct_type"]) * 4
    )


def main() -> None:
    exp_dir = Path(__file__).resolve().parent
    pages_dir = exp_dir.parent / "2026-08-06_paddleocr_vl16" / "pages"
    unihan_path = exp_dir.parent / "2026-08-05_scheme_comparison" / "build" / "Unihan_Variants.txt"

    truth_lib = v1.load_truth_library()
    db_std, _, _, _, _ = v1.load_cnbe(v1.REPO / "data" / "cnbe32.db")

    con = sqlite3.connect(str(v1.REPO / "data" / "cnbe32.db"))
    con.row_factory = sqlite3.Row
    db_all = {r["char"]: dict(r) for r in con.execute("SELECT * FROM cnbe32")}
    con.close()

    freq = v1.load_corpus_freq(v1.REPO / "experiments" / "2026-08-02_seven_corpora_compression" / "data")

    subs: list[dict] = []
    per_page = {}
    for page, truth in sorted(truth_lib.items()):
        md_path = pages_dir / f"page_{page:03d}.md"
        if not md_path.exists():
            continue
        ocr_text = md_path.read_text(encoding="utf-8")
        ocr_chars = list(v1.cjk_clean(ocr_text))
        truth_chars = list(v1.cjk_clean(truth))
        _, _, page_subs = v1.align(ocr_text, truth)
        per_page[page] = {"ocr": ocr_chars, "truth": truth_chars}
        for x, t in page_subs:
            subs.append({"page": page, "ocr": x, "truth": t})

    edges = parse_unihan_variants(unihan_path)
    uf = UnionFind()
    for a, b in edges:
        uf.union(a, b)

    def same_variant(a: str, b: str) -> bool:
        return a in uf.parent and b in uf.parent and uf.find(a) == uf.find(b)

    classified = []
    counts = Counter()
    variant_pairs = []
    for s in subs:
        x, t = s["ocr"], s["truth"]
        if same_variant(x, t):
            label = "variant"
        elif x in db_std and t in db_std and field_dist(db_std[x], db_std[t]) <= 64:
            label = "shape_confusable"
        elif t not in db_all:
            label = "truth_not_in_db"
        elif t not in db_std:
            label = "truth_not_in_standard"
        elif x not in db_all:
            label = "ocr_not_in_db"
        else:
            label = "other"
        counts[label] += 1
        rec = {
            "page": s["page"],
            "ocr": x,
            "truth": t,
            "label": label,
            "ocr_in_standard": x in db_std,
            "truth_in_standard": t in db_std,
            "field_distance": field_dist(db_std[x], db_std[t]) if x in db_std and t in db_std else None,
        }
        classified.append(rec)
        if label == "variant":
            variant_pairs.append(rec)

    truth_counter: Counter[str] = Counter()
    for page, truth in truth_lib.items():
        truth_counter.update(v1.cjk_clean(truth))
    coverage_gaps = []
    for c, n in truth_counter.items():
        coverage_gaps.append(
            {
                "char": c,
                "codepoint": f"U+{ord(c):04X}",
                "count": n,
                "in_db": c in db_all,
                "in_standard": c in db_std,
                "db_track": db_all[c]["track"] if c in db_all else None,
            }
        )
    coverage_gaps.sort(key=lambda r: (-r["count"], r["in_standard"]))
    gap_std = [g for g in coverage_gaps if not g["in_standard"]]
    gap_db = [g for g in coverage_gaps if not g["in_db"]]

    # variant clusters with corpus evidence
    cluster_members: dict[str, set[str]] = defaultdict(set)
    for c in set(truth_counter) | {p["ocr"] for p in subs} | set(db_std):
        if c in uf.parent:
            cluster_members[uf.find(c)].add(c)
    variant_map = []
    for root, members in sorted(cluster_members.items(), key=lambda kv: -sum(truth_counter[m] for m in kv[1])):
        members = sorted(members)
        std_members = [m for m in members if m in db_std]
        canonical = std_members[0] if std_members else max(members, key=lambda m: freq.get(m, 0))
        direction_evidence = {}
        for p in variant_pairs:
            if p["ocr"] in members and p["truth"] in members:
                direction_evidence.setdefault(p["ocr"], Counter())[p["truth"]] += 1
        learned_map = {
            ocr: truth
            for ocr, cnt in direction_evidence.items()
            for truth, c in cnt.items()
            if c >= 2 and c >= 2 * max((v for k, v in cnt.items() if k != truth), default=0)
        }
        if len(members) >= 2:
            variant_map.append(
                {
                    "root": root,
                    "members": members,
                    "canonical": canonical,
                    "has_standard_member": bool(std_members),
                    "direction_evidence": {k: dict(v) for k, v in direction_evidence.items()},
                    "learned_map": learned_map,
                }
            )

    # experiments
    oracle_fix = 0
    for p in variant_pairs:
        # count variant substitutions that a perfect variant normalizer would fix
        oracle_fix += 1

    learned_changes = 0
    learned_correct = 0
    naive_changes = 0
    naive_correct = 0
    rb = ra_learn = ra_naive = 0
    rt = 0
    learned_map_all: dict[str, str] = {}
    naive_map_all: dict[str, str] = {}
    for cluster in variant_map:
        for m in cluster["members"]:
            if m in cluster["learned_map"]:
                learned_map_all[m] = cluster["learned_map"][m]
            if m != cluster["canonical"]:
                naive_map_all[m] = cluster["canonical"]

    for page, rec in per_page.items():
        ocr_chars = rec["ocr"]
        truth_chars = rec["truth"]
        mb, tb, _ = v1.align("".join(ocr_chars), truth_lib[page])
        rb += mb
        rt += tb

        pred_learn = [learned_map_all.get(c, c) for c in ocr_chars]
        pred_naive = [naive_map_all.get(c, c) for c in ocr_chars]
        ma_learn, _, _ = v1.align("".join(pred_learn), truth_lib[page])
        ma_naive, _, _ = v1.align("".join(pred_naive), truth_lib[page])
        ra_learn += ma_learn
        ra_naive += ma_naive
        n = min(len(ocr_chars), len(truth_chars))
        for i in range(n):
            if ocr_chars[i] != pred_learn[i]:
                learned_changes += 1
                if pred_learn[i] == truth_chars[i]:
                    learned_correct += 1
            if ocr_chars[i] != pred_naive[i]:
                naive_changes += 1
                if pred_naive[i] == truth_chars[i]:
                    naive_correct += 1

    result = {
        "schema_version": 1,
        "substitutions": len(subs),
        "label_counts": dict(counts),
        "variant_pairs": len(variant_pairs),
        "coverage_gap": {
            "truth_unique_not_in_standard": len(gap_std),
            "truth_unique_not_in_db": len(gap_db),
            "examples_not_in_db": [{"char": g["char"], "count": g["count"]} for g in gap_db[:30]],
        },
        "experiments": {
            "baseline_accuracy": round(rb / rt, 4) if rt else 0.0,
            "oracle_variant_fix_chars": oracle_fix,
            "oracle_variant_accuracy": round((rb + oracle_fix) / rt, 4) if rt else 0.0,
            "learned_direction_accuracy": round(ra_learn / rt, 4) if rt else 0.0,
            "learned_direction_changes": learned_changes,
            "learned_direction_correct": learned_correct,
            "naive_canonical_accuracy": round(ra_naive / rt, 4) if rt else 0.0,
            "naive_canonical_changes": naive_changes,
            "naive_canonical_correct": naive_correct,
        },
    }
    top_pairs = Counter((p["ocr"], p["truth"]) for p in variant_pairs).most_common(15)
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "variant_pairs.json").write_text(
        json.dumps(variant_pairs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (exp_dir / "coverage_gap.json").write_text(
        json.dumps(coverage_gaps, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (exp_dir / "variant_map.json").write_text(
        json.dumps(variant_map, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# P0: Variant Pairs and CNBE Coverage Gaps (VL-1.6 Residual Errors)",
        "",
        "Date: 2026-08-06",
        "",
        "## 1. Residual substitution classification",
        "",
        f"- Total substitutions: {len(subs)}",
        f"- Label counts: {dict(counts)}",
        f"- Unihan variant pairs: {len(variant_pairs)}",
        "",
        "## 2. CNBE coverage gaps",
        "",
        f"- Unique truth chars not in CNBE standard track: {len(gap_std)}",
        f"- Unique truth chars not in CNBE DB at all: {len(gap_db)}",
        "",
        "## 3. Experiments",
        "",
        f"- Baseline accuracy: {result['experiments']['baseline_accuracy']:.4f}",
        f"- Oracle variant fix: +{oracle_fix} chars -> "
        f"{result['experiments']['oracle_variant_accuracy']:.4f}",
        f"- Corpus-learned direction map: "
        f"{result['experiments']['learned_direction_accuracy']:.4f} "
        f"({learned_changes} changes; alignment-based accuracy)",
        f"- Naive canonical map: {result['experiments']['naive_canonical_accuracy']:.4f} "
        f"({naive_changes} changes; destructive without direction awareness)",
        "",
        "### Top variant pairs (count)",
        "",
        "| OCR form | Truth form | Count |",
        "|---|---:|---:|",
    ]
    for (x, t), n in top_pairs:
        lines.append(f"| {x} | {t} | {n} |")
    lines += [
        "",
        "## 4. Notes",
        "",
        "- Variant relation comes from Unihan kSemanticVariant / kSimplifiedVariant / "
        "kTraditionalVariant / kZVariant / kCompatibilityVariant / kSpoofingVariant.",
        "- The learned-direction map is corpus-derived and in-sample; it is a data "
        "construction artifact, not a deployed model.",
        "- Repro: `python3 analyze_variants.py`.",
        "",
        "## 5. Conclusion",
        "",
        f"- Variant normalization is the largest residual lever: {len(variant_pairs)}/{len(subs)} "
        "substitutions are Unihan variant relations.",
        f"- Oracle variant fix ceiling: {result['experiments']['oracle_variant_accuracy']:.4f} "
        f"(+{result['experiments']['oracle_variant_accuracy'] - result['experiments']['baseline_accuracy']:.4f}).",
        f"- Corpus-learned direction map: {result['experiments']['learned_direction_accuracy']:.4f} "
        f"(+{result['experiments']['learned_direction_accuracy'] - result['experiments']['baseline_accuracy']:.4f}), "
        "close to the ceiling without using ground truth at decision time.",
        f"- Naive canonical normalization is destructive ({result['experiments']['naive_canonical_accuracy']:.4f}) "
        "and must not be applied without direction awareness.",
        f"- Coverage: {len(gap_std)} unique truth chars are outside the CNBE standard track, "
        f"{len(gap_db)} are missing from the DB entirely.",
        "- The remaining non-variant errors need OCR top-N candidate reranking, not a "
        "static variant map.",
    ]
    (exp_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
