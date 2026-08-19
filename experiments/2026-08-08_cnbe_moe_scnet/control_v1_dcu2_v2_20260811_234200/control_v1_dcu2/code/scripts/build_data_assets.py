#!/usr/bin/env python3
# Build vocab and balanced expert mappings from the full CNBE corpus.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cnbe_router import build_balanced_mapping
from src.data import build_vocab, load_codes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cnbe-paths", nargs="+", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--experts", nargs="+", type=int, default=[128, 256])
    ap.add_argument("--train-ratio", type=float, default=0.95)
    args = ap.parse_args()

    codes = load_codes(args.cnbe_paths)
    split = int(len(codes) * args.train_ratio)
    train_codes = codes[:split]
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    vocab = build_vocab(codes)
    (out / "vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False), encoding="utf-8"
    )
    (out / "vocab_meta.json").write_text(
        json.dumps(
            {"total_tokens": len(codes), "unique_codes": len(vocab), "train_tokens": len(train_codes)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for n in args.experts:
        mapping = build_balanced_mapping(train_codes, n, mode=3)
        (out / f"mapping_{n}.json").write_text(
            json.dumps(mapping, ensure_ascii=False), encoding="utf-8"
        )
        print(f"mapping_{n}: templates={len(mapping['mapping'])}", flush=True)

    print("saved:", out, flush=True)
    print("total_tokens:", len(codes), "unique_codes:", len(vocab), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
