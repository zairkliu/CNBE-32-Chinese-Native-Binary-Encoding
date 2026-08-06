#!/usr/bin/env python3
"""Run vision-bridge on a small glyph sample for multimodal verification."""

from __future__ import annotations

import json
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent
BRIDGE = r"C:\Users\zairk\.codex\skills\vision-bridge\vision.js"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()
    evidence = json.loads((EXP / "results" / "pilot_evidence.json").read_text(encoding="utf-8"))["entries"]
    sample = [e for e in evidence if e["glyph"]][: args.limit]
    outputs = []
    for e in sample:
        image = REPO / e["glyph"]["image"]
        prompt = f"请识别这个汉字，并描述其部首、笔画结构（上下/左右/独体/包围等）、字形特征。"
        try:
            result = subprocess.run(
                ["node", BRIDGE, str(image), prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
        except subprocess.TimeoutExpired:
            outputs.append({"ucp": e["ucp"], "char": e["char"], "image": e["glyph"]["image"], "error": "timeout"})
            continue
        outputs.append(
            {
                "ucp": e["ucp"],
                "char": e["char"],
                "image": e["glyph"]["image"],
                "returncode": result.returncode,
                "stdout": result.stdout[:800],
                "stderr": result.stderr[:400],
            }
        )
    out = EXP / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "vision_verify.json").write_text(json.dumps({"schema_version": 1, "n": len(outputs), "entries": outputs}, ensure_ascii=False, indent=2), encoding="utf-8")
    for o in outputs:
        print(o["ucp"], o["returncode"], o["stdout"][:120].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
