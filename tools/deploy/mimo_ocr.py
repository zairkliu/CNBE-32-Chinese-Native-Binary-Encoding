#!/usr/bin/env python3
"""MiMo V2.5 image OCR adapter for the CNBE-32 deploy pipeline.

The Xiaomi MiMo key is managed by the installed deepseek-vision skill
(~/.codex/skills/deepseek-vision), so this adapter never reads or writes
the key itself.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_PROMPT = "请把图片中的全部文字按阅读顺序逐字转录，只输出识别出的文字，不要遗漏，不要解释。"


def find_mimo_script() -> Path:
    candidates = [
        os.environ.get("MIMO_SKILL_SCRIPT", ""),
        str(Path.home() / ".codex" / "skills" / "deepseek-vision" / "scripts" / "mimo.py"),
        "/root/.codex/skills/deepseek-vision/scripts/mimo.py",
    ]
    for cand in candidates:
        if cand:
            path = Path(cand)
            if path.exists():
                return path
    raise FileNotFoundError("deepseek-vision skill not found; install it first")


def ocr_image(
    image_path: Path,
    prompt: str = DEFAULT_PROMPT,
    max_tokens: int = 4096,
    timeout: int = 300,
) -> dict:
    script = find_mimo_script()
    cmd = [
        sys.executable,
        str(script),
        "analyze",
        "--files",
        str(image_path),
        "--prompt",
        prompt,
        "--max-tokens",
        str(max_tokens),
        "--timeout",
        str(timeout),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] or proc.stdout[-2000:])
    data = json.loads(proc.stdout)
    if not data.get("ok"):
        raise RuntimeError(json.dumps(data, ensure_ascii=False))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="MiMo V2.5 image OCR")
    parser.add_argument("image", type=Path)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    result = ocr_image(args.image, args.prompt, args.max_tokens, args.timeout)
    print(result.get("content", ""))
    usage = result.get("usage", {})
    print(
        json.dumps(
            {
                "model": result.get("model"),
                "total_tokens": usage.get("total_tokens"),
                "cost_cny": result.get("cost_cny"),
                "finish_reason": result.get("finish_reason"),
                "truncated": result.get("truncated"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
