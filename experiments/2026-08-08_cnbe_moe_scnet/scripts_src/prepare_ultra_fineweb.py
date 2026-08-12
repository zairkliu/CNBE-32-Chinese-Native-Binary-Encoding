#!/usr/bin/env python3
"""Extract Chinese text from Ultra-FineWeb-L3 shards into one plain-text file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def extract_text(record: dict) -> str:
    for key in ("text", "content", "response", "instruction"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--max-chars", type=int, default=0)
    args = ap.parse_args()

    files = sorted(args.input_dir.rglob("*.jsonl")) + sorted(args.input_dir.rglob("*.json"))
    if not files:
        try:
            import pandas as pd
            for p in sorted(args.input_dir.rglob("*.parquet")):
                df = pd.read_parquet(p)
                col = next((c for c in ("text", "content", "response") if c in df.columns), None)
                if col:
                    files.append(("parquet", p, col))
        except ImportError:
            print("pandas/pyarrow not installed; only JSONL/JSON supported", file=sys.stderr)

    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with out.open("w", encoding="utf-8") as fh:
        for item in files:
            if isinstance(item, tuple):
                _, path, col = item
                import pandas as pd
                for text in pd.read_parquet(path, columns=[col])[col]:
                    if not isinstance(text, str):
                        continue
                    total += len(text)
                    fh.write(text + "\n")
                    if args.max_chars and total >= args.max_chars:
                        print("reached max_chars:", total)
                        return 0
                continue
            path = item
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = extract_text(record)
                    if not text:
                        continue
                    total += len(text)
                    fh.write(text + "\n")
                    if args.max_chars and total >= args.max_chars:
                        print("reached max_chars:", total)
                        return 0
    print("saved:", out, "chars:", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
