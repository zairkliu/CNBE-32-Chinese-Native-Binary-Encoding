# -*- coding: utf-8 -*-
"""用蘇文忠公詩集 OCR 原文标点构建句读 eval 集。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def is_cjk(ch: str) -> bool:
    return "\u3400" <= ch <= "\u4dbf" or "\u4e00" <= ch <= "\u9fff" or "\U00020000" <= ch <= "\U0002ebef"


def strip_punct(text: str) -> str:
    return "".join(ch for ch in text if is_cjk(ch))


def main() -> int:
    parser = argparse.ArgumentParser(description="构建蘇文忠公詩集句读 eval")
    parser.add_argument("--raw", default="outputs/sushi_raw.txt")
    parser.add_argument("--out", default="outputs/sushi_punct_eval.jsonl")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--min-len", type=int, default=60)
    parser.add_argument("--max-len", type=int, default=180)
    parser.add_argument("--min-punct", type=int, default=3)
    args = parser.parse_args()

    text = Path(args.raw).read_text(encoding="utf-8")
    chunks = []
    cur = []
    cur_pure = 0
    for ch in text:
        cur.append(ch)
        if is_cjk(ch):
            cur_pure += 1
        if ch in "。，、；：？！" and cur_pure >= args.min_len:
            chunks.append("".join(cur))
            cur, cur_pure = [], 0
        elif cur_pure >= args.max_len:
            s = "".join(cur)
            cut = max(s.rfind(c) for c in "。，、；：？！；")
            if cut > 0:
                chunks.append(s[: cut + 1])
                cur = list(s[cut + 1 :])
                cur_pure = sum(1 for c in cur if is_cjk(c))
            else:
                chunks.append(s)
                cur, cur_pure = [], 0
    if cur:
        chunks.append("".join(cur))

    rows = []
    for chunk in chunks:
        pure = strip_punct(chunk)
        punct_count = sum(1 for ch in chunk if ch in "。，、；：？！")
        if 40 <= len(pure) <= 200 and punct_count >= args.min_punct:
            rows.append(
                {
                    "messages": [
                        {"role": "user", "content": pure},
                        {"role": "assistant", "content": chunk},
                    ],
                    "source": "sushi_ocr",
                }
            )
        if len(rows) >= args.limit:
            break
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"已生成 {len(rows)} 条蘇詩句读 eval -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
