# -*- coding: utf-8 -*-
"""DJVU 文本层 -> 原始文本 -> 纯中文字流（蘇文忠公詩集）。"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def is_cjk(ch: str) -> bool:
    return (
        "\u3400" <= ch <= "\u4dbf"
        or "\u4e00" <= ch <= "\u9fff"
        or "\uf900" <= ch <= "\ufaff"
        or "\U00020000" <= ch <= "\U0002ebef"
    )


def extract_djvu_text(djvu_path: Path, djvutxt: str = "") -> str:
    exe = djvutxt or r"C:\Program Files (x86)\DjVuLibre\djvutxt.exe"
    proc = subprocess.run(
        [exe, str(djvu_path)],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    return proc.stdout.decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="提取蘇文忠公詩集 DJVU 文本层")
    parser.add_argument("djvu", nargs="?", default=r"D:\电子书\宋集珍本丛刊108册\4,蘇文忠公詩集a.djvu")
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--djvutxt", default=r"C:\Program Files (x86)\DjVuLibre\djvutxt.exe")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = extract_djvu_text(Path(args.djvu), args.djvutxt)
    if len(text) < 1000:
        print("提取文本过短")
        return 1
    (out_dir / "sushi_raw.txt").write_text(text, encoding="utf-8")
    chars = "".join(ch for ch in text if is_cjk(ch))
    (out_dir / "sushi.chars.txt").write_text(chars, encoding="utf-8")
    print(f"原始文本: {len(text):,} 字符")
    print(f"纯中文字流: {len(chars):,} 字 -> {out_dir / 'sushi.chars.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
