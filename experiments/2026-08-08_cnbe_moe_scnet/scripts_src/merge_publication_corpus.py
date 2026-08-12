#!/usr/bin/env python3
"""Merge existing CNBE corpus with new publication streams and rebuild assets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scnet_upload_package" / "code"))

from src.cnbe_router import build_balanced_mapping  # noqa: E402
from src.data import build_vocab, load_codes  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--existing-dir", type=Path, required=True)
    ap.add_argument("--new-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--experts", nargs="+", type=int, default=[128, 256])
    ap.add_argument("--train-ratio", type=float, default=0.95)
    args = ap.parse_args()

    existing = sorted(args.existing_dir.glob("*.cnbe"))
    new = sorted(args.new_dir.glob("*.cnbe"))
    paths = existing + new
    if not paths:
        print("no cnbe files")
        return 2
    print("existing", len(existing), "new", len(new), "total", len(paths))

    codes = load_codes([str(p) for p in paths])
    split = int(len(codes) * args.train_ratio)
    train_codes = codes[:split]
    vocab = build_vocab(codes)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False), encoding="utf-8"
    )
    (out / "vocab_meta.json").write_text(
        json.dumps(
            {
                "total_tokens": int(len(codes)),
                "unique_codes": len(vocab),
                "train_tokens": int(len(train_codes)),
                "existing_files": len(existing),
                "new_files": len(new),
            },
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

    (out / "corpus_manifest.json").write_text(
        json.dumps(
            {
                "total_tokens": int(len(codes)),
                "train_tokens": int(len(train_codes)),
                "eval_tokens": int(len(codes) - len(train_codes)),
                "unique_codes": len(vocab),
                "existing": [str(p) for p in existing],
                "new": [str(p) for p in new],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("saved:", out)
    print("total_tokens:", len(codes), "unique_codes:", len(vocab))
    return 0


if __name__ == "__main__":
    sys.exit(main())
