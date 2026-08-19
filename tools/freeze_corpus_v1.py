#!/usr/bin/env python3
"""Freeze corpus v1: canonical manifest, CNBE streams, vocab and mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

SPLIT_SEED = 42
SPLIT_RATIOS = {"train": 0.98, "eval": 0.01, "val": 0.01}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assign_splits(manifest: list[dict], seed: int = SPLIT_SEED) -> dict[str, str]:
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for entry in manifest:
        by_bucket[entry["bucket"]].append(entry)
    result: dict[str, str] = {}
    for bucket, entries in by_bucket.items():
        buckets: dict[str, list[dict]] = defaultdict(list)
        for entry in sorted(entries, key=lambda e: e["slug"]):
            digest = hashlib.sha256(f"{entry['slug']}|{seed}".encode("utf-8")).digest()
            r = int.from_bytes(digest[:8], "big") % 10000
            split = "eval" if r < 100 else ("val" if r < 200 else "train")
            buckets[split].append(entry)
            result[entry["slug"]] = split
        for needed in ("eval", "val"):
            if not buckets[needed]:
                donor = buckets["train"].pop()
                buckets[needed].append(donor)
                result[donor["slug"]] = needed
    return result


def build_manifest(root: Path, output: Path, seed: int = SPLIT_SEED) -> dict:
    manifest = json.loads((root / "corpus_manifest.json").read_text(encoding="utf-8"))
    splits = assign_splits(manifest, seed)
    entries = []
    for entry in sorted(manifest, key=lambda e: e["slug"]):
        entries.append(
            {
                "slug": entry["slug"],
                "bucket": entry["bucket"],
                "batch": entry["batch"],
                "split": splits[entry["slug"]],
                "name": entry["name"],
                "chars": entry["chars"],
                "cjk": entry["cjk"],
                "cjk_ratio": entry["cjk_ratio"],
                "meta_hits": entry["meta_hits"],
                "sha256": entry["sha256"],
            }
        )
    totals = {"files": len(entries), "chars": sum(e["chars"] for e in entries)}
    for split in ("train", "eval", "val"):
        selected = [e for e in entries if e["split"] == split]
        totals[split] = {
            "files": len(selected),
            "chars": sum(e["chars"] for e in selected),
        }
    payload = {
        "schema": "cnbe_corpus_v1_canonical_manifest",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "corpus_root": str(root),
        "split_seed": seed,
        "split_strategy": "sha256(slug|seed) mod 10000; eval=1%, val=1%, train=98%",
        "split_ratios": SPLIT_RATIOS,
        "totals": totals,
        "entries": entries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("canonical manifest:", output)
    print("totals:", json.dumps(totals, ensure_ascii=False))
    return payload


class Encoder:
    def __init__(self, db: Path):
        conn = sqlite3.connect(str(db))
        rows = conn.execute("SELECT char, cnbe FROM cnbe32 WHERE cnbe IS NOT NULL").fetchall()
        conn.close()
        table = np.zeros(0x110000, dtype=np.uint32)
        for ch, code in rows:
            if ch:
                cp = ord(ch)
                if cp < len(table):
                    table[cp] = int(code)
        self.table = table

    def encode(self, text: str) -> np.ndarray:
        cps = np.frombuffer(text.encode("utf-32-le"), dtype="<u4").astype(np.int64)
        return self.table[cps]


def encode_corpus(root: Path, out_dir: Path, db: Path, manifest_path: Path) -> dict:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    encoder = Encoder(db)
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    streams = {
        split: open(data_dir / f"{split}.cnbe", "wb")
        for split in ("train", "eval", "val")
    }
    first = {split: True for split in streams}
    global_counts: dict[int, int] = {}
    train_code_counts: dict[int, int] = {}
    train_template_counts: dict[int, int] = {}
    split_tokens = {split: 0 for split in streams}
    split_code0 = {split: 0 for split in streams}
    separator = encoder.encode("\n\n")
    trailing = encoder.encode("\n")
    t0 = time.perf_counter()

    for entry in payload["entries"]:
        path = root / entry["bucket"] / f"{entry['slug']}.txt"
        text = path.read_text(encoding="utf-8", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
        codes = encoder.encode(text)
        split = entry["split"]
        if not first[split]:
            streams[split].write(separator.tobytes())
        first[split] = False
        streams[split].write(codes.astype(">u4").tobytes())
        split_tokens[split] += int(len(codes))
        split_code0[split] += int((codes == 0).sum())

        unique, counts = np.unique(codes, return_counts=True)
        for code, count in zip(unique.tolist(), counts.tolist()):
            global_counts[code] = global_counts.get(code, 0) + count
        if split == "train":
            for code, count in zip(unique.tolist(), counts.tolist()):
                train_code_counts[code] = train_code_counts.get(code, 0) + count
            keys = (
                ((codes >> 24) & 0xFF) << 9
                | ((codes >> 15) & 0x0F) << 5
                | ((codes >> 19) & 0x1F)
            )
            tkeys, tcounts = np.unique(keys, return_counts=True)
            for key, count in zip(tkeys.tolist(), tcounts.tolist()):
                train_template_counts[key] = train_template_counts.get(key, 0) + count

    for split in streams:
        streams[split].write(trailing.tobytes())
        streams[split].close()

    vocab_codes = sorted(global_counts)
    vocab = {str(code): i for i, code in enumerate(vocab_codes)}
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False), encoding="utf-8"
    )
    (assets / "vocab_meta.json").write_text(
        json.dumps(
            {
                "total_tokens": sum(split_tokens.values()),
                "unique_codes": len(vocab_codes),
                "split_tokens": split_tokens,
                "split_code0": split_code0,
                "train_tokens": split_tokens["train"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    num_experts = 128
    loads = np.zeros(num_experts, dtype=np.int64)
    mapping: dict[str, dict] = {}
    for key, freq in sorted(
        train_template_counts.items(), key=lambda item: -item[1]
    ):
        expert = int(np.argmin(loads))
        mapping[str(key)] = {
            "experts": [expert],
            "freq": freq,
            "radix": key >> 9,
            "struct": (key >> 5) & 0x0F,
            "strokes": key & 0x1F,
        }
        loads[expert] += freq
    mapping_payload = {
        "version": 1,
        "stats": {"num_experts": num_experts, "mode": 3},
        "mapping": mapping,
    }
    (assets / "mapping_128.json").write_text(
        json.dumps(mapping_payload, ensure_ascii=False), encoding="utf-8"
    )

    stats = {
        "split_tokens": split_tokens,
        "split_code0": split_code0,
        "unique_codes": len(vocab_codes),
        "mapping_templates": len(mapping),
        "runtime_seconds": round(time.perf_counter() - t0, 1),
    }
    (out_dir / "encode_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("encode stats:", json.dumps(stats, ensure_ascii=False))
    print("data files:", [str(p) for p in sorted(data_dir.glob("*.cnbe"))])
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--manifest-only", action="store_true")
    args = ap.parse_args()

    root = args.root
    out = args.out or (root / "frozen")
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "canonical_manifest.json"
    build_manifest(root, manifest_path)
    if args.manifest_only:
        return 0
    encode_corpus(root, out, args.db, manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
