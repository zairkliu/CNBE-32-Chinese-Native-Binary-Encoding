#!/usr/bin/env python3
"""Cross-batch full audit and merge of the CNBE publication + guji corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from clean_publication_markdown import clean_book  # noqa: E402

META_PATTERNS = [
    "版权",
    "ISBN",
    "总目录",
    "书名：",
    "作者：",
    "出版社",
    "定价",
]
BATCH_PRIORITY = {"01": 0, "02": 1, "03": 2, "guji": 3}


def normalize_text(text: str) -> str:
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"


def cjk_stats(text: str) -> tuple[int, int]:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
    mask = (
        ((cps >= 0x4E00) & (cps <= 0x9FFF))
        | ((cps >= 0x3400) & (cps <= 0x4DBF))
        | ((cps >= 0xF900) & (cps <= 0xFAFF))
    )
    return int(mask.sum()), int(len(cps))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_title(name: str) -> str:
    s = name
    for prefix in ("v2.1_", "v2.2_", "v2_", "v2.", "v2_出版物__", "出版物__"):
        if s.startswith(prefix):
            s = s[len(prefix) :]
            break
    s = re.sub(r"[_\-\s（）()\[\]【】《》「」]", "", s)
    s = re.sub(r"\.txt$", "", s)
    return s[:40]


def fingerprint(text: str, stride: int = 100) -> set[int]:
    cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4")
    vals: set[int] = set()
    for i in range(0, max(0, len(cps) - 4), stride):
        vals.add(hash(tuple(cps[i : i + 5])))
    return vals


def metadata_hits(text: str, limit: int = 50_000) -> int:
    sample = text[:limit]
    return sum(sample.count(p) for p in META_PATTERNS)


def slugify(name: str, idx: int) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", name).strip("_")
    return f"{idx:05d}_{base or 'book'}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--publication-root", type=Path, required=True)
    ap.add_argument("--guji-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--core-ratio", type=float, default=0.7)
    ap.add_argument("--technical-ratio", type=float, default=0.3)
    ap.add_argument("--dedup-threshold", type=float, default=0.85)
    args = ap.parse_args()

    out = args.output_dir
    core_dir = out / "core"
    tech_dir = out / "technical"
    core_dir.mkdir(parents=True, exist_ok=True)
    tech_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    t0 = time.perf_counter()

    # 1. Publication TXT batches.
    pub_root = args.publication_root
    for batch_dir in sorted(pub_root.iterdir()):
        if not batch_dir.is_dir() or not batch_dir.name[:3] in ("01_", "02_", "03_"):
            continue
        batch_id = batch_dir.name[:2]
        for path in sorted(batch_dir.glob("*.txt")):
            raw = path.read_text(encoding="utf-8", errors="replace")
            text = normalize_text(raw)
            cjk, total = cjk_stats(text)
            records.append(
                {
                    "source": str(path),
                    "batch": batch_id,
                    "name": path.name,
                    "chars": total,
                    "cjk": cjk,
                    "ratio": round(cjk / max(1, total), 4),
                    "meta_hits": metadata_hits(text),
                    "hash": content_hash(text),
                }
            )

    # 2. Guji MD files.
    guji_root = args.guji_root
    for path in sorted(guji_root.rglob("*.md")):
        cleaned, _ = clean_book(path)
        if not cleaned.strip():
            continue
        cjk, total = cjk_stats(cleaned)
        rel = path.relative_to(guji_root).as_posix()
        records.append(
            {
                "source": str(path),
                "batch": "guji",
                "name": rel.replace("/", "__"),
                "chars": total,
                "cjk": cjk,
                "ratio": round(cjk / max(1, total), 4),
                "meta_hits": metadata_hits(cleaned),
                "hash": content_hash(cleaned),
            }
        )

    print("scanned", len(records), "records in", round(time.perf_counter() - t0, 1), "s", flush=True)

    # 3. Exact dedup by cleaned-content hash.
    by_hash: dict[str, dict] = {}
    exact_dups: list[list[str]] = []
    for rec in records:
        key = rec["hash"]
        if key in by_hash:
            exact_dups.append([by_hash[key]["name"], rec["name"]])
            if (rec["ratio"], rec["chars"]) > (by_hash[key]["ratio"], by_hash[key]["chars"]):
                by_hash[key] = rec
        else:
            by_hash[key] = rec
    kept = list(by_hash.values())
    print("after exact dedup", len(kept), "records, exact groups", len(exact_dups), flush=True)

    # 4. Near-dup by normalized title within publication batches.
    near_dups: list[list[str]] = []
    title_groups: dict[str, list[dict]] = {}
    for rec in kept:
        if rec["batch"] == "guji":
            continue
        key = normalized_title(rec["name"])
        title_groups.setdefault(key, []).append(rec)
    remove: set[str] = set()
    for key, group in title_groups.items():
        if len(group) < 2:
            continue
        fingerprints = []
        for rec in group:
            text = Path(rec["source"]).read_text(encoding="utf-8", errors="replace")
            fingerprints.append(fingerprint(normalize_text(text)))
        for i in range(len(group)):
            if group[i]["hash"] in remove:
                continue
            for j in range(i + 1, len(group)):
                if group[j]["hash"] in remove:
                    continue
                a, b = fingerprints[i], fingerprints[j]
                inter = len(a & b)
                union = len(a | b)
                sim = inter / max(1, union)
                if sim >= args.dedup_threshold:
                    near_dups.append([group[i]["name"], group[j]["name"]])
                    worse = group[i] if (group[i]["ratio"], group[i]["chars"]) < (
                        group[j]["ratio"],
                        group[j]["chars"],
                    ) else group[j]
                    remove.add(worse["hash"])
    kept = [rec for rec in kept if rec["hash"] not in remove]
    print("after near-dup", len(kept), "records, near groups", len(near_dups), flush=True)

    # 5. Quality split and copy.
    stats = {"core": {"files": 0, "chars": 0, "cjk": 0}, "technical": {"files": 0, "chars": 0, "cjk": 0}, "excluded": {"files": 0, "chars": 0, "cjk": 0}}
    manifest = []
    used_slugs: set[str] = set()
    for idx, rec in enumerate(sorted(kept, key=lambda r: (-r["ratio"], -r["chars"]))):
        if rec["chars"] < 1000:
            stats["excluded"]["files"] += 1
            stats["excluded"]["chars"] += rec["chars"]
            stats["excluded"]["cjk"] += rec["cjk"]
            continue
        if rec["ratio"] >= args.core_ratio:
            bucket = "core"
        elif rec["ratio"] >= args.technical_ratio:
            bucket = "technical"
        else:
            stats["excluded"]["files"] += 1
            stats["excluded"]["chars"] += rec["chars"]
            stats["excluded"]["cjk"] += rec["cjk"]
            continue
        slug = slugify(rec["name"], idx)
        while slug in used_slugs:
            slug = slug + "_2"
        used_slugs.add(slug)
        target = (core_dir if bucket == "core" else tech_dir) / f"{slug}.txt"
        source = Path(rec["source"])
        if rec["batch"] == "guji":
            cleaned, _ = clean_book(source)
            text = cleaned
        else:
            text = normalize_text(source.read_text(encoding="utf-8", errors="replace"))
        target.write_text(text, encoding="utf-8")
        stats[bucket]["files"] += 1
        stats[bucket]["chars"] += rec["chars"]
        stats[bucket]["cjk"] += rec["cjk"]
        manifest.append(
            {
                "slug": slug,
                "bucket": bucket,
                "source": rec["source"],
                "batch": rec["batch"],
                "name": rec["name"],
                "chars": rec["chars"],
                "cjk": rec["cjk"],
                "cjk_ratio": rec["ratio"],
                "meta_hits": rec["meta_hits"],
                "sha256": rec["hash"],
            }
        )

    out.mkdir(parents=True, exist_ok=True)
    report = {
        "scanned": len(records),
        "kept_after_dedup": len(kept),
        "exact_duplicate_pairs": len(exact_dups),
        "near_duplicate_pairs": len(near_dups),
        "stats": stats,
        "exact_duplicates": exact_dups[:50],
        "near_duplicates": near_dups[:50],
    }
    (out / "dedup_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "corpus_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    audit = {
        "total_records": len(records),
        "kept": len(kept),
        "core": stats["core"],
        "technical": stats["technical"],
        "excluded": stats["excluded"],
        "by_batch": {},
    }
    for rec in records:
        audit["by_batch"].setdefault(rec["batch"], {"files": 0, "chars": 0, "cjk": 0})
        audit["by_batch"][rec["batch"]]["files"] += 1
        audit["by_batch"][rec["batch"]]["chars"] += rec["chars"]
        audit["by_batch"][rec["batch"]]["cjk"] += rec["cjk"]
    (out / "quality_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("done in", round(time.perf_counter() - t0, 1), "s")
    print("stats", json.dumps(stats, ensure_ascii=False))
    print("saved", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
