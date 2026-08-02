# -*- coding: utf-8 -*-
"""统计 CNBE 流中的 (radix, stroke, struct) 高频模板。"""

from __future__ import annotations

import argparse
import json
import struct
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="构建高频结构模板")
    parser.add_argument("cnbe")
    parser.add_argument("output")
    parser.add_argument("--top-k", type=int, default=64)
    args = parser.parse_args()

    data = Path(args.cnbe).read_bytes()
    triples = []
    for i in range(0, len(data), 4):
        code = struct.unpack(">I", data[i : i + 4])[0]
        triples.append(((code >> 24) & 0xFF, (code >> 19) & 0x1F, (code >> 15) & 0x0F))
    counter = Counter(triples)
    top = counter.most_common(args.top_k)
    template = {
        str(idx): {"radix": r, "stroke": s, "struct": st, "freq": cnt}
        for idx, ((r, s, st), cnt) in enumerate(top)
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    total = len(triples)
    covered = sum(cnt for _, cnt in top)
    print(f"模板数: {len(template)}，覆盖率: {covered / total:.4%}（{covered}/{total}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
