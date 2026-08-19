#!/usr/bin/env python3
"""Build a Unicode-codepoint stream and vocabulary from plain Chinese corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Unicode codepoint dataset")
    ap.add_argument("--chars-paths", nargs="+", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--max-chars", type=int, default=0)
    args = ap.parse_args()

    parts: list[str] = []
    total = 0
    for p in args.chars_paths:
        text = Path(p).read_text(encoding="utf-8")
        if args.max_chars and total + len(text) > args.max_chars:
            text = text[: args.max_chars - total]
        parts.append(text)
        total += len(text)
        if args.max_chars and total >= args.max_chars:
            break
    text = "".join(parts)
    codepoints = np.array([ord(c) for c in text], dtype=np.int64)
    unique_cp = np.unique(codepoints)
    vocab = {int(c): i for i, c in enumerate(unique_cp)}

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "unicode.u32").write_bytes(codepoints.astype(">u4").tobytes())
    (out / "vocab.json").write_text(
        json.dumps(
            {
                "codepoint_to_id": {str(c): i for c, i in vocab.items()},
                "unique_codepoints": len(vocab),
                "total_chars": len(codepoints),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out / "meta.json").write_text(
        json.dumps(
            {"total_chars": len(codepoints), "unique_codepoints": len(vocab)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("saved:", out)
    print("total_chars:", len(codepoints), "unique_codepoints:", len(vocab))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
