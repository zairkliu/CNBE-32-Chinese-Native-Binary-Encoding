#!/usr/bin/env python3
"""Automated quality calibration for the merged CNBE corpus."""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from batch_encode_publications import FastCNBEEncoder  # noqa: E402

META_PATTERNS = ["版权", "ISBN", "总目录", "书名：", "作者：", "出版社", "定价"]


def entropy(counts: np.ndarray) -> float:
    total = int(counts.sum())
    if total == 0:
        return 0.0
    p = counts / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def kl(p: np.ndarray, q: np.ndarray) -> float:
    p = p + 1e-9
    q = q + 1e-9
    p = p / p.sum()
    q = q / q.sum()
    return float((p * np.log2(p / q)).sum())


def process_shards(shard_dir: Path, encoder: FastCNBEEncoder) -> dict:
    radix = np.zeros(256, dtype=np.int64)
    strokes = np.zeros(32, dtype=np.int64)
    struct = np.zeros(16, dtype=np.int64)
    code_counts: dict[int, int] = {}
    total = 0
    cjk_total = 0
    cjk_covered = 0
    replacement_chars = 0
    control_chars = 0
    meta_hits = {pattern: 0 for pattern in META_PATTERNS}
    for path in sorted(shard_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
        codes = encoder.table[cps].astype(np.int64)
        total += int(len(codes))
        replacement_chars += int((cps == 0xFFFD).sum())
        control_chars += int(
            ((cps < 32) & ~np.isin(cps, np.array([9, 10, 13]))).sum()
        )
        for pattern in META_PATTERNS:
            meta_hits[pattern] += text.count(pattern)
        mask = (
            ((cps >= 0x4E00) & (cps <= 0x9FFF))
            | ((cps >= 0x3400) & (cps <= 0x4DBF))
            | ((cps >= 0xF900) & (cps <= 0xFAFF))
        )
        cjk_total += int(mask.sum())
        cjk_covered += int((codes[mask] != 0).sum())
        radix += np.bincount((codes >> 24) & 0xFF, minlength=256)
        strokes += np.bincount((codes >> 19) & 0x1F, minlength=32)
        struct += np.bincount((codes >> 15) & 0x0F, minlength=16)
        unique, counts = np.unique(codes, return_counts=True)
        for code, count in zip(unique.tolist(), counts.tolist()):
            code_counts[code] = code_counts.get(code, 0) + count
    return {
        "total_tokens": total,
        "cjk_tokens": cjk_total,
        "cjk_covered": cjk_covered,
        "replacement_chars": replacement_chars,
        "control_chars": control_chars,
        "meta_hits": meta_hits,
        "unique_codes": len(code_counts),
        "code_counts": code_counts,
        "radix": radix,
        "strokes": strokes,
        "struct": struct,
    }


def sampled_fingerprint(text: str, stride: int = 200) -> set[int]:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4")
    vals: set[int] = set()
    for i in range(0, max(0, len(cps) - 4), stride):
        vals.add(hash(tuple(cps[i : i + 5])))
    return vals


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dedup-pairs", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    encoder = FastCNBEEncoder(str(args.db))
    t0 = time.perf_counter()
    core = process_shards(args.root / "shards_core", encoder)
    technical = process_shards(args.root / "shards_technical", encoder)
    print("processed in", round(time.perf_counter() - t0, 1), "s", flush=True)

    conn = sqlite3.connect(str(args.db))
    db_codes = set(
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT cnbe FROM cnbe32 WHERE cnbe IS NOT NULL AND cnbe != 0"
        )
    )
    conn.close()

    core_unique = {c for c in core["code_counts"] if c != 0}
    tech_unique = {c for c in technical["code_counts"] if c != 0}
    merged_unique = core_unique | tech_unique
    coverage = len(merged_unique) / max(1, len(db_codes))
    core_nonzero = {c: n for c, n in core["code_counts"].items() if c != 0}
    core_nonzero_total = sum(core_nonzero.values())
    top100 = sum(
        count for _, count in sorted(core_nonzero.items(), key=lambda x: -x[1])[:100]
    )
    top100_ratio = top100 / max(1, core_nonzero_total)

    def bucket_report(data: dict) -> dict:
        nonzero = {c: n for c, n in data["code_counts"].items() if c != 0}
        nonzero_total = sum(nonzero.values())
        top100_nonzero = sum(
            count
            for _, count in sorted(nonzero.items(), key=lambda x: -x[1])[:100]
        )
        return {
            "total_tokens": data["total_tokens"],
            "cjk_tokens": data["cjk_tokens"],
            "cjk_coverage": round(data["cjk_covered"] / max(1, data["cjk_tokens"]), 6),
            "unknown_tokens": data["code_counts"].get(0, 0),
            "unique_codes": len(nonzero),
            "unique_codes_all": data["unique_codes"],
            "top100_ratio": round(top100_nonzero / max(1, nonzero_total), 6),
            "entropy_radix": round(entropy(data["radix"]), 4),
            "entropy_strokes": round(entropy(data["strokes"]), 4),
            "entropy_struct": round(entropy(data["struct"]), 4),
        }

    kl_radix = kl(core["radix"].astype(float), technical["radix"].astype(float))
    kl_strokes = kl(core["strokes"].astype(float), technical["strokes"].astype(float))
    kl_struct = kl(core["struct"].astype(float), technical["struct"].astype(float))
    merged = {
        "radix": core["radix"] + technical["radix"],
        "strokes": core["strokes"] + technical["strokes"],
        "struct": core["struct"] + technical["struct"],
    }
    residual = {
        "core": {
            "replacement_chars": core["replacement_chars"],
            "control_chars": core["control_chars"],
            "metadata_pattern_hits": core["meta_hits"],
        },
        "technical": {
            "replacement_chars": technical["replacement_chars"],
            "control_chars": technical["control_chars"],
            "metadata_pattern_hits": technical["meta_hits"],
        },
    }

    # Dedup audit on random core file pairs.
    core_files = sorted((args.root / "core").glob("*.txt"))
    rng = random.Random(args.seed)
    pairs = []
    seen = set()
    while len(pairs) < args.dedup_pairs and len(seen) < len(core_files) ** 2:
        i, j = rng.sample(range(len(core_files)), 2)
        key = (min(i, j), max(i, j))
        if key in seen:
            continue
        seen.add(key)
        a = core_files[i].read_text(encoding="utf-8", errors="replace")
        b = core_files[j].read_text(encoding="utf-8", errors="replace")
        fa, fb = sampled_fingerprint(a), sampled_fingerprint(b)
        inter = len(fa & fb)
        sim = inter / max(1, len(fa | fb))
        pairs.append(round(sim, 4))
    over_03 = sum(1 for s in pairs if s > 0.3)
    over_05 = sum(1 for s in pairs if s > 0.5)

    # Completeness.
    manifest = json.loads((args.root / "corpus_manifest.json").read_text(encoding="utf-8"))
    missing = [
        e["slug"]
        for e in manifest
        if not (args.root / e["bucket"] / f"{e['slug']}.txt").exists()
    ]
    core_files_names = {p.stem for p in core_files}
    tech_files_names = {p.stem for p in (args.root / "technical").glob("*.txt")}
    manifest_slugs = {e["slug"] for e in manifest}
    orphans = sorted(
        (core_files_names | tech_files_names) - manifest_slugs
    )

    report = {
        "db_codes": len(db_codes),
        "unique_codes_merged": len(merged_unique),
        "code_coverage": round(coverage, 6),
        "top100_ratio": round(top100_ratio, 6),
        "core": bucket_report(core),
        "technical": bucket_report(technical),
        "entropy_merged": {
            "radix": round(entropy(merged["radix"]), 4),
            "strokes": round(entropy(merged["strokes"]), 4),
            "struct": round(entropy(merged["struct"]), 4),
        },
        "kl_divergence": {
            "radix": round(kl_radix, 6),
            "strokes": round(kl_strokes, 6),
            "struct": round(kl_struct, 6),
            "mean": round((kl_radix + kl_strokes + kl_struct) / 3, 6),
        },
        "dedup_audit": {
            "pairs": len(pairs),
            "max_jaccard": max(pairs) if pairs else 0.0,
            "over_0.3": over_03,
            "over_0.5": over_05,
            "percentile_99": round(
                sorted(pairs)[int(len(pairs) * 0.99) - 1], 4
            )
            if pairs
            else 0.0,
        },
        "completeness": {
            "manifest_entries": len(manifest),
            "missing_files": len(missing),
            "orphan_files": len(orphans),
        },
        "residual_noise": residual,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
