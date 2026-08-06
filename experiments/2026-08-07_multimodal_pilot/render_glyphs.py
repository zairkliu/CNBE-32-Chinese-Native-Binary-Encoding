#!/usr/bin/env python3
"""Render pilot glyph images from a system CJK font."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
EXP = Path(__file__).resolve().parent

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]


def pick_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("no CJK font found")


def main() -> int:
    scope = json.loads((EXP / "results" / "pilot_scope.json").read_text(encoding="utf-8"))["entries"]
    glyph_dir = EXP / "glyphs"
    glyph_dir.mkdir(parents=True, exist_ok=True)
    font = pick_font(180)
    manifest = []
    for entry in scope:
        ch = entry["char"]
        img = Image.new("RGB", (256, 256), "white")
        draw = ImageDraw.Draw(img)
        box = draw.textbbox((0, 0), ch, font=font)
        w = box[2] - box[0]
        h = box[3] - box[1]
        x = (256 - w) // 2 - box[0]
        y = (256 - h) // 2 - box[1]
        draw.text((x, y), ch, fill="black", font=font)
        out = glyph_dir / f"{entry['ucp']}.png"
        img.save(out)
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        manifest.append(
            {
                "ucp": entry["ucp"],
                "char": ch,
                "stratum": entry["stratum"],
                "image": str(out.relative_to(REPO)),
                "sha256": digest,
                "font": Path(FONT_CANDIDATES[0]).name,
                "size": 256,
            }
        )
    (EXP / "glyphs" / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "count": len(manifest), "entries": manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("rendered", len(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
